from neutrino_cli.compiler.templates.template import Template


template = """
#!/bin/bash

# Redirect output to stderr.
exec 1>&2

# Run nbstripout on staged .ipynb files before commit
git diff --name-only --cached | grep '.ipynb$' | xargs -L1 nbstripout
"""


class PreCommitHookTemplate(Template):
    def __init__(self):
        template_vars = {}
        super().__init__(template_str=template, template_vars=template_vars)

