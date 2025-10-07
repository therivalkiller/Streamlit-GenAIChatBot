"""
Database operations for the chatbot
"""
import sqlite3
import datetime
from typing import Dict, Any, List
from models import DEFAULT_MODEL

DB_PATH = "chatbot.db"

def now_iso() -> str:
    """Get current timestamp in ISO format"""
    return datetime.datetime.now().isoformat(sep=" ", timespec="seconds")

def get_db_conn():
    """Create and return a database connection"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initialize database tables and run migrations"""
    conn = get_db_conn()
    cur = conn.cursor()
    
    # Create tables if they don't exist
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            seq INTEGER NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
        """
    )
    
    # Migration: Add model_id columns if they don't exist
    try:
        cur.execute("SELECT model_id FROM sessions LIMIT 1")
    except sqlite3.OperationalError:
        cur.execute(f"ALTER TABLE sessions ADD COLUMN model_id TEXT DEFAULT '{DEFAULT_MODEL}'")
        print("✅ Added model_id column to sessions table")
    
    try:
        cur.execute("SELECT model_id FROM messages LIMIT 1")
    except sqlite3.OperationalError:
        cur.execute(f"ALTER TABLE messages ADD COLUMN model_id TEXT DEFAULT '{DEFAULT_MODEL}'")
        print("✅ Added model_id column to messages table")
    
    conn.commit()
    conn.close()

def create_session_in_db(title: str, model_id: str = None) -> int:
    """Create a new session in the database"""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO sessions (title, created_at, model_id) VALUES (?, ?, ?)", 
                (title, now_iso(), model_id or DEFAULT_MODEL))
    session_id = cur.lastrowid
    conn.commit()
    conn.close()
    return session_id

def delete_session_in_db(session_id: int):
    """Delete a session from the database"""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

def load_sessions_from_db() -> List[Dict[str, Any]]:
    """Load all sessions and their messages from the database"""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, created_at, model_id FROM sessions ORDER BY id DESC")
    rows = cur.fetchall()
    sessions = []
    for r in rows:
        session_id = r["id"]
        cur.execute(
            "SELECT role, content, created_at, seq, model_id FROM messages WHERE session_id = ? ORDER BY seq",
            (session_id,),
        )
        messages = [
            {
                "role": m["role"], 
                "content": m["content"], 
                "created_at": m["created_at"], 
                "seq": m["seq"],
                "model_id": m["model_id"] if m["model_id"] else DEFAULT_MODEL
            }
            for m in cur.fetchall()
        ]
        sessions.append({
            "id": session_id, 
            "title": r["title"], 
            "created_at": r["created_at"], 
            "model_id": r["model_id"] if r["model_id"] else DEFAULT_MODEL,
            "messages": messages
        })
    conn.close()
    return sessions

def save_message_in_db(session_id: int, role: str, content: str, model_id: str = None):
    """Save a message to the database"""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(seq), 0) + 1 AS nextseq FROM messages WHERE session_id = ?", (session_id,))
    row = cur.fetchone()
    nextseq = row["nextseq"] if row is not None else 1
    cur.execute(
        "INSERT INTO messages (session_id, role, content, created_at, seq, model_id) VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, role, content, now_iso(), nextseq, model_id),
    )
    conn.commit()
    conn.close()