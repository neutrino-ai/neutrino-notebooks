from setuptools import setup, find_packages

version = {}
with open("neutrino_cli/__version__.py") as fp:
    exec(fp.read(), version)

setup(
    name='neutrino-cli',
    version=version['__version__'],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        'nbformat',
        'autopep8',
        'python-dotenv',
        'termcolor',
        'Jinja2',
        'PyYAML',
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'neutrino=neutrino_cli:cli',  # Replace 'main' with the name of the entry function in your CLI
        ],
    },
)
