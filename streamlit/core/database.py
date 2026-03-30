import sqlite3
from datetime import datetime

from config import DB_PATH


def get_db():
    return sqlite3.connect(str(DB_PATH))


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT DEFAULT '新对话',
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            role TEXT,
            content TEXT,
            response_time REAL,
            conversation_id TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            message_id INTEGER,
            rating INTEGER,
            feedback TEXT,
            FOREIGN KEY(message_id) REFERENCES chat_history(id)
        )
    ''')
    conn.commit()
    conn.close()


def create_conversation(conv_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    c = conn.cursor()
    c.execute(
        'INSERT OR IGNORE INTO conversations (id, title, created_at, updated_at) VALUES (?,?,?,?)',
        (conv_id, "新对话", now, now),
    )
    conn.commit()
    conn.close()


def update_conversation_title(conv_id, title):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        'UPDATE conversations SET title=?, updated_at=? WHERE id=?',
        (title, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), conv_id),
    )
    conn.commit()
    conn.close()


def delete_conversation(conv_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM chat_history WHERE conversation_id=?', (conv_id,))
    c.execute('DELETE FROM conversations WHERE id=?', (conv_id,))
    conn.commit()
    conn.close()


def get_conversations():
    """返回 [(id, title, updated_at), ...] 按更新时间倒序"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, title, updated_at FROM conversations ORDER BY updated_at DESC')
    rows = c.fetchall()
    conn.close()
    if not rows:
        conn2 = get_db()
        c2 = conn2.cursor()
        c2.execute('''
            SELECT DISTINCT conversation_id FROM chat_history
            WHERE conversation_id IS NOT NULL ORDER BY timestamp DESC
        ''')
        legacy = c2.fetchall()
        conn2.close()
        for (cid,) in legacy:
            create_conversation(cid)
        if legacy:
            return get_conversations()
    return rows


def save_chat(role, content, response_time=None, conversation_id=None):
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        'INSERT INTO chat_history (timestamp, role, content, response_time, conversation_id) VALUES (?,?,?,?,?)',
        (now, role, content, response_time, conversation_id),
    )
    last_id = c.lastrowid
    if conversation_id:
        c.execute('UPDATE conversations SET updated_at=? WHERE id=?', (now, conversation_id))
    conn.commit()
    conn.close()
    return last_id


def save_feedback(message_id, rating, feedback=None):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        'INSERT INTO user_feedback (timestamp, message_id, rating, feedback) VALUES (?,?,?,?)',
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message_id, rating, feedback),
    )
    conn.commit()
    conn.close()


def load_chat_history(limit=50, conversation_id=None):
    conn = get_db()
    c = conn.cursor()
    if conversation_id:
        c.execute('''
            SELECT id, timestamp, role, content, response_time
            FROM chat_history WHERE conversation_id=? ORDER BY timestamp ASC LIMIT ?
        ''', (conversation_id, limit))
    else:
        c.execute('''
            SELECT id, timestamp, role, content, response_time
            FROM chat_history ORDER BY timestamp DESC LIMIT ?
        ''', (limit,))
    history = c.fetchall()
    conn.close()
    return history
