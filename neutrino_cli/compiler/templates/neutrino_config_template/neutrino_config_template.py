from neutrino_cli.compiler.templates.template import Template


template = """
project:
    name: {{project_name}}
    version: 0.0.1
    config:
        port: {{port}}
"""


class NeutrinoConfigTemplate(Template):
    def __init__(self, project_name: str):
        template_vars = {
            'project_name': project_name,
            'port': 8080
        }
        super().__init__(template_str=template, template_vars=template_vars)

