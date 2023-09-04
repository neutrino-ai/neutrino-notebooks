import hashlib
import os
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Union

from neutrino_cli.compiler.templates import DockerfileTemplate, SchedulerTemplate, ConfigTemplate, MainTemplate, \
    WebsocketsManagerTemplate


def hash_file(file_path: str) -> str:
    """Create a SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def requirements_changed(build_dir: str) -> bool:
    """Check if requirements have changed since the last build."""
    requirements_path = os.path.join(build_dir, 'requirements.txt')
    hash_file_path = os.path.join(build_dir, 'requirements_hash.txt')

    # Create hash for the current requirements.txt
    current_hash = hash_file(requirements_path)

    try:
        # Read the previously stored hash
        with open(hash_file_path, 'r') as f:
            previous_hash = f.read().strip()
    except FileNotFoundError:
        previous_hash = None

    return current_hash != previous_hash


def install_requirements_from_build(build_dir: str):
    """Installs Python packages from the requirements.txt file in the build directory.

    Parameters:
        build_dir (str): Path to the build directory.
    """
    requirements_file_path = f"{build_dir}/requirements.txt"
    print(requirements_file_path)
    if os.path.exists(requirements_file_path):
        print("Installing requirements from requirements.txt...")
        subprocess.run(["pip", "install", "-r", requirements_file_path])


def merge_requirements(stock_path: str, user_path: str, output_path: str) -> None:
    """
    Merge two requirements.txt files.

    :param stock_path: File path to the stock requirements file
    :param user_path: File path to the user-defined requirements file
    :param output_path: File path to the output requirements file
    """

    def parse_requirements(file_path: str) -> defaultdict[str, Union[str, None]]:
        """
        Parse a requirements.txt file into a defaultdict.

        :param file_path: File path to the requirements file
        :return: defaultdict of package and version
        """
        reqs = defaultdict(lambda: None)
        with open(file_path, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                pkg_info = line.split("==")
                reqs[pkg_info[0]] = pkg_info[1] if len(pkg_info) > 1 else None
        return reqs

    # Parse stock and user requirements
    stock_reqs = parse_requirements(stock_path)
    user_reqs = parse_requirements(user_path)

    # Update stock requirements with user requirements
    stock_reqs.update(user_reqs)

    # Write the merged requirements to the output file
    with open(output_path, 'w') as f:
        for pkg, version in stock_reqs.items():
            f.write(f"{pkg}{'==' + version if version else ''}\n")


def create_boilerplate_files(build_dir: str, boilerplate_files: list[str], root_dir: Path,
                             ignore_list: list[str] = None, config_data: dict = None) -> None:
    """
    Creates boilerplate files needed for a FastAPI app.

    :param ignore_list:
    :param build_dir: Directory where the build resides
    :param boilerplate_files: List of boilerplate files to be created
    :param root_dir: Root directory of the project
    :param config_data: Project config data
    """
    for file in boilerplate_files:
        file_path = os.path.join(build_dir, file)
        with open(file_path, 'w') as f:
            if file == 'main.py':
                app_main_template = MainTemplate(root_dir, ignore_list=ignore_list, config_data=config_data)
                content = app_main_template.render()  # Assuming a render() method is available
                f.write(content)
            elif file == 'config.py':
                config_template = ConfigTemplate(config_data=config_data)
                content = config_template.render()
                f.write(content)
            elif file == 'Dockerfile':
                dockerfile_template = DockerfileTemplate(config_data=config_data)
                content = dockerfile_template.render()
                f.write(content)
            elif file == 'scheduler.py':
                scheduler_template = SchedulerTemplate()
                content = scheduler_template.render()
                f.write(content)
            elif file == 'websocket_manager.py':
                manager_template = WebsocketsManagerTemplate()
                content = manager_template.render()
                f.write(content)
