import sys
from argparse import ArgumentParser
from argparse import Namespace
from datetime import datetime

from constants import _MONTHS


def get_args() -> Namespace:
    argv = sys.argv[1:]
    parser = ArgumentParser()
    cur_day = datetime.now()
    cur_month = cur_day.strftime("%b")
    parser.add_argument("--month", action="store", default=cur_month,
                        type=str, choices=_MONTHS)
    args = parser.parse_args(argv)
    return args
