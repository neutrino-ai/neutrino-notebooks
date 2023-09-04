#!/usr/bin/env python3

import os
import subprocess
import traceback
from pathlib import Path

import click
import yaml
from termcolor import colored

from neutrino_cli.compiler.build_setup import hash_file, requirements_changed
from neutrino_cli.compiler.compiler import compile_notebooks_into_build, create_dest_dir_if_not_exists, format_python_files_in_dir, \
    merge_project_requirements, \
    create_boilerplate_files_in_dir
from neutrino_cli.compiler.ignore_handler import read_ignore_list
from neutrino_cli.compiler.templates import NeutrinoIgnoreTemplate, NeutrinoConfigTemplate


@click.group()
def cli():
    """Neutrino CLI for running and deploying projects."""
    pass


@click.command()
@click.option('--name', default="NeutrinoProject", help='Your project name.')
def init(name: str):
    """Initialize a new Neutrino project."""
    ignore_file_path = '.neutrinoignore'
    neutrino_config_file_path = 'neutrinoconfig.yml'

    # Check if .neutrinoignore already exists
    if os.path.exists(ignore_file_path) or os.path.exists(neutrino_config_file_path):
        print(colored("This project already contains a neutrinoconfig.yml!", 'yellow'))
        return

    try:
        # Create .neutrinoignore and populate with default ignores
        with open(ignore_file_path, 'w') as f:
            ignore_template = NeutrinoIgnoreTemplate()
            content = ignore_template.render()
            f.write(content)
        with open(neutrino_config_file_path, 'w') as f:
            config_template = NeutrinoConfigTemplate(project_name=name)
            content = config_template.render()
            f.write(content)

        print(colored(f"{neutrino_config_file_path} and {ignore_file_path} created successfully.", 'green'))

    except Exception as e:
        print(colored(f"An unexpected error occurred: {e}", 'red'))
        print(traceback.format_exc())


@click.command()
@click.option('--source', default=os.getcwd(), type=click.Path(exists=True), help='Path to the source folder.')
def build(source: str):
    try:
        config_data = None

        # Look for configuration file
        for file_name in ["neutrinoconfig.yml", "neutrino_config.yaml"]:
            if os.path.exists(file_name):
                with open(file_name, 'r') as f:
                    config_data = yaml.safe_load(f)
                break

        if not config_data:
            print(colored("neutrino_config.yaml not found. Using default settings.", 'yellow'))

        print(colored("Building Neutrino project...", 'cyan'))

        build_dir = './build'
        create_dest_dir_if_not_exists(Path(build_dir))

        ignore_list = read_ignore_list()
        compile_notebooks_into_build(source, build_dir, ignore_list)

        format_python_files_in_dir(build_dir)
        merge_project_requirements(source, build_dir)
        create_boilerplate_files_in_dir(source, build_dir, ignore_list=ignore_list, config_data=config_data)

        # Hash the requirements.txt file
        requirements_path = os.path.join(build_dir, '../requirements.txt')
        requirements_hash = hash_file(requirements_path)

        # Save the hash for future comparison
        with open(os.path.join(build_dir, 'requirements_hash.txt'), 'w') as f:
            f.write(requirements_hash)

        print(colored("Build completed successfully.", 'green'))

    except FileNotFoundError as e:
        print(colored(f"File not found: {e}", 'red'))
    except PermissionError as e:
        print(colored(f"Permission Error: {e}", 'red'))
    except Exception as e:
        print(colored(f"An unexpected error occurred: {e}", 'red'))
        print(traceback.format_exc())
    finally:
        print(colored("Build process finished.", 'yellow'))


@click.command()
@click.option('--docker', is_flag=True, help='Run using Docker.')
@click.option('--port', default=8080, help='Port to run the server on.')
def run(docker, port):
    """Run your code."""
    build_dir = './build'
    build_dir_absolute = Path(build_dir).resolve()

    if not os.path.exists(build_dir):
        print(colored("ERROR: The project hasn't been built. Run 'build' command first.", 'red'))
        return

    main_file_path = os.path.join(build_dir, 'main.py')

    if not os.path.exists(main_file_path):
        print(colored(f"ERROR: main.py not found in {build_dir}. Ensure the project was built correctly.", 'red'))
        return

    print(colored("Launching Neutrino server...", 'cyan'))

    try:
        # Change directory to build
        os.chdir(build_dir)

        if docker:
            # Docker-related logic
            subprocess.run(["docker", "build", "-t", "neutrino-server", "."], check=True)
            subprocess.run(["docker", "run", "-p", f"{port}:8080", "neutrino-server"], check=True)
        else:
            # Check if requirements have changed
            if requirements_changed(str(build_dir_absolute)):
                print(colored("Requirements have changed, installing...", 'cyan'))
                subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)

                # Update the hash file
                with open(build_dir_absolute / 'requirements_hash.txt', 'w') as f:
                    f.write(hash_file(str(build_dir_absolute / "requirements.txt")))

            # Run FastAPI app with uvicorn for hot reloading
            subprocess.run(["uvicorn", "main:app", "--reload", "--port", str(port)], check=True)

    except subprocess.CalledProcessError as e:
        print(colored(f"Error in running the server: {e}", 'red'))
    except Exception as e:
        print(colored(f"An unexpected error occurred: {e}", 'red'))


@click.command()
def deploy():
    """Deploy your code."""
    print("Deploying code...")
    # Your 'deploy' logic here.


# Adding commands to the CLI group
cli.add_command(init)
cli.add_command(run)
cli.add_command(deploy)
cli.add_command(build)

if __name__ == "__main__":
    cli()
