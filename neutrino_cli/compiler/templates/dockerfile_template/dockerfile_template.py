from neutrino_cli.compiler.templates.template import Template


class DockerfileTemplate(Template):
    def __init__(self):
        template_variables = {}
        super().__init__('dockerfile_template', 'Dockerfile.template', template_variables)

    @classmethod
    def get_template_name(cls):
        return 'Dockerfile.template'
