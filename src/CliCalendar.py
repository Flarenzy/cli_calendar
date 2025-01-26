import calendar
import curses
import logging
import os
import signal
import sqlite3
import sys
from _curses import window
from argparse import Namespace
from collections import ChainMap
from datetime import datetime
from typing import Any
from typing import Optional

from constants import DEFAULT_CONFIG
from constants import DB_NAME
from constants import DB_CONFIG_TABLE
from constants import DB_TASK_TABLE
from dateutil.relativedelta import relativedelta

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

color_to_curses_color_pair = {
    "black": 0,
    "red": 1,
    "green": 2,
    "yellow": 3,
    "blue": 4,
    "magenta": 5,
    "cyan": 6,
    "white": 7
}


class CliCalender():

    def __init__(self):
        self.pos = (0, 0)  # (y, x)
        self.state_matrix = None
        self._text_cal = calendar.TextCalendar()
        self._date = datetime.now()
        self._month_calender = self._gen_current_month(self._date.year,
                                                       self._date.month)
        self._init_db()
        self._config = None
        self._load_config()
        curses.start_color()
        self._init_colors()

    def _load_config(self) -> None:
        if self._config is not None:
            return
        user_config = self._user_config()
        self._config = ChainMap(user_config, DEFAULT_CONFIG)

    def _user_config(self) -> dict[str, int]:
        conf: dict[str, int] = {}
        query = (f"SELECT * FROM {DB_CONFIG_TABLE} "
                 "WHERE id = 1 "
                 "AND bg_color IS NOT NULL "
                 "AND task_color IS NOT NULL "
                 "AND task_title IS NOT NULL "
                 "AND calendar_color IS NOT NULL "
                 "AND cursor_color IS NOT NULL"
                 )
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        try:
            res = cur.execute(query).fetchone()
            if res:
                columns = ["bg_color", "task_color", "task_title",
                           "calendar_color", "cursor_color"]
                conf = {colum: res[i] for i, colum in enumerate(columns)
                        if res[i] is not None}
            else:
                logger.info("No user configuration found in the database.")
        finally:
            cur.close()
            con.close()
        logger.info(f"Loaded configuration: {conf}")
        return conf

    def _init_db(self) -> None:
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute(f"CREATE TABLE IF NOT EXISTS {DB_TASK_TABLE} ("
                    " date TEXT UNIQUE NOT NULL, task TEXT NOT NULL)")
        cur.execute(f"CREATE TABLE IF NOT EXISTS {DB_CONFIG_TABLE} ("
                    " id INTEGER PRIMARY KEY CHECK (id = 1),"
                    " bg_color INTEGER,"
                    " task_color INTEGER,"
                    " task_title INTEGER,"
                    " calendar_color INTEGER,"
                    " cursor_color INTEGER)")
        cur.close()
        con.commit()
        con.close()

    def _gen_current_month(self, year: int = 0, month: int = 0) -> str:
        return self._text_cal.formatmonth(year, month)

    def _draw_tasks(self, win: window) -> None:
        four_spaces = "    "
        win.clear()
        win.addstr(f"\n\n{four_spaces}")
        win.addstr("Tasks:",
                   curses.color_pair(self._config["task_title"]))
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        day_beging = self._date.strftime("%Y-%m-%d") + " 00:00:00"
        day_end = self._date.strftime("%Y-%m-%d") + " 23:59:00"
        for date, task in cur.execute(f"SELECT date, task from {DB_TASK_TABLE}"
                                      " WHERE date > ? "
                                      "AND date < ? ORDER BY date ASC",
                                      (day_beging, day_end)):
            hour = datetime.strptime(date, "%Y-%m-%d %H:%M:%S").time()\
                .strftime("%H:%M")
            logger.debug(f"Printing task: {task} to side window. Hour: {hour}")
            win.addstr(f"\n{four_spaces}")
            win.addstr(f"{hour}: {task}",
                       curses.color_pair(self._config["task_color"]))
        cur.close()
        con.close()

    def _init_colors(self) -> None:
        colors = [
            (curses.COLOR_RED, self._config["bg_color"]),
            (curses.COLOR_GREEN, self._config["bg_color"]),
            (curses.COLOR_YELLOW, self._config["bg_color"]),
            (curses.COLOR_BLUE, self._config["bg_color"]),
            (curses.COLOR_MAGENTA, self._config["bg_color"]),
            (curses.COLOR_CYAN, self._config["bg_color"]),
            (curses.COLOR_WHITE, self._config["bg_color"]),
        ]
        for i, (fg, bg) in enumerate(colors, start=1):
            curses.init_pair(i, fg, bg)

    def draw(self, stdscr: window, day: Optional[str] = None) -> None:
        if day is None:
            day = self._date.strftime("%-d")
        else:
            self._date = self._date.replace(day=int(day))
        stdscr.clear()
        stdscr.addstr("\n\n")
        if len(day) == 1:
            day = " " + day
        four_spaces = "    "
        found = False
        split = self._month_calender.splitlines()
        for i, line in enumerate(split):
            logger.debug(f"Entered loop with index {i}")
            if i == 0:
                line += "    "
            if i == len(split) - 1:
                x = len(split[2]) - len(line)
                line += " " * x
            if day not in line or found or i < 2:
                stdscr.addstr(f"{four_spaces}")
                stdscr.addstr(f"{line}\n",
                              curses.color_pair(self._config["calendar_color"])
                              )
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
                        stdscr.addstr(" ",
                                      curses.color_pair(self._config["calendar"
                                                                     "_color"]
                                                        )
                                      )
                    attrs = curses.color_pair(self._config["cursor_color"]) \
                        | curses.A_STANDOUT
                    stdscr.addstr(f"{c}", attrs)
                    found = True
                    continue
                if j != 0:
                    c = " " + c
                stdscr.addstr(f"{c}",
                              curses.color_pair(self._config["calendar_color"]
                                                )
                              )
            if i == len(split) - 1:
                logger.info("Usli smo aleluja")
                stdscr.addstr(" " * (len(split[2]) - len(split[6])),
                              curses.color_pair(self._config["calendar_color"])
                              )
            stdscr.addstr("\n")
        max_y, max_x = stdscr.getmaxyx()
        win = curses.newwin(max_y,
                            max_x // 4,
                            0,
                            max_x // 4)
        stdscr.refresh()
        self._draw_tasks(win)
        win.refresh()

    def _handle_signal(self, signal_number: int, frame: Any) -> None:
        # clean up any db cons?
        curses.endwin()
        logger.info(f"Exiting on signal: {signal_number}")
        sys.exit(0)

    def _add_date(self, year: int = 0, month: int = 0, day: int = 0) -> None:
        self._date = self._date + relativedelta(years=year,
                                                months=month,
                                                days=day)
        self._month_calender = self._gen_current_month(self._date.year,
                                                       self._date.month)
        logger.info(f"New date is {self._date}")

    def move(self, stdscr: window) -> None:
        temp = self._month_calender.splitlines()
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTSTP, self._handle_signal)
        m = len(temp)
        n = len(temp[2])
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
            case "\x0e":  # This is the asci value for control + n
                logger.debug("Pressed the next page button!")
                self._add_date(month=1)
                self.draw(stdscr, str(self._date.day))
            case "\x10":  # This is the asci value for control + p
                logger.debug("Pressed the prev page button!")
                self._add_date(month=-1)
                self.draw(stdscr, str(self._date.day))

    def _pad_line(self, stdscr: window, line: str) -> None:
        i = 0
        for c in line:
            if c != " ":
                break
            i += 1
        logger.debug({f"Need to pad {i} times"})
        stdscr.addstr(" " * (i - 1),
                      curses.color_pair(self._config["calendar_color"]))

    def _add_task(self, date: str, task_desc: str) -> None:
        try:
            datetime.strptime(date, "%Y-%m-%d %H:%M")
        except ValueError as e:
            logger.error(f"Got error parsing date to add: {e}")
            raise SystemExit(2)
        try:
            con = sqlite3.connect(DB_NAME)
            cur = con.cursor()
            cur.execute(f"INSERT INTO {DB_TASK_TABLE} values(?, ?)",
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
        cur.execute(f"DELETE FROM {DB_TASK_TABLE} WHERE date == ?",
                    (date + ":00",))
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

    def _save_user_config(self, args: Namespace) -> None:
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        updates = []
        values = []
        if args.bg_color:
            updates.append("bg_color = ?")
            values.append(color_to_curses_color_pair[args.bg_color])
        if args.cursor_color:
            updates.append("cursor_color = ?")
            values.append(color_to_curses_color_pair[args.cursor_color])
        if args.task_color:
            updates.append("task_color = ?")
            values.append(color_to_curses_color_pair[args.task_color])
        if args.task_title:
            updates.append("task_title = ?")
            values.append(color_to_curses_color_pair[args.task_title])
        if args.calendar_color:
            updates.append("calendar_color = ?")
            values.append(color_to_curses_color_pair[args.calendar_color])

        try:
            cur.execute(f"INSERT OR IGNORE INTO {DB_CONFIG_TABLE} "
                        "(id) VALUES (1);")
            if updates:
                query = f"""
                UPDATE {DB_CONFIG_TABLE}
                SET {', '.join(updates)}
                WHERE id = 1;
                """
                cur.execute(query, values)
            con.commit()
        finally:
            cur.close()
            con.close()

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
                raise SystemExit(0)
            elif args.command == "config":
                self._save_user_config(args)
                curses.endwin()
                raise SystemExit(0)
