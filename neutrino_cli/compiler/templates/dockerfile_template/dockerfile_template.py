from neutrino_cli.compiler.templates.template import Template


template = """
# start by pulling the python image
FROM python:3.11

# switch working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Run Uvicorn server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{{api_port}}"]
"""


class DockerfileTemplate(Template):
    def __init__(self, config_data: dict = None):
        if not config_data:
            config_data = {}

        template_variables = {
            'api_port': config_data.get('api_port', 8080)
        }

        super().__init__(template_str=template, template_vars=template_variables)

