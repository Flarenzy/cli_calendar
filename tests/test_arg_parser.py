import pytest

from ArgParser import get_args


def test_get_args_defaults() -> None:
    args = get_args([])

    assert isinstance(args.year, int)
    assert isinstance(args.day, int)
    assert isinstance(args.month, str)
    assert args.command is None


def test_task_add_requires_date() -> None:
    with pytest.raises(SystemExit) as exc:
        get_args(["task", "add", "do thing"])

    assert exc.value.code == 2


def test_task_add_requires_description() -> None:
    with pytest.raises(SystemExit) as exc:
        get_args(["task", "add", "--date", "2025-01-17 12:00"])

    assert exc.value.code == 2


def test_task_add_parses_valid_command() -> None:
    args = get_args([
        "task",
        "add",
        "--date",
        "2025-01-17 12:00",
        "do thing",
    ])

    assert args.command == "task"
    assert args.task_command == "add"
    assert args.date == "2025-01-17 12:00"
    assert args.description == "do thing"


def test_task_delete_requires_date() -> None:
    with pytest.raises(SystemExit) as exc:
        get_args(["task", "delete"])

    assert exc.value.code == 2


def test_task_delete_parses_valid_command() -> None:
    args = get_args(["task", "delete", "--date", "2025-01-17 12:00"])

    assert args.command == "task"
    assert args.task_command == "delete"
    assert args.date == "2025-01-17 12:00"


def test_config_rejects_invalid_color() -> None:
    with pytest.raises(SystemExit) as exc:
        get_args(["config", "--bg-color", "orange"])

    assert exc.value.code == 2


def test_config_accepts_valid_colors() -> None:
    args = get_args([
        "config",
        "--bg-color",
        "black",
        "--cursor-color",
        "red",
        "--task-color",
        "green",
        "--task-title",
        "yellow",
        "--calendar-color",
        "white",
    ])

    assert args.command == "config"
    assert args.bg_color == "black"
    assert args.cursor_color == "red"
    assert args.task_color == "green"
    assert args.task_title == "yellow"
    assert args.calendar_color == "white"
