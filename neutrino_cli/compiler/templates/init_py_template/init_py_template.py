from pathlib import Path

from neutrino_cli.compiler.templates.template import Template
from neutrino_cli.util.strings import to_snake_case


template = """
from fastapi import APIRouter

{% for filename, router_name, _ in route_files %}
from .{{ filename }} import router as {{ router_name }}
{% endfor %}
{% for dir_name, router_name, _ in nested_routers %}
from .{{ dir_name }} import router as {{ router_name }}
{% endfor %}

router = APIRouter()

{% for _, router_name, url_prefix in route_files %}
router.include_router({{ router_name }}, prefix="{{ url_prefix }}")
{% endfor %}
{% for _, router_name, url_prefix in nested_routers %}
router.include_router({{ router_name }}, prefix="{{ url_prefix }}")
{% endfor %}
"""

class InitPyTemplate(Template):
    def __init__(self, directory: Path):
        nested_routers = []
        route_files = []

        # For files directly in the directory
        root_files = [
            file for file in directory.glob("*.ipynb")
            if file.stem != "__init__" and not file.name.endswith("sandbox.ipynb")
        ]
        for root_file in root_files:
            filename = to_snake_case(root_file.stem)
            router_name = f"{filename}_router"
            url_prefix = f'/{filename}' if not filename.lower().endswith('routes') else ''
            route_files.append((filename, router_name, url_prefix))

        # For subdirectories
        for subdir in directory.iterdir():
            if subdir.is_dir():
                init_file = subdir / "__init__.py"
                sub_nested_routers = [file for file in subdir.glob("*.ipynb")]

                if init_file.exists() or sub_nested_routers:
                    subdir_name = to_snake_case(subdir.name)
                    router_name = f'{subdir_name}_router'
                    url_prefix = f'/{subdir_name}' if not subdir_name.lower().endswith('routes') else ''
                    nested_routers.append((subdir_name, router_name, url_prefix))

        template_vars = {
            "nested_routers": nested_routers,
            "route_files": route_files,
        }

        super().__init__(template_str=template, template_vars=template_vars, is_python=True)
