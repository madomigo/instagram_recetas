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
        image BLOB,
        video BLOB,
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
    rows = []
    for r in cur.fetchall():
        row = dict(r)
        # Convertir BLOB a base64 para mostrar en HTML
        if row['image']:
            import base64
            row['image'] = base64.b64encode(row['image']).decode('utf-8')
        if row['video']:
            import base64
            row['video'] = base64.b64encode(row['video']).decode('utf-8')
        rows.append(row)
    conn.close()
    return rows

def fetch_recipe(recipe_id: int) -> Optional[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM recipes WHERE id=?", (recipe_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    row = dict(row)
    import base64
    if row['image']:
        row['image'] = base64.b64encode(row['image']).decode('utf-8')
    if row['video']:
        row['video'] = base64.b64encode(row['video']).decode('utf-8')
    return row

def upsert_recipe(data: Dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM recipes WHERE url=?", (data.get('url'),))
    row = cur.fetchone()
    image_bytes = data.get('image_bytes')
    video_bytes = data.get('video_bytes')
    if row:
        cur.execute("""UPDATE recipes SET
            shortcode=?, author=?, caption=?, image=?, video=?,
            posted_at=?, likes=?, title=?, folder=?
            WHERE id=?
        """, (
            data.get('shortcode'),
            data.get('author'),
            data.get('caption'),
            image_bytes,
            video_bytes,
            data.get('posted_at'),
            data.get('likes'),
            data.get('title'),
            data.get('folder'),
            row['id']
        ))
    else:
        cur.execute("""INSERT INTO recipes (url, shortcode, author, caption, image, video, posted_at, likes, title, folder)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            data.get('url'),
            data.get('shortcode'),
            data.get('author'),
            data.get('caption'),
            image_bytes,
            video_bytes,
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
    cur.execute("UPDATE recipes SET folder = NULL WHERE folder = ?", (name,))
    cur.execute("DELETE FROM folders WHERE name = ?", (name,))
    conn.commit()
    conn.close()
