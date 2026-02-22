import sqlite3
from datetime import datetime

from constants import DB_CONFIG_TABLE
from constants import DB_TASK_TABLE


class TaskRepository:

    def __init__(self, db_path: str):
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def init_db(self) -> None:
        con = self._connect()
        cur = con.cursor()
        try:
            cur.execute(f"CREATE TABLE IF NOT EXISTS {DB_TASK_TABLE} ("
                        " date TEXT UNIQUE NOT NULL, task TEXT NOT NULL)")
            cur.execute(f"CREATE TABLE IF NOT EXISTS {DB_CONFIG_TABLE} ("
                        " id INTEGER PRIMARY KEY CHECK (id = 1),"
                        " bg_color INTEGER,"
                        " task_color INTEGER,"
                        " task_title INTEGER,"
                        " calendar_color INTEGER,"
                        " cursor_color INTEGER)")
            con.commit()
        finally:
            cur.close()
            con.close()

    def load_config(self) -> dict[str, int]:
        conf: dict[str, int] = {}
        query = (f"SELECT * FROM {DB_CONFIG_TABLE} "
                 "WHERE id = 1 "
                 "AND bg_color IS NOT NULL "
                 "AND task_color IS NOT NULL "
                 "AND task_title IS NOT NULL "
                 "AND calendar_color IS NOT NULL "
                 "AND cursor_color IS NOT NULL")
        con = self._connect()
        cur = con.cursor()
        try:
            res = cur.execute(query).fetchone()
            if res:
                columns = ["bg_color", "task_color", "task_title",
                           "calendar_color", "cursor_color"]
                conf = {column: res[i] for i, column in enumerate(columns, start=1)
                        if res[i] is not None}
        finally:
            cur.close()
            con.close()
        return conf

    def save_config(self, updates: dict[str, int]) -> None:
        con = self._connect()
        cur = con.cursor()
        try:
            cur.execute(f"INSERT OR IGNORE INTO {DB_CONFIG_TABLE} "
                        "(id) VALUES (1);")
            if updates:
                set_clause = ", ".join(f"{key} = ?" for key in updates.keys())
                values = list(updates.values())
                query = f"""
                UPDATE {DB_CONFIG_TABLE}
                SET {set_clause}
                WHERE id = 1;
                """
                cur.execute(query, values)
            con.commit()
        finally:
            cur.close()
            con.close()

    def add_task(self, date: str, task_desc: str) -> None:
        con = self._connect()
        cur = con.cursor()
        try:
            cur.execute(f"INSERT INTO {DB_TASK_TABLE} values(?, ?)",
                        (date, task_desc))
            con.commit()
        finally:
            cur.close()
            con.close()

    def delete_task(self, date: str) -> int:
        con = self._connect()
        cur = con.cursor()
        try:
            cur.execute(f"DELETE FROM {DB_TASK_TABLE} WHERE date == ?",
                        (date,))
            con.commit()
            return cur.rowcount
        finally:
            cur.close()
            con.close()

    def tasks_for_day(self, date: datetime) -> list[tuple[str, str]]:
        day_begin = date.strftime("%Y-%m-%d") + " 00:00:00"
        day_end = date.strftime("%Y-%m-%d") + " 23:59:00"
        con = self._connect()
        cur = con.cursor()
        try:
            rows = cur.execute(
                f"SELECT date, task from {DB_TASK_TABLE} "
                "WHERE date > ? AND date < ? ORDER BY date ASC",
                (day_begin, day_end)
            ).fetchall()
            return [(row[0], row[1]) for row in rows]
        finally:
            cur.close()
            con.close()
