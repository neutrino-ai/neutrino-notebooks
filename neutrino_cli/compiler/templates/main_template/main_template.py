from pathlib import Path

from neutrino_cli.compiler.ignore_handler import should_ignore_file
from neutrino_cli.compiler.templates.template import Template
from neutrino_cli.util.strings import to_snake_case


class MainTemplate(Template):
    def __init__(self, root_dir: Path, ignore_list: list[str] = None):
        if ignore_list is None:
            ignore_list = []

        import_root_routers = []
        register_root_routers = []

        root_ipynbs = [file for file in root_dir.glob("*.ipynb") if not should_ignore_file(file.name, ignore_list)]
        for root_ipynb in root_ipynbs:
            ipynb_name = to_snake_case(root_ipynb.stem)
            router_name = f"{ipynb_name}_router"
            import_root_routers.append(f"from {ipynb_name} import router as {router_name}")
            register_root_routers.append(f"app.include_router({router_name})")

        for subdir in root_dir.iterdir():
            if subdir.is_dir() and not should_ignore_file(subdir.name, ignore_list):
                subdir_name = to_snake_case(subdir.name)

                dir_router_name = f"{subdir_name}_router"
                import_root_routers.append(f"from {subdir_name} import router as {dir_router_name}")
                url_prefix = f'/{subdir_name}' if subdir_name.endswith('_routes') else ''
                register_root_routers.append(f"app.include_router({dir_router_name}, prefix='{url_prefix}')")

        template_variables = {
            "import_root_routers": "\n".join(import_root_routers),
            "register_root_routers": "\n".join(register_root_routers),
        }

        super().__init__('main_template', 'main.py.template', template_variables)
