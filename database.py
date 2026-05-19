import sqlite3
from datetime import datetime

DB_PATH = "planner.db"


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                username TEXT,
                text TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                assignee TEXT,
                deadline TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


def save_message(chat_id: int, username: str, text: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (chat_id, username, text) VALUES (?, ?, ?)",
            (chat_id, username, text),
        )
        conn.commit()


def get_recent_messages(chat_id: int, limit: int = 50) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT username, text, created_at FROM messages WHERE chat_id = ? ORDER BY created_at DESC LIMIT ?",
            (chat_id, limit),
        ).fetchall()
    return [{"username": r[0], "text": r[1], "created_at": r[2]} for r in reversed(rows)]


def add_task(chat_id: int, description: str, assignee: str | None, deadline: str | None) -> int:
    with get_conn() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (chat_id, description, assignee, deadline) VALUES (?, ?, ?, ?)",
            (chat_id, description, assignee, deadline),
        )
        conn.commit()
        return cursor.lastrowid


def get_tasks(chat_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, description, assignee, deadline, status FROM tasks WHERE chat_id = ? ORDER BY id",
            (chat_id,),
        ).fetchall()
    return [
        {"id": r[0], "description": r[1], "assignee": r[2], "deadline": r[3], "status": r[4]}
        for r in rows
    ]


def complete_task(task_id: int, chat_id: int) -> bool:
    with get_conn() as conn:
        cursor = conn.execute(
            "UPDATE tasks SET status = 'done' WHERE id = ? AND chat_id = ?",
            (task_id, chat_id),
        )
        conn.commit()
        return cursor.rowcount > 0
