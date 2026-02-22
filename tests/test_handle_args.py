from types import SimpleNamespace
from datetime import datetime

import pytest

from CliCalendar import CliCalender


class FakeCurses:
    COLOR_RED = 1
    COLOR_GREEN = 2
    COLOR_YELLOW = 3
    COLOR_BLUE = 4
    COLOR_MAGENTA = 5
    COLOR_CYAN = 6
    COLOR_WHITE = 7
    A_STANDOUT = 256

    def __init__(self) -> None:
        self.ended = False

    def start_color(self) -> None:
        pass

    def init_pair(self, index: int, fg: int, bg: int) -> None:
        pass

    def color_pair(self, value: int) -> int:
        return value

    def newwin(self, *args, **kwargs):  # pragma: no cover
        raise AssertionError("newwin should not be used in these tests")

    def endwin(self) -> None:
        self.ended = True


def make_calendar(tmp_path, fixed_now: datetime | None = None) -> tuple[CliCalender, FakeCurses]:
    fake_curses = FakeCurses()
    now = fixed_now or datetime(2024, 1, 15, 12, 0, 0)
    cal = CliCalender(
        db_path=str(tmp_path / "handle_args.db"),
        now_fn=lambda: now,
        curses_api=fake_curses,
    )
    return cal, fake_curses


def test_handle_args_month_updates_calendar_month(tmp_path) -> None:
    cal, _ = make_calendar(tmp_path, fixed_now=datetime(2024, 1, 15, 12, 0, 0))

    args = SimpleNamespace(year=None, month="Feb", day=None, command=None)
    cal.handle_args(args)

    assert cal._date.month == 2
    assert "February 2024" in cal._month_calender


def test_handle_args_invalid_day_exits_with_code_2_and_endwin(tmp_path) -> None:
    cal, fake_curses = make_calendar(tmp_path, fixed_now=datetime(2024, 2, 1, 12, 0, 0))

    args = SimpleNamespace(year=None, month=None, day=31, command=None)

    with pytest.raises(SystemExit) as exc:
        cal.handle_args(args)

    assert exc.value.code == 2
    assert fake_curses.ended is True


def test_handle_args_task_add_exits_with_code_0(tmp_path) -> None:
    cal, fake_curses = make_calendar(tmp_path)

    args = SimpleNamespace(
        year=None,
        month=None,
        day=None,
        command="task",
        task_command="add",
        date="2025-01-17 12:00",
        description="meeting",
    )

    with pytest.raises(SystemExit) as exc:
        cal.handle_args(args)

    assert exc.value.code == 0
    assert fake_curses.ended is True


def test_handle_args_task_delete_invalid_date_exits_with_code_2(tmp_path) -> None:
    cal, fake_curses = make_calendar(tmp_path)

    args = SimpleNamespace(
        year=None,
        month=None,
        day=None,
        command="task",
        task_command="delete",
        date="not-a-date",
        description=None,
    )

    with pytest.raises(SystemExit) as exc:
        cal.handle_args(args)

    assert exc.value.code == 2
    # endwin is not called in this path because task processing aborts early.
    assert fake_curses.ended is False


def test_handle_args_config_exits_with_code_0(tmp_path) -> None:
    cal, fake_curses = make_calendar(tmp_path)

    args = SimpleNamespace(
        year=None,
        month=None,
        day=None,
        command="config",
        bg_color="black",
        cursor_color=None,
        task_color=None,
        task_title=None,
        calendar_color=None,
    )

    with pytest.raises(SystemExit) as exc:
        cal.handle_args(args)

    assert exc.value.code == 0
    assert fake_curses.ended is True
