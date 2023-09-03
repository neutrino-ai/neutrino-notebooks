from neutrino_cli.compiler.templates.template import Template


template = """
# Ignore Python build artifacts and cache
__pycache__
*.py[cod]
*.pyo
*.pyd
*.so
*.egg-info
dist/
build/
*.egg
*.sqlite3

# Ignore virtual environments
.env/
venv/
env/

# Ignore Jupyter Notebook files
.ipynb_checkpoints/

# Ignore IDE and editor files
.idea/
.vscode/
*.swp
*.swo
*.swn
*.suo
*.user
*.bak

# Ignore OS generated files
.DS_Store
Thumbs.db

# Ignore FastAPI specific
instance/
*.env
*.flaskenv
flask_session/

# Ignore database
/db/
/data/

.gitignore
.neutrinoignore
"""


class NeutrinoIgnoreTemplate(Template):
    def __init__(self):
        template_vars = {}
        super().__init__(template_str=template, template_vars=template_vars)

