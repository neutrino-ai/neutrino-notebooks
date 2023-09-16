from neutrino_cli.compiler.templates.template import Template
import platform

mac_template = """
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

# Add execution permission to your shell script and run it
COPY start.sh /start.sh
RUN chmod +x /start.sh
CMD ["/start.sh"]
"""

windows_template = """# Start by pulling the Python image
FROM python:3.11

# Switch working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Add execution permission to your shell script
COPY start.sh /start.sh

# Install dos2unix and convert line endings in start.sh
RUN apt-get update && \
    apt-get install -y dos2unix && \
    dos2unix /start.sh && \
    apt-get --purge remove -y dos2unix && \
    apt-get autoremove -y && \
    apt-get clean

# Make the shell script executable
RUN chmod +x /start.sh

# Run the shell script
CMD ["/start.sh"]"""


class DockerfileTemplate(Template):
    def __init__(self, config_data: dict = None):
        if not config_data:
            config_data = {}

        template_variables = {
            'api_port': config_data.get('api_port', 8080)
        }

        # Detect the platform
        if platform.system() == "Darwin":  # Mac OS
            template_str = mac_template
        elif platform.system() == "Windows":
            template_str = windows_template
        else:
            # Optionally handle other platforms or set a default
            template_str = mac_template  # Set mac_template as default, for example

        super().__init__(template_str=template_str, template_vars=template_variables)
