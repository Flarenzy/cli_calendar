import curses
import calendar
import os
from datetime import datetime
from argparse import Namespace
from _curses import window

from ArgParser import get_args

_CUR_DIR = os.path.dirname(os.path.abspath(__file__))


def init_colors() -> None:
    colors = [
        (curses.COLOR_RED, curses.COLOR_BLACK),
        (curses.COLOR_GREEN, curses.COLOR_BLACK),
        (curses.COLOR_YELLOW, curses.COLOR_BLACK),
        (curses.COLOR_BLUE, curses.COLOR_BLACK),
        (curses.COLOR_MAGENTA, curses.COLOR_BLACK),
        (curses.COLOR_CYAN, curses.COLOR_BLACK),
        (curses.COLOR_WHITE, curses.COLOR_BLACK),
    ]
    for i, (fg, bg) in enumerate(colors, start=1):
        curses.init_pair(i, fg, bg)


def main(stdscr: window, args: Namespace) -> int:
    stdscr.clear()
    curses.start_color()
    init_colors()
    if curses.has_colors():
        stdscr.addstr("\tWe have colors!\n")
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
    cur_day = datetime.now()
    text_cal = calendar.TextCalendar()

    print(months_to_nums[args.month])
    monthrange = text_cal.formatmonth(cur_day.year, months_to_nums[args.month])
    for line in monthrange.splitlines():
        pair = 0 if str(cur_day.day) not in line else 1
        if not pair:
            stdscr.addstr(f"\t{line}\n", curses.color_pair(0))
        else:
            stdscr.addstr("\t")
            for c in line.split():
                if c == str(cur_day.day):
                    stdscr.addstr(f" {c}", curses.color_pair(1))
                    continue
                stdscr.addstr(f" {c}", curses.color_pair(0))
            stdscr.addstr("\n")
    stdscr.refresh()
    stdscr.getkey()


if __name__ == "__main__":
    args = get_args()
    curses.wrapper(main, args)
