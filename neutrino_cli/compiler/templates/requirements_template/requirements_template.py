from neutrino_cli.compiler.templates.template import Template


class RequirementsTemplate(Template):
    def __init__(self):
        template_variables = {}
        super().__init__('requirements_template', 'requirements.template', template_variables)

    @classmethod
    def get_template_name(cls):
        return 'requirements.template'
