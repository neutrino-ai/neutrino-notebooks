from typing import List, Union
from termcolor import colored
from neutrino_cli.util.ast import get_function_name_from_ast, is_async_function

class WebSocketCell:
    def __init__(
            self,
            endpoint: str,
            func_body: str,
            ws_type: str = 'event',
            message_schema: Union[str, List[str]] = None,
            query: Union[str, List[str]] = None,
            headers: Union[str, List[str]] = None,
            validate_message_schema: bool = True,
    ):
        self.endpoint = endpoint
        self.ws_type = ws_type
        self.message_schema = self._parse_fields(message_schema)
        self.query = self._parse_fields(query)
        self.headers = self._parse_fields(headers)
        self.func_body = func_body
        self.validate_message_schema = validate_message_schema

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

    def _generate_func_body_params(self) -> str:
        params = []
        if self.query:
            for query_param in self.query:
                key, type_hint = query_param.split(':')
                params.append(f"{key}={key}")

        return ', '.join(params)

    def _generate_code(self) -> List[str]:
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

    def _generate_event_code(self, func_name: str) -> List[str]:
        code = [
            "    await websocket.accept()",
            "    try:",
            "        while True:",
            f"            event_data = await websocket.receive_text()",
            f"            response = {'await ' if is_async_function(self.func_body) else ''}{func_name}(event_data, {self._generate_func_body_params()})",
            "            if response is not None:",
            "                await websocket.send_text(json.dumps(response))",
        ]
        code = code + self._handle_exception()

        return code

    def _generate_stream_code_no_message(self, func_name: str) -> List[str]:
        code = self._generate_streaming_wrapper_no_input()

        code = code + [
            "    await websocket.accept()",
            "    try:",
            f"        async for response in _streaming_wrapper(websocket, {func_name}):",
            "            await websocket.send_text(json.dumps(response))"
        ]
        code = code + self._handle_exception()

        return code

    def _generate_stream_code_with_message(self, func_name: str) -> List[str]:
        """
        Generate the code for streaming with message validation.

        Parameters:
            func_name (str): Function name to call.

        Returns:
            List[str]: List of code lines.
        """
        code = self._generate_streaming_wrapper()

        if self.validate_message_schema:
            schema_validation_code = [
                "        parsed_data = MessageSchema.parse_raw(new_input)",
                "        user_input = parsed_data.dict()",
                "    except ValidationError as e:",
                '        await websocket.send_text(f"Error: {e.json()}")',
                "        continue"
            ]
            schema_validation_code = [f"        {line}" for line in schema_validation_code]

            # Find the index where "user_input = new_input" should be
            idx = next((i for i, line in enumerate(code) if line.strip() == "user_input = new_input"), None)

            if idx is not None:
                # Replace "user_input = new_input" with validation code
                code[idx:idx + 1] = schema_validation_code

        code += [
            "    await websocket.accept()",  # Accept the WebSocket connection
            "    try:",
            f"        async for data in _streaming_wrapper(websocket, {func_name}):",
            "            await websocket.send_text(json.dumps(data))"  # Send the data received from the generator
        ]
        code += self._handle_exception()  # Add exception handling

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
        """.split("\n")

        code = ["    " + line for line in code]
        return code

    def _generate_streaming_wrapper(self) -> list[str]:
        code = f"""
async def _streaming_wrapper(websocket: WebSocket, udf: Callable[[str], Any]) -> AsyncGenerator[str, None]:
    user_input = {'{}' if self.validate_message_schema else "''"}  # default value

    while True:
        try:
            new_input = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
            user_input = new_input
        except asyncio.TimeoutError:
            pass

        async for data in udf(user_input):
            yield data
        """.split("\n")

        code = ["    " + line for line in code]
        return code

    @staticmethod
    def _handle_exception() -> List[str]:
        return [
            "    except Exception as e:",
            "        if hasattr(e, 'status_code') and hasattr(e, 'message'):",
            "            await websocket.close(code=e.status_code)",
            "        else:",
            "            print(f'WebSocket Error: {e}')",
            "            await websocket.close(code=1007)"
        ]

    def __str__(self) -> str:
        func_name = get_function_name_from_ast(self.func_body)

        endpoint_def = [f"@router.websocket('{self.endpoint}')"]
        func_params = [f"websocket: WebSocket"]

        # If message_schema is present and validate_message_schema is True
        if self.message_schema and self.validate_message_schema:
            message_schema = self._generate_pydantic_model(self.message_schema, "MessageSchema")
            endpoint_def = [message_schema] + endpoint_def  # Add Pydantic schema at the beginning

        endpoint_def.append(f"async def {func_name}_websocket({', '.join(func_params)}):")
        endpoint_def.extend(self._generate_code())
        endpoint_def.append(self.func_body)

        return "\n".join(endpoint_def)
