import os

from jinja2 import Environment, FileSystemLoader


class Template:
    def __init__(self, template_dir, template_name, template_variables):
        this_dir = os.path.dirname(os.path.abspath(__file__))
        templates_dir = os.path.join(this_dir, template_dir)
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        self.template_name = template_name
        self.template_variables = template_variables

    @classmethod
    def get_template_name(cls) -> str:
        raise NotImplementedError

    def render(self):
        template = self.env.get_template(self.template_name)
        return template.render(self.template_variables)
