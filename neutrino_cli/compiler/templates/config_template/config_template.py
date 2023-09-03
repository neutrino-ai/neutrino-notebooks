from neutrino_cli.compiler.templates.template import Template


class ConfigTemplate(Template):
    def __init__(self):
        template_vars = {}
        super().__init__('config_template', 'config.py.template', template_vars)

    @classmethod
    def get_template_name(cls) -> str:
        return 'config.py.template'
