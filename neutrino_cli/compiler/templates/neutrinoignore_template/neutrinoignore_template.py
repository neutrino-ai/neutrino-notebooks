from neutrino_cli.compiler.templates.template import Template


class NeutrinoIgnoreTemplate(Template):
    def __init__(self):
        template_variables = {}
        super().__init__('neutrinoignore_template', 'neutrinoignore.template', template_variables)

    @classmethod
    def get_template_name(cls):
        return 'neutrinoignore.template'
