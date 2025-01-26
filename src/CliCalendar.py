import curses
import calendar
import os
import sys
import signal
import sqlite3
import logging
from argparse import Namespace
from datetime import datetime
from _curses import window
from typing import Any
from typing import Optional

from constants import DB_NAME
from constants import DB_TABLE

_CUR_DIR = os.path.dirname(os.path.abspath(__file__))

logger = logging.getLogger(__name__)
logging.basicConfig(filename="cli-calender.log", level=logging.INFO)


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

nums_to_months = {v: k for k, v in months_to_nums.items()}


class CliCalender():

    def __init__(self):
        self.pos = (0, 0)  # (y, x) 
        self.state_matrix = None
        self._text_cal = calendar.TextCalendar()
        self._date = datetime.now()
        self._month_calender = self._gen_current_month(self._date.year,
                                                       self._date.month)
        self._init_db()

    def _init_db(self) -> None:
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute(f"CREATE TABLE IF NOT EXISTS {DB_TABLE} (" 
                    " date TEXT UNIQUE NOT NULL, task TEXT NOT NULL)")
        cur.close()
        con.commit()
        con.close()

    def _gen_current_month(self, year: int = 0, month: int = 0) -> str:
        return self._text_cal.formatmonth(year, month)

    def _draw_tasks(self, win: window) -> None:
        four_spaces = "    "
        win.clear()
        win.addstr(f"\n\n{four_spaces}Tasks:", curses.color_pair(1))
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        day_beging = self._date.strftime("%Y-%m-%d") + " 00:00:00"
        day_end = self._date.strftime("%Y-%m-%d") + " 23:59:00"
        for date, task in cur.execute(f"SELECT date, task from {DB_TABLE} "
                                      "WHERE date > ? "
                                      "AND date < ? ORDER BY date ASC",
                                      (day_beging, day_end)):
            hour = datetime.strptime(date, "%Y-%m-%d %H:%M:%S").time()\
                .strftime("%H:%M")
            logger.debug(f"Printing task: {task} to side window. Hour: {hour}")
            win.addstr(f"\n{four_spaces}{hour}: {task}",
                       curses.color_pair(3))
        cur.close()
        con.close()

    def draw(self, stdscr: window, day: Optional[str] = None) -> None:
        if not day:
            day = self._date.strftime("%-d")
        else:
            self._date = self._date.replace(day=int(day))
        stdscr.clear()
        stdscr.addstr("\n\n")
        if len(day) == 1:
            day = " " + day
        four_spaces = "    "
        found = False
        for i, line in enumerate(self._month_calender.splitlines()):
            logger.debug(f"Entered loop with index {i}")
            if day not in line or found:
                stdscr.addstr(f"{four_spaces}{line}\n", curses.color_pair(0))
                continue
            stdscr.addstr(f"{four_spaces}")
            if i == 2:
                self._pad_line(stdscr, line)
            x_pos = line.index(day)
            self.pos = (i, x_pos)
            logger.debug(f"current pos is {self.pos}")
            logger.debug(f"current num is:{line[x_pos:x_pos+2]}")
            for j, c in enumerate(line.split()):
                if len(c) == 1:
                    c = " " + c
                if c == day:
                    if j != 0:
                        stdscr.addstr(" ")
                    attrs = curses.color_pair(1) | curses.A_STANDOUT
                    stdscr.addstr(f"{c}", attrs)
                    found = True
                    continue
                if j != 0:
                    c = " " + c
                stdscr.addstr(f"{c}", curses.color_pair(0))
            stdscr.addstr("\n")
        max_y, max_x = stdscr.getmaxyx()
        win = curses.newwin(max_y,
                            max_x // 4,
                            0,
                            max_x // 4)

        # win.addstr(f"\n{four_spaces}Task 1: pick up car", curses.color_pair(3))
        stdscr.refresh()
        self._draw_tasks(win)
        win.refresh()

    def _handle_signal(self, signal_number: int, frame: Any) -> None:
        # clean up any db cons? 
        curses.endwin()
        logger.info(f"Exiting on signal: {signal_number}")
        sys.exit(0)

    def move(self, stdscr: window) -> None:
        temp = self._month_calender.splitlines()
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTSTP, self._handle_signal)
        m = len(temp)
        n = len(temp[2])
        logger.debug("======================")
        match stdscr.getkey():
            case "KEY_UP":
                if self.pos[0] - 1 > 1:
                    logger.debug(f"Going from pos {self.pos} to "
                                f"{self.pos[0]-1}:{self.pos[1]}")
                    day = temp[self.pos[0] - 1][self.pos[1]:self.pos[1] + 2]
                    day = day.strip()
                    if not day.isnumeric():
                        logger.debug(f"Early exit {day}")
                        return
                    logger.debug(f"new day is {day}")
                    self.draw(stdscr, day)
                    logger.debug("Yoou pressed up!")
            case "KEY_DOWN":
                if self.pos[0] + 1 < m:
                    logger.debug(f"Going from pos {self.pos} to "
                                f"{self.pos[0] + 1}:{self.pos[1]}")
                    day = temp[self.pos[0] + 1][self.pos[1]:self.pos[1] + 2]
                    day = day.strip()
                    if not day.isnumeric():
                        logger.debug(f"Early exit {day}")
                        return
                    logger.debug(f"new day is {day}")
                    self.draw(stdscr, day)
                    logger.debug("Yoou pressed down!")
            case "KEY_LEFT":
                if self.pos[1] - 3 >= 0:
                    logger.debug(f"Going from pos {self.pos} to "
                                 f"{self.pos[0]}:{self.pos[1] - 3}")
                    day = temp[self.pos[0]][self.pos[1] - 3:self.pos[1]]
                    day = day.strip()
                    if not day.isnumeric():
                        logger.debug(f"Early exit {day}")
                        return
                    logger.debug(f"new day is {day}")
                    self.draw(stdscr, day)
                    logger.debug("Yoou pressed left!")
            case "KEY_RIGHT":
                if self.pos[1] + 3 < n:
                    logger.debug(f"Going from pos {self.pos} to "
                                f"{self.pos[0]}:{self.pos[1] + 3}")
                    day = temp[self.pos[0]][self.pos[1] + 3:self.pos[1] + 5]
                    day = day.strip()
                    if not day.isnumeric():
                        logger.debug(f"Early exit {day}")
                        return
                    logger.debug(f"new day is {day}")
                    self.draw(stdscr, day)
                    logger.debug("Yoou pressed right!")

    def _pad_line(self, stdscr: window, line: str) -> None:
        i = 0
        for c in line:
            if c != " ":
                break
            i += 1
        logger.debug({f"Need to pad {i} times"})
        stdscr.addstr(" " * (i - 1))

    def _add_task(self, date: str, task_desc: str) -> None:
        try:
            datetime.strptime(date, "%Y-%m-%d %H:%M")
        except ValueError as e:
            logger.error(f"Got error parsing date to add: {e}")
            raise SystemExit(2)
        try:
            con = sqlite3.connect(DB_NAME)
            cur = con.cursor()
            cur.execute(f"INSERT INTO {DB_TABLE} values(?, ?)",
                        (date + ":00",
                        task_desc))
            logger.info(f"Added task '{task_desc}', to date {date}.")
        except sqlite3.IntegrityError as e:
            logger.error(f"Task for date {date} already exists: {e}")
        finally:
            cur.close()
            con.commit()
            con.close()

    def _delete_task(self, date: str) -> None:
        try:
            datetime.strptime(date, "%Y-%m-%d %H:%M")
        except ValueError as e:
            logger.error(f"Got error deleting date: {e}")
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute(f"DELETE FROM {DB_TABLE} WHERE date == ?", (date + ":00",))
        if cur.rowcount == 0:
            logger.info(f"No task found for date {date} to delete.")
        else:
            logger.info(f"Task for date {date} deleted.")
        cur.close()
        con.commit()
        con.close()

    def _handle_task(self, args: Namespace) -> None:
        if args.task_command == "add":
            self._add_task(args.date, args.description)
        elif args.task_command == "delete":
            self._delete_task(args.date)

    def handle_args(self, args: Namespace) -> None:
        if args.year:
            mon = self._date.month
            self._date = self._date.replace(year=args.year)
            self._month_calender = self._gen_current_month(args.year, mon)
        if args.month:
            mon = self._date.month
            year = self._date.year
            self._date = self._date.replace(month=months_to_nums[args.month])
            self._month_calender = self._gen_current_month(year, mon)
        if args.day:
            mon = self._date.month
            year = self._date.year
            _, last_day = calendar.monthrange(year, mon)
            logger.debug(f"The last day of the month is {last_day}")
            if args.day > last_day:
                logger.error(f"Invalid day {args.day!r} for month"
                             f" {nums_to_months[mon]}")
                curses.endwin()
                raise SystemExit(2)
            self._date = self._date.replace(day=args.day)
        if args.command:
            if args.command == "task":
                self._handle_task(args)
                curses.endwin()
                SystemExit(0)
