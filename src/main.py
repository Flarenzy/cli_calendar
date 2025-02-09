import curses
import logging
import os
from _curses import window
from argparse import Namespace

from ArgParser import get_args
from CliCalendar import CliCalender

_CUR_DIR = os.path.dirname(os.path.abspath(__file__))

logger = logging.getLogger(__name__)
logging.basicConfig(filename="cli-calender.log", level=logging.INFO)


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
    curses.start_color()
    init_colors()
    cal = CliCalender()
    cal.handle_args(args)
    curses.curs_set(0)
    cal.draw(stdscr)
    while True:
        cal.move(stdscr)


def main_entry() -> int:
    args = get_args()
    curses.wrapper(main, args)
    return 0


if __name__ == "__main__":
    main_entry()
