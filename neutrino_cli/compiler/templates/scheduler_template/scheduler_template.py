from neutrino_cli.compiler.templates.template import Template


template = """
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
"""


class SchedulerTemplate(Template):
    def __init__(self):
        template_vars = {}
        super().__init__(template_str=template, template_vars=template_vars, is_python=True)

