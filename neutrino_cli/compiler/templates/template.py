from jinja2 import Environment


class Template:
    def __init__(self, template_str: str, template_vars: dict):
        self.env = Environment()
        self.template_str = template_str  # Template stored as a string
        self.template_vars = template_vars

    def render(self):
        try:
            template = self.env.from_string(self.template_str)
            return template.render(self.template_vars)
        except Exception as e:
            print(f"Error rendering template: {e}")
            raise
