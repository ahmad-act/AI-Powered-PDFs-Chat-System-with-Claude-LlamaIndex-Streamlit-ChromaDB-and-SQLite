# storage.py

import sqlite3
from datetime import datetime
from config import SQLITE_CHAT_HISTORY_DB_PATH
from logging_config import setup_logger

logger = setup_logger(__name__)
DB_PATH = SQLITE_CHAT_HISTORY_DB_PATH

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Enable foreign key support
        c.execute("PRAGMA foreign_keys = ON")

        # Create chat_history table without 'title'
        c.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                session_id TEXT,
                timestamp TEXT,
                role TEXT,
                message TEXT
            )
        ''')

        # Create metadata table
        c.execute('''
            CREATE TABLE IF NOT EXISTS chat_history_metadata (
                session_id TEXT PRIMARY KEY,
                title TEXT DEFAULT NULL,
                FOREIGN KEY (session_id) REFERENCES chat_history(session_id) ON DELETE CASCADE
            )
        ''')

        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize DB: {e}")
    finally:
        conn.close()


def save_message(session_id, role, message, title=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Insert into chat_history
        c.execute(
            "INSERT INTO chat_history (session_id, timestamp, role, message) VALUES (?, ?, ?, ?)",
            (session_id, datetime.utcnow().isoformat(), role, message)
        )

        # Insert into chat_history_metadata if session_id does not exist
        c.execute(
            "INSERT OR IGNORE INTO chat_history_metadata (session_id, title) VALUES (?, ?)",
            (session_id, title)
        )

        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to save message for session {session_id}: {e}")
    finally:
        conn.close()


def load_history(session_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT role, message FROM chat_history WHERE session_id = ?", (session_id,))
        history = c.fetchall()
        return history
    except sqlite3.Error as e:
        logger.error(f"Failed to load history for session {session_id}: {e}")
        return []
    finally:
        conn.close()

def delete_history(session_id=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if session_id:
            c.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
        else:
            c.execute("DELETE FROM chat_history")
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to delete history{' for session ' + session_id if session_id else ''}: {e}")
    finally:
        conn.close()

def get_all_history(limit=10, offset=0):
    """
    Returns limited chat messages from all sessions ordered by timestamp.
    Each item is a tuple: (session_id, timestamp, role, message)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            SELECT session_id, timestamp, role, message 
            FROM chat_history 
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        history = c.fetchall()
        return history
    except sqlite3.Error as e:
        logger.error(f"Failed to get paginated chat history: {e}")
        return []
    finally:
        conn.close()


def get_recent_session_titles(limit=10, offset=0):
    """
    Fetch recent session titles ordered by latest timestamp in chat_history.
    Returns a list of tuples: (session_id, title)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            SELECT m.session_id, m.title
            FROM chat_history_metadata m
            JOIN (
                SELECT session_id, MAX(timestamp) as latest
                FROM chat_history
                GROUP BY session_id
            ) h ON m.session_id = h.session_id
            ORDER BY h.latest DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        return c.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch recent session titles: {e}")
        return []
    finally:
        conn.close()
