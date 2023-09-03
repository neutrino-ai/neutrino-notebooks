import os
import shutil
from pathlib import Path

from neutrino_cli.compiler.ignore_handler import should_ignore_file
from neutrino_cli.compiler.templates import InitPyTemplate
from neutrino_cli.parser.parser import compile_notebook_to_py


def create_dest_dir_if_not_exists(dest_dir: Path):
    """Create destination directory if it doesn't exist.
    Parameters:
        dest_dir (Path): Path to the destination directory.
    """
    if not dest_dir.exists():
        os.makedirs(dest_dir)


def create_init_file(dest_dir: Path, root_path: Path, build_dir: Path):
    """Create __init__.py file in a given directory.
    Parameters:
        dest_dir (Path): Path to the destination directory.
        root_path (Path): Path to the root directory.
        build_dir (Path): Path to the build directory.
    """
    if dest_dir == build_dir:
        return

    init_template = InitPyTemplate(directory=root_path)
    content = init_template.render()
    init_file_path = dest_dir / "__init__.py"
    with open(init_file_path, 'w') as f:
        f.write(content)


def copy_files(root_path: Path, dest_dir: Path, files: list[str], ignore_list: list[str]):
    """Copy or compile files to the destination directory.
    Parameters:
        root_path (Path): Path to the root directory.
        dest_dir (Path): Path to the destination directory.
        files (list): List of files to copy.
        ignore_list (list): List of files and folders to ignore.
    """
    for file in files:
        if should_ignore_file(file, ignore_list):
            continue

        src_file_path = root_path / file
        dest_file_path = dest_dir / file

        if file.endswith('.ipynb'):
            # ignore sandbox files
            if not file.endswith('sandbox.ipynb'):
                code = compile_notebook_to_py(src_file_path)
                dest_file_path = dest_file_path.with_suffix('.py')
                with open(dest_file_path, 'w') as dest_file:
                    dest_file.write(code)
        else:
            shutil.copy(src_file_path, dest_file_path)
