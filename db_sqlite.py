import sqlite3
from pathlib import Path
from typing import List, Dict, Optional

DB_FILE = Path(__file__).resolve().parent / "recetas_dev.db"

def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        shortcode TEXT,
        author TEXT,
        caption TEXT,
        image_url TEXT,
        posted_at TEXT,
        likes INTEGER,
        title TEXT,
        folder TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS folders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )""")
    conn.commit()
    conn.close()

def fetch_all_recipes() -> List[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM recipes ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def fetch_recipe(recipe_id: int) -> Optional[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM recipes WHERE id=?", (recipe_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def upsert_recipe(data: Dict):
    conn = get_conn()
    cur = conn.cursor()
    # try update by url if exists
    cur.execute("SELECT id FROM recipes WHERE url=?", (data.get('url'),))
    row = cur.fetchone()
    if row:
        cur.execute("""UPDATE recipes SET
            shortcode=?, author=?, caption=?, image_url=?, posted_at=?, likes=?, title=?, folder=?
            WHERE id=?
        """, (
            data.get('shortcode'),
            data.get('author'),
            data.get('caption'),
            data.get('image_url'),
            data.get('posted_at'),
            data.get('likes'),
            data.get('title'),
            data.get('folder'),
            row['id']
        ))
    else:
        cur.execute("""INSERT INTO recipes (url, shortcode, author, caption, image_url, posted_at, likes, title, folder)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            data.get('url'),
            data.get('shortcode'),
            data.get('author'),
            data.get('caption'),
            data.get('image_url'),
            data.get('posted_at'),
            data.get('likes'),
            data.get('title'),
            data.get('folder')
        ))
    conn.commit()
    conn.close()

def delete_recipe(recipe_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM recipes WHERE id=?", (recipe_id,))
    conn.commit()
    conn.close()

# Folder helpers
def get_folders() -> List[str]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM folders ORDER BY LOWER(name)")
    rows = [r['name'] for r in cur.fetchall()]
    conn.close()
    return rows

def create_folder(name: str) -> int:
    name = name.strip()
    if not name:
        raise ValueError("Nombre vacío")
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO folders (name) VALUES (?)", (name,))
        conn.commit()
        folder_id = cur.lastrowid
    except sqlite3.IntegrityError:
        cur.execute("SELECT id FROM folders WHERE name=?", (name,))
        row = cur.fetchone()
        folder_id = row['id'] if row else None
    conn.close()
    return folder_id

def delete_folder_by_name(name: str):
    conn = get_conn()
    cur = conn.cursor()
    # unset folder on recipes
    cur.execute("UPDATE recipes SET folder = NULL WHERE folder = ?", (name,))
    # delete folder
    cur.execute("DELETE FROM folders WHERE name = ?", (name,))
    conn.commit()
    conn.close()
