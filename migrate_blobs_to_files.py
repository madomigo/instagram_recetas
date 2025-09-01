import sqlite3
from pathlib import Path
from db_sqlite import DB_FILE

UPLOAD_FOLDER = Path("static/uploads")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_FILE)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Crear columnas temporales image_path y video_path en tabla antigua si no existen
try:
    cur.execute("ALTER TABLE recipes ADD COLUMN image_path TEXT")
except sqlite3.OperationalError:
    pass  # ya existe

try:
    cur.execute("ALTER TABLE recipes ADD COLUMN video_path TEXT")
except sqlite3.OperationalError:
    pass  # ya existe

# Guardar BLOBs en archivos y actualizar las nuevas columnas
cur.execute("SELECT * FROM recipes")
rows = cur.fetchall()
for r in rows:
    shortcode = r['shortcode']
    image_blob = r['image']
    video_blob = r['video']

    image_path = f"{shortcode}.jpg" if image_blob else None
    video_path = f"{shortcode}.mp4" if video_blob else None

    if image_blob:
        with open(UPLOAD_FOLDER / image_path, "wb") as f:
            f.write(image_blob)
    if video_blob:
        with open(UPLOAD_FOLDER / video_path, "wb") as f:
            f.write(video_blob)

    cur.execute(
        "UPDATE recipes SET image_path=?, video_path=? WHERE id=?",
        (image_path, video_path, r['id'])
    )

conn.commit()

# Crear tabla nueva limpia sin BLOBs
cur.execute("ALTER TABLE recipes RENAME TO recipes_old")
cur.execute("""
CREATE TABLE recipes (
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

# Copiar datos de la tabla antigua a la nueva
cur.execute("""
INSERT INTO recipes (id, url, shortcode, author, caption, image_path, video_path, posted_at, likes, title, folder)
SELECT id, url, shortcode, author, caption, image_path, video_path, posted_at, likes, title, folder
FROM recipes_old
""")

# Borrar tabla antigua
cur.execute("DROP TABLE recipes_old")
conn.commit()
conn.close()

print("Migración completada ✅. Ahora la tabla 'recipes' está limpia y usa rutas de archivos en lugar de BLOBs.")
