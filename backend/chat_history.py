"""
Chat History Storage using SQLite.
Stores sessions and messages so users can revisit past conversations.
"""
import sqlite3
import os
import uuid
from datetime import datetime
from typing import List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "chat_history.db")

def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            active_document TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
    """)
    conn.commit()
    conn.close()
    print("Chat history database initialized.")

def create_session(user_id: str, title: str, active_document: str = "") -> dict:
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    conn = get_db()
    conn.execute(
        "INSERT INTO sessions (id, user_id, title, active_document, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, user_id, title, active_document, now, now)
    )
    conn.commit()
    conn.close()
    return {
        "id": session_id,
        "user_id": user_id,
        "title": title,
        "active_document": active_document,
        "created_at": now,
        "updated_at": now
    }

def get_sessions(user_id: str) -> List[dict]:
    """Get all sessions for a user, ordered by most recent first."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_session(session_id: str) -> Optional[dict]:
    """Get a single session by ID."""
    conn = get_db()
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_session_title(session_id: str, title: str):
    """Update a session's title."""
    conn = get_db()
    conn.execute(
        "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
        (title, datetime.utcnow().isoformat(), session_id)
    )
    conn.commit()
    conn.close()

def update_session_document(session_id: str, active_document: str):
    """Update a session's active document."""
    conn = get_db()
    conn.execute(
        "UPDATE sessions SET active_document = ?, updated_at = ? WHERE id = ?",
        (active_document, datetime.utcnow().isoformat(), session_id)
    )
    conn.commit()
    conn.close()

def touch_session(session_id: str):
    """Update the session's updated_at timestamp."""
    conn = get_db()
    conn.execute(
        "UPDATE sessions SET updated_at = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), session_id)
    )
    conn.commit()
    conn.close()

def delete_session(session_id: str):
    """Delete a session and all its messages."""
    conn = get_db()
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

def add_message(session_id: str, role: str, content: str) -> dict:
    """Add a message to a session."""
    now = datetime.utcnow().isoformat()
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (session_id, role, content, now)
    )
    msg_id = cursor.lastrowid
    # Also update session's updated_at
    conn.execute(
        "UPDATE sessions SET updated_at = ? WHERE id = ?",
        (now, session_id)
    )
    conn.commit()
    conn.close()
    return {"id": msg_id, "session_id": session_id, "role": role, "content": content, "created_at": now}

def get_messages(session_id: str) -> List[dict]:
    """Get all messages for a session, ordered chronologically."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Initialize database on import
init_db()
