from datetime import datetime

from CliCalendar import CliCalender


class FakeWindow:
    def __init__(self) -> None:
        self.calls: list[tuple[tuple, dict]] = []

    def clear(self) -> None:
        self.calls.append((("clear",), {}))

    def addstr(self, *args, **kwargs) -> None:
        self.calls.append((args, kwargs))

    def refresh(self) -> None:
        self.calls.append((("refresh",), {}))


class FakeStdScr:
    def __init__(self, key: str | None = None) -> None:
        self._key = key
        self.calls: list[tuple[tuple, dict]] = []

    def set_key(self, key: str) -> None:
        self._key = key

    def clear(self) -> None:
        self.calls.append((("clear",), {}))

    def addstr(self, *args, **kwargs) -> None:
        self.calls.append((args, kwargs))

    def refresh(self) -> None:
        self.calls.append((("refresh",), {}))

    def getmaxyx(self) -> tuple[int, int]:
        return (30, 120)

    def getkey(self) -> str:
        assert self._key is not None
        return self._key


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
        self.created_windows: list[FakeWindow] = []

    def start_color(self) -> None:
        self.started = True

    def init_pair(self, index: int, fg: int, bg: int) -> None:
        self.pairs.append((index, fg, bg))

    def color_pair(self, value: int) -> int:
        return value

    def newwin(self, *_args, **_kwargs) -> FakeWindow:
        win = FakeWindow()
        self.created_windows.append(win)
        return win

    def endwin(self) -> None:
        pass


def make_calendar(tmp_path) -> tuple[CliCalender, FakeCurses]:
    fake_curses = FakeCurses()
    cal = CliCalender(
        db_path=str(tmp_path / "move.db"),
        now_fn=lambda: datetime(2024, 1, 15, 12, 0, 0),
        curses_api=fake_curses,
    )
    return cal, fake_curses


def test_draw_sets_position_and_renders_task_panel(tmp_path) -> None:
    cal, fake_curses = make_calendar(tmp_path)
    stdscr = FakeStdScr()

    cal.draw(stdscr)

    assert cal.pos != (0, 0)
    assert len(fake_curses.created_windows) == 1
    window_text = [call[0][0] for call in fake_curses.created_windows[0].calls if call[0] and isinstance(call[0][0], str)]
    assert any("Tasks:" in text for text in window_text)


def test_move_right_triggers_draw_with_next_day(tmp_path, monkeypatch) -> None:
    cal, _ = make_calendar(tmp_path)
    stdscr = FakeStdScr()
    cal.draw(stdscr)

    called: list[str] = []

    def fake_draw(_stdscr, day=None):
        called.append(day)

    monkeypatch.setattr(cal, "draw", fake_draw)
    monkeypatch.setattr("CliCalendar.signal.signal", lambda *_args, **_kwargs: None)

    stdscr.set_key("KEY_RIGHT")
    cal.move(stdscr)

    assert called == ["16"]


def test_move_right_on_weekday_header_cell_returns_early(tmp_path, monkeypatch) -> None:
    cal, _ = make_calendar(tmp_path)
    stdscr = FakeStdScr(key="KEY_RIGHT")
    # Use last-week row where slicing to the right yields empty string.
    cal.pos = (6, 6)

    draw_called = {"value": False}

    def fake_draw(_stdscr, day=None):
        draw_called["value"] = True

    monkeypatch.setattr(cal, "draw", fake_draw)
    monkeypatch.setattr("CliCalendar.signal.signal", lambda *_args, **_kwargs: None)

    cal.move(stdscr)

    assert draw_called["value"] is False


def test_move_ctrl_n_advances_month_and_draws_same_day(tmp_path, monkeypatch) -> None:
    cal, _ = make_calendar(tmp_path)
    stdscr = FakeStdScr(key="\x0e")
    day_before = cal._date.day

    called: list[str] = []

    def fake_draw(_stdscr, day=None):
        called.append(day)

    monkeypatch.setattr(cal, "draw", fake_draw)
    monkeypatch.setattr("CliCalendar.signal.signal", lambda *_args, **_kwargs: None)

    cal.move(stdscr)

    assert cal._date.month == 2
    assert called == [str(day_before)]


def test_move_ctrl_p_moves_to_previous_month(tmp_path, monkeypatch) -> None:
    cal, _ = make_calendar(tmp_path)
    stdscr = FakeStdScr(key="\x10")

    called: list[str] = []

    def fake_draw(_stdscr, day=None):
        called.append(day)

    monkeypatch.setattr(cal, "draw", fake_draw)
    monkeypatch.setattr("CliCalendar.signal.signal", lambda *_args, **_kwargs: None)

    cal.move(stdscr)

    assert cal._date.month == 12
    assert cal._date.year == 2023
    assert called == ["15"]
