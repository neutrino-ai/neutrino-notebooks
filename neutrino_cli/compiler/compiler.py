import os
from pathlib import Path

import autopep8

from neutrino_cli.compiler.build_setup import merge_requirements, create_boilerplate_files
from neutrino_cli.compiler.file_utilities import create_init_file, create_dest_dir_if_not_exists, copy_files
from neutrino_cli.compiler.ignore_handler import should_ignore_file
from neutrino_cli.compiler.templates import RequirementsTemplate


def compile_notebooks_into_build(source_path: str, build_dir: str, ignore_list: list[str] = None):
    source_path = Path(source_path).resolve()
    build_dir = Path(build_dir).resolve()
    if ignore_list is None:
        ignore_list = []

    for root, dirs, files in os.walk(source_path):
        root_path = Path(root).resolve()

        # Make root_path relative to source_path for proper ignoring
        relative_root_path = root_path.relative_to(source_path)

        # Explicitly ignore .ipynb_checkpoints directories
        dirs[:] = [d for d in dirs if d != '.ipynb_checkpoints' and d not in ignore_list]
        # Skip directories in ignore_list
        dirs[:] = [d for d in dirs if not should_ignore_file(str((relative_root_path / d).as_posix()), ignore_list)]

        process_directory(root_path, source_path, build_dir, files, ignore_list)


def process_directory(root_path: Path, source_path: Path, build_dir: Path, files: list[str], ignore_list: list[str]):
    rel_root = root_path.relative_to(source_path)
    dest_dir = build_dir / rel_root

    if should_ignore_file(str(rel_root), ignore_list):
        return

    create_dest_dir_if_not_exists(dest_dir)

    # Skip creating __init__.py in the root directory
    if rel_root and any(file.endswith('.ipynb') for file in files):
        create_init_file(dest_dir, root_path, build_dir=build_dir)

    copy_files(root_path, dest_dir, files, ignore_list)


def format_python_files_in_dir(directory: str):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    code = f.read()

                formatted_code = autopep8.fix_code(code)

                with open(file_path, 'w') as f:
                    f.write(formatted_code)


def merge_project_requirements(source_path: str, build_dir: str):
    user_requirements = os.path.join(source_path, 'requirements.txt')
    output_requirements = os.path.join(build_dir, 'requirements.txt')

    # create new requirements.txt
    requirements_template = RequirementsTemplate()
    requirements_content = requirements_template.render()
    with open(output_requirements, 'w') as f:
        f.write(requirements_content)

    if os.path.exists(user_requirements):
        merge_requirements(output_requirements, user_requirements, output_requirements)


def create_boilerplate_files_in_dir(
        source_path: str,
        build_dir: str,
        ignore_list: list[str] = None,
        config_data: dict = None
):
    boilerplate_files = ['main.py', 'config.py', 'Dockerfile', 'scheduler.py', 'websocket_manager.py']
    create_boilerplate_files(
        build_dir,
        boilerplate_files,
        root_dir=Path(source_path),
        ignore_list=ignore_list,
        config_data=config_data
    )
