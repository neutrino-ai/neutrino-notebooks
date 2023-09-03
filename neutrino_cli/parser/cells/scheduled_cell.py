from termcolor import colored

from neutrino_cli.util.ast import get_function_name_from_ast


class ScheduledCell:
    # Class-level counter to generate unique function names for code blocks
    _counter = 0

    def __init__(self, func_body: str, cron: str = None, interval: str = None):
        self.func_body = func_body
        self.cron = cron  # Expecting a string in format "second minute hour day month day_of_week"
        self.interval = interval

    def __str__(self) -> str:
        func_name = get_function_name_from_ast(self.func_body)
        is_already_function = func_name is not None

        if func_name is None:
            func_name = f"generated_func_{ScheduledCell._counter}"
            ScheduledCell._counter += 1

        schedule_def = []

        if self.cron:
            try:
                cron_fields = self.cron.split(' ')
                cron_dict = {
                    'second': cron_fields[0],
                    'minute': cron_fields[1],
                    'hour': cron_fields[2],
                    'day': cron_fields[3],
                    'month': cron_fields[4],
                    'day_of_week': cron_fields[5]
                }

                schedule_def.append(
                    f"@scheduler.scheduled_job('cron', id='{func_name}_cron', name='{func_name}_cron_job', **{cron_dict})")
            except IndexError:
                print(colored("WARNING: Invalid cron format. Not enough fields provided.", 'yellow'))
                return "# Invalid cron format"

        elif self.interval:
            schedule_def.append(
                f"@scheduler.scheduled_job('interval', id='{func_name}_interval', name='{func_name}_interval_job', seconds={self._parse_interval(self.interval)})")

        if not is_already_function:
            schedule_def.append(f"async def scheduled_{func_name}():")

        schedule_def.append("    " + self.func_body.replace("\n", "\n    "))

        return "\n".join(schedule_def)

    def _check_function_args(self):
        func_args = get_function_name_from_ast(self.func_body)
        if func_args is None:
            print(colored("WARNING: Function arguments could not be extracted from AST", 'yellow'))

    @staticmethod
    def _parse_interval(interval: str) -> int:
        """
        Parse the interval and return it in seconds.
        Only supports 's' for seconds, 'm' for minutes, and 'h' for hours.
        """
        unit = interval[-1]
        value = int(interval[:-1])
        if unit == 's':
            return value
        elif unit == 'm':
            return value * 60
        elif unit == 'h':
            return value * 3600
        else:
            print(colored(f"WARNING: Unsupported interval unit: {unit}. Defaulting to seconds.", 'yellow'))
            return value
