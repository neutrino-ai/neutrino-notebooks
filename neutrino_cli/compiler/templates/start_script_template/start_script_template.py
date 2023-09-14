from neutrino_cli.compiler.templates.template import Template


template = """
#!/bin/sh

# Get the value of PORT environment variable, if not set, default to 8080
PORT=${PORT:-8080}

# Run your application
exec uvicorn main:app --host 0.0.0.0 --port $PORT
"""


class StartScriptTemplate(Template):
    def __init__(self):
        template_variables = {}

        super().__init__(template_str=template, template_vars=template_variables)

