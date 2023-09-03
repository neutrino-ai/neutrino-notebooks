import re
from typing import Union

from termcolor import colored

from neutrino_cli.util.ast import get_function_name_from_ast, get_function_args_from_ast, is_async_function
from neutrino_cli.util.strings import snake_to_pascal


class HttpCell:
    def __init__(
            self,
            http: str,
            body: Union[str, list[str]],
            resp: Union[str, list[str]],
            query: Union[str, list[str]],
            headers: Union[str, list[str]],
            endpoint: str,
            func_body: str
    ):
        self.http = http
        self.endpoint = endpoint
        self.body = self._parse_fields(body)
        self.resp = self._parse_fields(resp)
        self.query = self._parse_fields(query)
        self.headers = self._parse_fields(headers)
        self.func_body = func_body

        self._check_function_args()

    def _check_function_args(self):
        func_args = get_function_args_from_ast(self.func_body)
        func_name = get_function_name_from_ast(self.func_body)
        if func_args is None:
            print(colored("WARNING: Function arguments could not be extracted from AST", 'yellow'))
            return

        if not isinstance(self.body, list) or not isinstance(self.query, list):
            print(colored(
                f"ERROR: self.body and self.query should be lists, found {type(self.body)} and {type(self.query)} instead",
                'red'))
            return

        expected_args = set([arg.split(":")[0].strip() for arg in self.body + self.query])
        url_params = set([param[0] for param in self._extract_url_params()])
        expected_args.update(url_params)
        missing_args = expected_args - set(func_args)
        if missing_args:
            print(colored(f"WARNING: Missing expected arguments in function {func_name}: {', '.join(missing_args)}",
                          'yellow'))

    @staticmethod
    def _parse_fields(fields: Union[str, list[str]]) -> list[str]:
        return fields if isinstance(fields, list) else fields.split(',') if fields else []

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

    def _extract_url_params(self) -> list[tuple[any, str]]:
        return [(name, 'str') for name in re.findall(r"/{([\w]+)}", self.endpoint)]

    def _generate_func_body_params(self) -> str:
        def clean_field(field: str) -> str:
            return field.split(":")[0].strip()

        # Handling body params
        body_params = []
        if self.body:
            for field in self.body:
                clean_field_name = clean_field(field)
                body_params.append(f"{clean_field_name}=body.{clean_field_name}")

        # Handling query params
        query_params = [f"{clean_field(field)}={clean_field(field)}" for field in self.query]

        # Handling URL params
        url_params = [f"{name}={name}" for name, _ in self._extract_url_params()]

        all_params = body_params + query_params + url_params

        return ', '.join(all_params)

    def __str__(self) -> str:
        if not self.http or not self.endpoint:
            return "# Missing HTTP method or endpoint."

        func_name = get_function_name_from_ast(self.func_body)
        pascal_func_name = snake_to_pascal(func_name) if func_name else None
        model_names = [f"{pascal_func_name}{suffix}" if pascal_func_name else suffix for suffix in
                       ["RequestBody", "ResponseModel"]]

        endpoint_def = []
        for model_name, fields in zip(model_names, [self.body, self.resp]):
            if fields:
                endpoint_def.append(f"{self._generate_pydantic_model(fields, model_name)}\n")

        endpoint_def.append(f"@router.{self.http.lower()}('{self.endpoint}')")

        url_params = self._extract_url_params()
        func_params = [f"{name}: {type_}" for name, type_ in url_params]

        if self.body:
            func_params.append(f"body: {model_names[0]}")
        if self.query:
            func_params.extend([f"{name}: {type_}" for name, type_ in [q.split(':') for q in self.query]])

        is_async = is_async_function(self.func_body)

        endpoint_def.append(f"async def {func_name}_endpoint({', '.join(func_params)}):")
        endpoint_def.extend([
            "    try:",
            f"        return {'await ' if is_async else ''}{func_name}({self._generate_func_body_params()})",
            "    except Exception as e:",
            "        if hasattr(e, 'status_code') and hasattr(e, 'message'):",
            "            raise HTTPException(status_code=e.status_code, detail=f'{e.message}')",
            "        else:",
            "            raise HTTPException(status_code=500, detail=f'Internal Server Error: {str(e)}')"
        ])
        endpoint_def.append(self.func_body)
        return "\n".join(endpoint_def)
