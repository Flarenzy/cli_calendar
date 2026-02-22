from datetime import datetime

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
        self.started = False
        self.pairs: list[tuple[int, int, int]] = []
        self.ended = False

    def start_color(self) -> None:
        self.started = True

    def init_pair(self, index: int, fg: int, bg: int) -> None:
        self.pairs.append((index, fg, bg))

    def color_pair(self, value: int) -> int:
        return value

    def newwin(self, *args, **kwargs):  # pragma: no cover - not needed here
        raise AssertionError("newwin should not be called during constructor")

    def endwin(self) -> None:
        self.ended = True


def test_constructor_supports_dependency_injection(tmp_path) -> None:
    fake_curses = FakeCurses()
    fixed_now = datetime(2024, 2, 29, 10, 30, 0)
    db_path = tmp_path / "calendar_test.db"

    cal = CliCalender(
        db_path=str(db_path),
        now_fn=lambda: fixed_now,
        curses_api=fake_curses,
    )

    assert cal._date == fixed_now
    assert cal._date.year == 2024
    assert cal._date.month == 2
    assert db_path.exists()
    assert fake_curses.started is True
    assert len(fake_curses.pairs) == 7


def test_constructor_uses_default_config_values_when_db_empty(tmp_path) -> None:
    fake_curses = FakeCurses()
    cal = CliCalender(
        db_path=str(tmp_path / "calendar_test.db"),
        curses_api=fake_curses,
    )

    assert cal._config["bg_color"] == 0
    assert cal._config["cursor_color"] == 1
    assert cal._config["task_color"] == 1
    assert cal._config["task_title"] == 3
    assert cal._config["calendar_color"] == 0
