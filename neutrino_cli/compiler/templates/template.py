import autopep8
from jinja2 import Environment


class Template:
    def __init__(self, template_str: str, template_vars: dict, is_python: bool = False):
        self.env = Environment()
        self.template_str = template_str  # Template stored as a string
        self.template_vars = template_vars
        self.is_python = is_python

    def render(self):
        try:
            template = self.env.from_string(self.template_str)
            code = template.render(self.template_vars)
            if self.is_python:
                code = autopep8.fix_code(code)
            return code.lstrip()
        except Exception as e:
            print(f"Error rendering template: {e}")
            raise
