from typing import List, Union
import re
from termcolor import colored
from util.ast import get_function_name_from_ast, get_function_args_from_ast

class WebSocketCell:
    def __init__(
        self,
        endpoint: str,
        func_body: str,
        query: Union[str, List[str]] = None,
        headers: Union[str, List[str]] = None,
    ):
        self.endpoint = endpoint
        self.query = self._parse_fields(query)
        self.headers = self._parse_fields(headers)
        self.func_body = func_body
        self._check_function_args()

    @staticmethod
    def _parse_fields(fields: str | list[str] | dict[str, str]) -> list[str] | dict[str, str]:
        if isinstance(fields, list):
            return fields
        elif isinstance(fields, str):
            return fields.split(',') if fields else []
        elif isinstance(fields, dict):
            return fields
        else:
            return []

    def _check_function_args(self):
        func_args = get_function_args_from_ast(self.func_body)
        func_name = get_function_name_from_ast(self.func_body)
        if func_args is None:
            print(colored("WARNING: Function arguments could not be extracted from AST", 'yellow'))
        elif "event" not in func_args:
            print(colored(f"WARNING: Missing event object in function {func_name}. Reformat the function as follows:\n"
                          f"\tdef {func_name}(event: str, ...):\n\t\t...", 'yellow'))

    def __str__(self) -> str:
        func_name = get_function_name_from_ast(self.func_body)
        endpoint_def = [f"@router.websocket('{self.endpoint}')"]

        url_params = [f"{name}: {type_ if type_ else 'str'}" for name, type_ in self._extract_url_params()]

        func_params = ["websocket: WebSocket"] + url_params

        if self.query:
            if isinstance(self.query, list):
                func_params.extend([
                    f"{name}: {self._format_type_hint(type_)}"
                    for name, type_ in [q.split(':') for q in self.query]
                ])
            elif isinstance(self.query, dict):
                func_params.extend([
                    f"{name}: {self._format_type_hint(type_)}"
                    for name, type_ in self.query.items()
                ])

        endpoint_def.append(f"async def {func_name}_websocket({', '.join(func_params)}):")
        endpoint_def.append("    await websocket.accept()")
        endpoint_def.extend([
            "    try:",
            "        while True:",
            "            event_data = await websocket.receive_text()",
            f"            response = {func_name}(event_data, {self._generate_func_body_params()})",
            "            if response is not None:",
            "                await websocket.send_text(json.dumps(response))",
            "    except Exception as e:",
            "        if hasattr(e, 'status_code') and hasattr(e, 'message'):",
            "            await websocket.close(code=e.status_code)",
            "        else:",
            "            print(f'WebSocket Error: {e}')",
            "            await websocket.close(code=1007)"
        ])

        endpoint_def.append(self.func_body)

        return "\n".join(endpoint_def)

    def _generate_func_body_params(self) -> str:
        params = []
        for query_param in self.query:
            parts = query_param.split(':')
            if len(parts) == 2:
                key, type_hint = parts
                params.append(f"{key}={key}")
            else:
                print(colored(f"WARNING: Ignoring malformed query parameter: {query_param}", 'yellow'))

        for url_param in self._extract_url_params():
            key, _ = url_param
            params.append(f"{key}={key}")

        return ', '.join(params)

    def _extract_url_params(self):
        matches = re.findall(r"/{([\w]+)}", self.endpoint)
        return [(name, None) for name in matches]

    @staticmethod
    def _format_type_hint(type_hint: str) -> str:
        """Format the type hint based on whether it is optional or required."""
        if type_hint[-1] == '?':
            return f"{type_hint[:-1]} | None = None"
        elif type_hint[-1] == '!':
            return type_hint[:-1]
        else:
            return type_hint

