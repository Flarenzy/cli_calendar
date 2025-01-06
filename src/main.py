import calendar
import os
from argparse import ArgumentParser
from datetime import datetime
# from datetime import timedelta
# from datetime import timezone
from typing import Sequence

from constants import _MONTHS

_CUR_DIR = os.path.dirname(os.path.abspath(__file__))


def main(argv: Sequence[str] | None = None) -> int:
    months_to_nums = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Avg": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12,
    }
    parser = ArgumentParser()
    cur_day = datetime.now()
    cur_month = cur_day.strftime("%b")
    parser.add_argument("--month", action="store", default=cur_month,
                        type=str, choices=_MONTHS)
    text_cal = calendar.TextCalendar()
    args = parser.parse_args(argv)
    print(months_to_nums[args.month])
    monthrange = text_cal.formatmonth(cur_day.year, months_to_nums[args.month])
    for line in monthrange.splitlines():
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
