import re
from typing import List, Union
from termcolor import colored
from neutrino_cli.util.ast import get_function_name_from_ast, is_async_function


class WebSocketCell:
    def __init__(
            self,
            endpoint: str,
            func_body: str,
            ws_type: str = 'event',
            message_schema: Union[str, list[str]] = None,
            query: Union[str, list[str]] = None,
            headers: Union[str, list[str]] = None,
            validate_message_schema: bool = True,
    ):
        self.endpoint = endpoint
        self.ws_type = ws_type
        self.message_schema = self._parse_fields(message_schema)
        self.query = self._parse_fields(query)
        self.headers = self._parse_fields(headers)
        self.func_body = func_body
        self.validate_message_schema = validate_message_schema

    def _extract_url_params(self) -> list[tuple[any, str]]:
        return [(name, 'str') for name in re.findall(r"/{([\w]+)}", self.endpoint)]

    @staticmethod
    def _parse_fields(fields: Union[str, List[str], dict[str, str]]) -> Union[List[str], dict[str, str]]:
        if isinstance(fields, list):
            return fields
        elif isinstance(fields, str):
            return fields.split(',') if fields else []
        elif isinstance(fields, dict):
            return fields
        else:
            return []

    def _generate_endpoint_signature(self, func_name: str) -> str:
        """
        Generate a method signature based on query parameters and URL parameters.

        Parameters:
            func_name (str): The function name.
            query_params (List[str]): The query parameters in 'name:type' format.
            url_params (List[Tuple[str, str]]): The URL parameters as a list of (name, type).
            return_type (str, optional): The return type of the function. Defaults to "None".

        Returns:
            str: The generated method signature.
        """

        def clean_field(field: str) -> tuple[str, str]:
            parts = field.split(":")
            name = parts[0].strip()
            f_type = "Any" if len(parts) == 1 else parts[1].strip()
            return name, f_type

        # Handle query params
        query_strs = [f"{name}: {f_type}" for field in self.query for name, f_type in [clean_field(field)]]

        # Handle URL params
        url_strs = [f"{name}: str" for name, f_type in self._extract_url_params()]

        all_params = ", ".join(query_strs + url_strs)
        all_params = f", {all_params}" if all_params else ""

        return f"async def {func_name}_websocket(websocket: WebSocket{all_params}):"

    def _generate_func_body_invocation_params(self, skip_room_and_client: bool = False) -> str:
        def clean_field(field: str) -> tuple[str, str]:
            parts = field.split(":")
            f = parts[0].strip()
            t = "Any"
            if len(parts) == 2:
                t = parts[1].strip()
            return f, t

        # Handling query params
        query_field_names = [clean_field(field)[0] for field in self.query]
        if skip_room_and_client:
            query_field_names = [name for name in query_field_names if name not in ['room_id', 'client_id']]
        query_params = [f"{name}={name}" for name in query_field_names]

        # Handling URL params
        url_field_names = [name for name, _ in self._extract_url_params()]
        if skip_room_and_client:
            url_field_names = [name for name in url_field_names if name not in ['room_id', 'client_id']]
        url_params = [f"{name}={name}" for name in url_field_names]

        all_params = query_params + url_params

        return ', '.join(all_params)

    def _contains_room_and_client_id(self) -> tuple[bool, bool]:
        """
        Checks if 'room_id' and 'client_id' are present in the parameter list.

        Returns:
            tuple[bool, bool]: A tuple containing two booleans.
                               The first boolean is True if 'room_id' is present, otherwise False.
                               The second boolean is True if 'client_id' is present, otherwise False.
        """
        def clean_field(field: str) -> str:
            return field.split(":")[0].strip()

        # Handling query params
        query_params = [clean_field(field) for field in self.query]

        # Handling URL params
        url_params = [name for name, _ in self._extract_url_params()]

        return 'room_id' in query_params + url_params, 'client_id' in query_params + url_params

    def _generate_code(self) -> list[str]:
        """Generate code based on ws_type."""
        func_name = get_function_name_from_ast(self.func_body)
        if self.ws_type == 'event':
            return self._generate_event_code(func_name)
        elif self.ws_type == 'stream' and not self.message_schema:
            return self._generate_stream_code_no_message(func_name)
        elif self.ws_type == 'stream' and self.message_schema:
            return self._generate_stream_code_with_message(func_name)
        else:
            raise ValueError(f"Unsupported ws_type: {self.ws_type}")

    @staticmethod
    def _generate_func_return_validation_code() -> list[str]:
        code = [
            "            if response is not None:",
            "                await manager.parse_and_send_message(response)",
        ]
        return code

    def _generate_event_code(self, func_name: str) -> list[str]:
        contains_room, contains_client = self._contains_room_and_client_id()
        code = []

        # Initialize the room_id and client_id variables if they are not expected in the method signature
        if not contains_room:
            code.append("    room_id = None")
        if not contains_client:
            code.append("    client_id = str(uuid.uuid4())")

        code += [
            "    await manager.connect(websocket, room_id, client_id)",
            "    try:",
            "        while True:",
            f"            event_data = await websocket.receive_text()",
            f"            response = {'await ' if is_async_function(self.func_body) else ''}{func_name}(event_data, {self._generate_func_body_invocation_params()})",
            "            if response is not None:",
            "                await manager.parse_and_send_message(response)",
        ]

        # Generate exception handler
        code += self._handle_exception()

        return code

    def _generate_stream_code_no_message(self, func_name: str) -> list[str]:
        contains_room, contains_client = self._contains_room_and_client_id()
        code = self._generate_streaming_wrapper_no_input()

        # Initialize room_id and client_id variables if they are not expected in the method signature
        if not contains_room:
            code.append("    room_id = None")
        if not contains_client:
            code.append("    client_id = str(uuid.uuid4())")

        # Connection and main loop logic
        code += [
            "    await manager.connect(websocket, room_id, client_id)",
            "    try:",
            f"        async for response in _streaming_wrapper(websocket, lambda: {func_name}({self._generate_func_body_invocation_params()})):",
            "            if response is not None:",
            "                await manager.parse_and_send_message(response)",
        ]

        # Add exception handling
        code += self._handle_exception()

        return code

    def _generate_stream_code_with_message(self, func_name: str) -> List[str]:
        """
        Generate the code for streaming with message validation.

        Parameters:
            func_name (str): Function name to call.

        Returns:
            List[str]: List of code lines.
        """
        contains_room, contains_client = self._contains_room_and_client_id()
        code = []

        invocation_params = self._generate_func_body_invocation_params()
        if invocation_params:
            invocation_params = ", " + invocation_params

        # Streaming wrapper
        code += self._generate_streaming_wrapper(additional_params=invocation_params)

        # Initialize room_id and client_id variables if they are not expected in the method signature
        if not contains_room:
            code += ["    room_id = None"]
        if not contains_client:
            code += ["    client_id = str(uuid.uuid4())"]

        # Manager connection
        code += ["    await manager.connect(websocket, room_id, client_id)"]

        if self.validate_message_schema:
            schema_validation_code = [
                "        parsed_data = MessageSchema.parse_raw(new_input)",
                "        user_input = parsed_data.dict()",
                "    except ValidationError as e:",
                "        await manager.send_message(json.dumps({'error': str(e)}), room_id, client_id)",
                "        continue"
            ]
            schema_validation_code = [f"        {line}" for line in schema_validation_code]

            # Find the index where "user_input = new_input" should be
            idx = next((i for i, line in enumerate(code) if line.strip() == "user_input = new_input"), None)

            if idx is not None:
                # Replace "user_input = new_input" with validation code
                code[idx:idx + 1] = schema_validation_code

        wrapper_params = self._generate_func_body_invocation_params(skip_room_and_client=True)
        if wrapper_params:
            wrapper_params = ", " + wrapper_params

        code += [
            "    try:",
            f"        async for response in _streaming_wrapper(websocket, client_id=client_id, room_id=room_id, udf={func_name}{wrapper_params}):",
            "            if response is not None:",
            "                await manager.parse_and_send_message(response)",
        ]

        # Add exception handling
        code += self._handle_exception()

        return code

    def _generate_pydantic_model(self, fields: list[str], class_name: str) -> str:
        field_lines = [self._field_to_py_str(field) for field in fields]
        return f"class {class_name}(BaseModel):\n" + "\n".join(field_lines)

    @staticmethod
    def _field_to_py_str(field: str) -> str:
        if ":" not in field:
            print(colored(f"WARNING: No type hint provided for field: {field}. Defaulting to 'Any'.", 'yellow'))
            name = field.strip()
            type_ = 'Any'
        else:
            name, type_ = field.split(":")

        is_optional = '?' in type_
        type_ = type_.replace('?', '').replace('!', '').strip()
        return f"    {name.strip()}: {'Union[' + type_ + ', None]' if is_optional else type_}"

    @staticmethod
    def _generate_streaming_wrapper_no_input() -> list[str]:
        code = """
async def _streaming_wrapper(websocket: WebSocket, udf: Callable[[], Any]) -> AsyncGenerator[str, None]:
    while True:
        async for data in udf():
            yield data
        """.lstrip().split("\n")

        code = ["    " + line for line in code]
        return code

    def _generate_streaming_wrapper(self, additional_params: str = "") -> list[str]:
        additional_params_signature = additional_params.split(", ")
        signature_addon = ""
        for field in additional_params_signature:
            f_name = field.split("=")[0].strip()
            if f_name and f_name != "client_id" and f_name != "room_id":
                signature_addon += f", {f_name}: Any = None"

        code = f"""
async def _streaming_wrapper(websocket: WebSocket, client_id: str, room_id: str, udf: Callable[[str], Any]{signature_addon}) -> AsyncGenerator[str, None]:
    user_input = {'{}' if self.validate_message_schema else "''"}  # default value

    while True:
        try:
            new_input = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
            user_input = new_input
        except asyncio.TimeoutError:
            pass

        async for data in udf(user_input{additional_params}):
            yield data
        """.lstrip().split("\n")

        code = ["    " + line for line in code]
        return code

    @staticmethod
    def _handle_exception() -> List[str]:
        return [
            "    except Exception as e:",
            "        await manager.handle_error(websocket, e)",
        ]

    def __str__(self) -> str:
        func_name = get_function_name_from_ast(self.func_body)

        endpoint_def = [f"@router.websocket('{self.endpoint}')"]

        url_and_query_params = self._generate_func_body_invocation_params()
        func_params = "websocket: WebSocket"
        if url_and_query_params:
            func_params += f", {url_and_query_params}"

        # If message_schema is present and validate_message_schema is True
        if self.message_schema and self.validate_message_schema:
            message_schema = self._generate_pydantic_model(self.message_schema, "MessageSchema")
            endpoint_def = [message_schema] + endpoint_def  # Add Pydantic schema at the beginning

        endpoint_def.append(self._generate_endpoint_signature(func_name=func_name))
        endpoint_def.extend(self._generate_code())
        endpoint_def.append(self.func_body)

        return "\n".join(endpoint_def)
