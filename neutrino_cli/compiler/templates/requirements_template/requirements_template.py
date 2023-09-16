from neutrino_cli.compiler.templates.template import Template
import platform

template = """
numpy
scipy
scikit-learn
matplotlib
pandas
PyYAML
Jinja2
gunicorn==20.1.0
python-dotenv
httptools
fastapi
uvicorn
python-dotenv
websockets
APScheduler
"""


class RequirementsTemplate(Template):
    def __init__(self):
        # Detect OS
        if platform.system() != "Windows":  # Mac OS
            template += "\nuvloop"

        template_vars = {}
        super().__init__(template_str=template, template_vars=template_vars)
