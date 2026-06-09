"""SQLite 数据库初始化 — 知识库、文档、Skills、设置 四表"""

import sqlite3
import os
import threading

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DB_PATH = os.path.join(DATA_DIR, 'distiller.db')

_local = threading.local()

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at  TEXT DEFAULT (datetime('now','localtime')),
    updated_at  TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kb_id       INTEGER NOT NULL,
    title       TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_path TEXT DEFAULT NULL,
    chunk_count INTEGER DEFAULT 0,
    created_at  TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id)
);

CREATE TABLE IF NOT EXISTS chunks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id      INTEGER NOT NULL,
    kb_id       INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content     TEXT NOT NULL,
    FOREIGN KEY (doc_id) REFERENCES documents(id),
    FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id)
);

CREATE TABLE IF NOT EXISTS skills (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    type          TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    description   TEXT DEFAULT '',
    is_default    INTEGER DEFAULT 0,
    created_at    TEXT DEFAULT (datetime('now','localtime')),
    updated_at    TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS settings (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now','localtime'))
);

INSERT OR IGNORE INTO knowledge_bases (id, name, description) VALUES (1, '默认知识库', '初始知识库，可以重命名或删除');
"""


def get_connection():
    if not hasattr(_local, 'conn') or _local.conn is None:
        os.makedirs(DATA_DIR, exist_ok=True)
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = get_connection()
    with conn:
        conn.executescript(SCHEMA_SQL)


def dict_from_row(row):
    if row is None:
        return None
    return dict(row)
