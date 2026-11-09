
import sqlite3
import json
from datetime import datetime

DB_NAME = "local_bot.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    with get_connection() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                messages TEXT NOT NULL DEFAULT '[]',
                created_at TEXT,
                updated_at TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL UNIQUE,
                created_at TEXT
            )
        """)


def create_chat():
    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO chats (title, messages, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, ("New Chat", "[]", now, now))

        return cursor.lastrowid


def get_all_chats():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM chats
            ORDER BY updated_at DESC
        """).fetchall()

        return [dict(row) for row in rows]


def get_chat(chat_id):
    with get_connection() as conn:
        row = conn.execute("""
            SELECT * FROM chats WHERE id = ?
        """, (chat_id,)).fetchone()

        if row:
            chat = dict(row)
            chat["messages"] = json.loads(chat["messages"])
            return chat

        return None


def save_chat(chat_id, messages, title=None):
    now = datetime.now().isoformat(timespec="seconds")
    messages_json = json.dumps(messages, ensure_ascii=False)

    with get_connection() as conn:

        if title is not None:
            conn.execute("""
                UPDATE chats
                SET messages = ?, title = ?, updated_at = ?
                WHERE id = ?
            """, (messages_json, title, now, chat_id))

        else:
            conn.execute("""
                UPDATE chats
                SET messages = ?, updated_at = ?
                WHERE id = ?
            """, (messages_json, now, chat_id))


def delete_chat(chat_id):
    with get_connection() as conn:
        conn.execute("""
            DELETE FROM chats WHERE id = ?
        """, (chat_id,))


# -----------------------------
# MEMORY DATABASE
# -----------------------------

def add_memory(content):
    content = content.strip()

    if not content:
        return

    with get_connection() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO memories
            (content, created_at)
            VALUES (?, ?)
        """, (
            content,
            datetime.now().isoformat(timespec="seconds")
        ))


def get_all_memories():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM memories
            ORDER BY id DESC
        """).fetchall()

        return [dict(row) for row in rows]


def delete_memory(memory_id):
    with get_connection() as conn:
        conn.execute("""
            DELETE FROM memories WHERE id = ?
        """, (memory_id,))


def clear_memories():
    with get_connection() as conn:
        conn.execute("DELETE FROM memories")
