from neutrino_cli.compiler.templates.template import Template


class SchedulerTemplate(Template):
    def __init__(self):
        template_variables = {}
        super().__init__('scheduler_template', 'scheduler.py.template', template_variables)

    @classmethod
    def get_template_name(cls):
        return 'scheduler.py.template'
