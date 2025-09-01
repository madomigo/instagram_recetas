import sqlite3
from pathlib import Path
from typing import List, Dict, Optional

DB_FILE = Path(__file__).resolve().parent / "recetas_dev.db"
UPLOAD_FOLDER = Path(__file__).resolve().parent / "static/uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True, parents=True)

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
        url TEXT UNIQUE,
        shortcode TEXT,
        author TEXT,
        caption TEXT,
        image_path TEXT,
        video_path TEXT,
        posted_at TEXT,
        likes INTEGER,
        title TEXT,
        folder TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS folders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)
    conn.commit()
    conn.close()

def fetch_recipes_paginated(limit: int, offset: int = 0, folder: Optional[str] = None, query: Optional[str] = None) -> List[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    sql = "SELECT * FROM recipes"
    params = []
    conditions = []

    if folder:
        conditions.append("(folder = ?)")
        params.append(folder)

    if query:
        q = f"%{query.lower()}%"
        conditions.append("(LOWER(title) LIKE ? OR LOWER(author) LIKE ? OR LOWER(caption) LIKE ?)")
        params.extend([q, q, q])

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def count_recipes(folder: Optional[str] = None, query: Optional[str] = None) -> int:
    conn = get_conn()
    cur = conn.cursor()
    sql = "SELECT COUNT(*) FROM recipes"
    params = []
    conditions = []

    if folder:
        conditions.append("(folder = ?)")
        params.append(folder)

    if query:
        q = f"%{query.lower()}%"
        conditions.append("(LOWER(title) LIKE ? OR LOWER(author) LIKE ? OR LOWER(caption) LIKE ?)")
        params.extend([q, q, q])

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    cur.execute(sql, params)
    total = cur.fetchone()[0]
    conn.close()
    return total

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
    cur.execute("SELECT id FROM recipes WHERE url=?", (data.get('url'),))
    row = cur.fetchone()

    if row:
        cur.execute("""
        UPDATE recipes SET shortcode=?, author=?, caption=?, image_path=?, video_path=?, posted_at=?, likes=?, title=?, folder=?
        WHERE id=?
        """, (
            data.get('shortcode'), data.get('author'), data.get('caption'),
            data.get('image_path'), data.get('video_path'), data.get('posted_at'),
            data.get('likes'), data.get('title'), data.get('folder'), row['id']
        ))
    else:
        cur.execute("""
        INSERT INTO recipes (url, shortcode, author, caption, image_path, video_path, posted_at, likes, title, folder)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            data.get('url'), data.get('shortcode'), data.get('author'), data.get('caption'),
            data.get('image_path'), data.get('video_path'), data.get('posted_at'),
            data.get('likes'), data.get('title'), data.get('folder')
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

def update_recipe_folder(recipe_id: int, folder: str):
    """Actualiza la carpeta de una receta específica."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE recipes SET folder=? WHERE id=?", (folder, recipe_id))
    conn.commit()
    conn.close()

def delete_folder_by_name(name: str):
    """
    Al eliminar una carpeta, mover todos los posts a "Otros" en vez de NULL.
    """
    conn = get_conn()
    cur = conn.cursor()
    # Asegurarnos de que la carpeta "Otros" existe
    cur.execute("INSERT OR IGNORE INTO folders (name) VALUES ('Otros')")
    # Mover recetas a "Otros"
    cur.execute("UPDATE recipes SET folder='Otros' WHERE folder=?", (name,))
    # Eliminar la carpeta
    cur.execute("DELETE FROM folders WHERE name=?", (name,))
    conn.commit()
    conn.close()

def sync_folders():
    """
    Asegura que todos los valores distintos de recipes.folder
    existan en la tabla folders.
    """
    conn = get_conn()
    cur = conn.cursor()

    # 1. obtener todas las carpetas distintas usadas en recetas
    cur.execute("SELECT DISTINCT folder FROM recipes WHERE folder IS NOT NULL AND TRIM(folder) != ''")
    recipe_folders = {r['folder'].strip() for r in cur.fetchall()}

    # 2. obtener las carpetas que ya existen en folders
    cur.execute("SELECT name FROM folders")
    existing_folders = {r['name'].strip() for r in cur.fetchall()}

    # 3. calcular las que faltan
    missing = recipe_folders - existing_folders

    # 4. insertar las que falten
    for name in sorted(missing):
        try:
            cur.execute("INSERT INTO folders (name) VALUES (?)", (name,))
            print(f"🟢 Añadida carpeta faltante: {name}")
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()
    print("✅ Sincronización completada")

if __name__ == "__main__":
    init_db()
    sync_folders()