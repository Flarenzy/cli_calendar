import sqlite3
from datetime import datetime

import pytest

from TaskRepository import TaskRepository
from constants import DB_CONFIG_TABLE
from constants import DB_TASK_TABLE


def make_repo(tmp_path) -> tuple[TaskRepository, str]:
    db_path = tmp_path / "test_cli_calender.db"
    repo = TaskRepository(str(db_path))
    repo.init_db()
    return repo, str(db_path)


def test_init_db_creates_tables(tmp_path) -> None:
    repo, db_path = make_repo(tmp_path)

    con = sqlite3.connect(db_path)
    cur = con.cursor()
    try:
        rows = cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    finally:
        cur.close()
        con.close()

    names = {row[0] for row in rows}
    assert DB_TASK_TABLE in names
    assert DB_CONFIG_TABLE in names


def test_add_task_and_tasks_for_day_are_ordered(tmp_path) -> None:
    repo, _ = make_repo(tmp_path)

    repo.add_task("2025-01-17 12:00:00", "Lunch")
    repo.add_task("2025-01-17 09:00:00", "Standup")
    repo.add_task("2025-01-18 08:00:00", "Other day")

    tasks = repo.tasks_for_day(datetime(2025, 1, 17, 0, 0, 0))

    assert tasks == [
        ("2025-01-17 09:00:00", "Standup"),
        ("2025-01-17 12:00:00", "Lunch"),
    ]


def test_add_task_duplicate_date_raises_integrity_error(tmp_path) -> None:
    repo, _ = make_repo(tmp_path)

    repo.add_task("2025-01-17 12:00:00", "Lunch")
    with pytest.raises(sqlite3.IntegrityError):
        repo.add_task("2025-01-17 12:00:00", "Conflict")


def test_delete_task_returns_rowcount(tmp_path) -> None:
    repo, _ = make_repo(tmp_path)

    repo.add_task("2025-01-17 12:00:00", "Lunch")

    assert repo.delete_task("2025-01-17 12:00:00") == 1
    assert repo.delete_task("2025-01-17 12:00:00") == 0


def test_save_and_load_config_roundtrip(tmp_path) -> None:
    repo, _ = make_repo(tmp_path)

    repo.save_config({
        "bg_color": 0,
        "task_color": 1,
        "task_title": 3,
        "calendar_color": 0,
        "cursor_color": 2,
    })

    conf = repo.load_config()

    assert conf == {
        "bg_color": 0,
        "task_color": 1,
        "task_title": 3,
        "calendar_color": 0,
        "cursor_color": 2,
    }


def test_load_config_empty_when_not_all_fields_populated(tmp_path) -> None:
    repo, _ = make_repo(tmp_path)

    repo.save_config({"bg_color": 4})

    assert repo.load_config() == {}
