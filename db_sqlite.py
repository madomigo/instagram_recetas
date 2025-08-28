import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).resolve().parent / "recetas_dev.db"

def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        shortcode TEXT UNIQUE NOT NULL,
        author TEXT,
        caption TEXT,
        image_url TEXT,
        posted_at TEXT,
        likes INTEGER,
        title TEXT,
        folder TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def fetch_all_recipes():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM recipes ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def fetch_recipe(recipe_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM recipes WHERE id=?", (recipe_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def upsert_recipe(data: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO recipes (url, shortcode, author, caption, image_url, posted_at, likes, title, folder)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(shortcode) DO UPDATE SET
        url=excluded.url,
        author=excluded.author,
        caption=excluded.caption,
        image_url=excluded.image_url,
        posted_at=excluded.posted_at,
        likes=excluded.likes,
        title=excluded.title,
        folder=excluded.folder,
        updated_at=CURRENT_TIMESTAMP
    """, (
        data.get("url"),
        data.get("shortcode"),
        data.get("author"),
        data.get("caption"),
        data.get("image_url"),
        data.get("posted_at"),
        data.get("likes"),
        data.get("title"),
        data.get("folder"),
    ))
    conn.commit()
    conn.close()

def delete_recipe(recipe_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM recipes WHERE id=?", (recipe_id,))
    conn.commit()
    conn.close()
