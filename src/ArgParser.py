import sys
from argparse import ArgumentParser
from argparse import Namespace
from datetime import datetime

from constants import _COLORS
from constants import _DAYS
from constants import _MONTHS

DESCRIPTION = """
cli_calender is an interactive calender avaiable in the terminal.
Just running with no flags opens the calender of the current month.
By specifing --year, --month or --day you can chose to open the calender
on the specific date.
To the right of the calender are the task added for the current in
ascending time order.
You can add or delete desk with the task subcomand.
"""


def get_args(argv: list[str] | None = None) -> Namespace:
    if argv is None:
        argv = sys.argv[1:]
    parser = ArgumentParser(description=DESCRIPTION)
    cur_date = datetime.now()
    cur_month = cur_date.strftime("%b")
    cur_day = int(cur_date.strftime("%-d"))
    cur_year = int(cur_date.strftime("%Y"))
    parser.add_argument("--year",
                        action="store",
                        default=cur_year,
                        type=int,
                        help="The int value of the year.")
    parser.add_argument("--month",
                        action="store",
                        default=cur_month,
                        type=str,
                        help="The month of the year in short format",
                        choices=_MONTHS)
    parser.add_argument("--day",
                        action="store",
                        default=cur_day,
                        type=int,
                        choices=_DAYS,
                        help="The day of the month.")
    subparsers = parser.add_subparsers(dest="command")
    task = subparsers.add_parser("task", help="Subcommand for adding "
                                 "and deleting tasks.")
    config = subparsers.add_parser("config", help="Configure the settings - "
                                   "colors of the calender.")
    config.add_argument("--bg-color",
                        action="store",
                        help="Change the background color.",
                        type=str,
                        choices=_COLORS)
    config.add_argument("--cursor-color",
                        action="store",
                        help="Change the cursors color.",
                        type=str,
                        choices=_COLORS)
    config.add_argument("--task-color",
                        action="store",
                        help="Change the task text color.",
                        type=str,
                        choices=_COLORS)
    config.add_argument("--task-title",
                        action="store",
                        help="Change the background color.",
                        type=str,
                        choices=_COLORS)
    config.add_argument("--calendar-color",
                        action="store",
                        help="Change the background color.",
                        type=str,
                        choices=_COLORS)
    task_subpars = task.add_subparsers(dest="task_command")
    add_task = task_subpars.add_parser("add",
                                       help="Add task to calender. "
                                            "Needs to be used with --date.")
    delete_task = task_subpars.add_parser("delete",
                                          help="Delete task from calender."
                                               "Needs to be used with --date.")
    add_task.add_argument("--date",
                          action="store",
                          type=str,
                          required=True,
                          help="The date in the following format:"
                          " YYYY-MM-DD HH:mm")
    add_task.add_argument("description",
                          action="store",
                          type=str,
                          help="Description of the task to"
                          " add.")
    delete_task.add_argument("--date",
                             action="store",
                             type=str,
                             required=True,
                             help="The date in the following format:"
                                  " YYYY-MM-DD HH:mm. "
                                  "Time is in the 24h format.")
    args = parser.parse_args(argv)
    return args
