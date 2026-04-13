import sqlite3, json
from pathlib import Path

DB = Path("jarvis.db")

def init_db():
    con = sqlite3.connect(DB)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY,
            role TEXT,
            content TEXT,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
        USING fts5(content, content='memories', content_rowid='id');
    """)
    con.commit(); con.close()

def save(role: str, content: str):
    con = sqlite3.connect(DB)
    con.execute("INSERT INTO memories(role,content) VALUES(?,?)", (role, content))
    con.commit(); con.close()

def search(query: str, limit=8):
    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT role,content FROM memories_fts WHERE memories_fts MATCH ? LIMIT ?",
        (query, limit)
    ).fetchall()
    con.close()
    return [{"role": r, "content": c} for r, c in rows]

def recent(limit=10):
    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT role,content FROM memories ORDER BY ts DESC LIMIT ?", (limit,)
    ).fetchall()
    con.close()
    return [{"role": r, "content": c} for r, c in reversed(rows)]