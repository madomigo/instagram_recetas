import json
import lzma
import sqlite3
import subprocess
from pathlib import Path

# --- CONFIG ---
DB_FILE = Path(__file__).resolve().parent / "recetas_dev.db"
SAVED_DIR = Path("D:/")  # Ajusta según tu carpeta
OLLAMA_EXEC = "C:/Users/MATEO/AppData/Local/Programs/Ollama/ollama.exe"  # Si no está en PATH, pon la ruta completa, ej: "C:/Users/MATEO/AppData/Local/Programs/Ollama/ollama.exe"

# ----------------- DATABASE -----------------
def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def upsert_recipe(data: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM recipes WHERE url=?", (data.get("url"),))
    row = cur.fetchone()
    if row:
        cur.execute(
            """UPDATE recipes SET
                shortcode=?, author=?, caption=?, image=?, video=?, posted_at=?,
                likes=?, title=?, folder=?
                WHERE id=?
            """,
            (
                data.get("shortcode"),
                data.get("author"),
                data.get("caption"),
                data.get("image"),
                data.get("video"),
                data.get("posted_at"),
                data.get("likes"),
                data.get("title"),
                data.get("folder"),
                row["id"],
            ),
        )
    else:
        cur.execute(
            """INSERT INTO recipes
            (url, shortcode, author, caption, image, video, posted_at, likes, title, folder)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (
                data.get("url"),
                data.get("shortcode"),
                data.get("author"),
                data.get("caption"),
                data.get("image"),
                data.get("video"),
                data.get("posted_at"),
                data.get("likes"),
                data.get("title"),
                data.get("folder"),
            ),
        )
    conn.commit()
    conn.close()

def create_folder(name: str):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO folders (name) VALUES (?)", (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

# ----------------- OLLAMA -----------------
def ollama_generate(prompt: str, model: str = "llama3.2") -> str:
    """Llama a Ollama local usando subprocess, devuelve texto generado."""
    result = subprocess.run(
        [OLLAMA_EXEC, "run", model],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=120
    )
    if result.returncode != 0:
        print("❌ Error Ollama:", result.stderr)
        return "Receta sin título"
    return result.stdout.strip()

CATEGORIAS = [
  "Bizcochos", "Tartas", "Tartas de queso", "Tartas de frutas",
  "Cupcakes", "Donuts", "Galletas", "Brownies",
  "Waffles y gofres", "Crepes y tortitas", "Pasteles", "Bollería",
  "Helados",
  "Panes", "Pizza", "Masas",
  "Otros"
]

def analyze_post(caption: str, author: str):
    prompt = f"""
Eres un asistente que organiza recetas de Instagram en carpetas.

Dada la publicación:

Autor: {author}
Descripción: {caption}

1. Genera un título breve y atractivo para la receta (máx. 7 palabras).
2. Asigna la receta a UNA sola categoría de la siguiente lista (elige solo una, sin inventar nuevas):

{", ".join(CATEGORIAS)}

Si no encaja claramente en ninguna, asigna "Otros".

Responde SOLO en formato JSON:
{{"title": "...", "folder": "..."}}.
"""
    raw = ollama_generate(prompt)
    try:
        data = json.loads(raw)
        return data.get("title", "Receta sin título"), data.get("folder", "General")
    except Exception:
        return "Receta sin título", "General"

# ----------------- IMPORTER -----------------
def import_saved():
    cnt = 0
    for json_file in SAVED_DIR.glob("*.json.xz"):
        with lzma.open(json_file, "rt", encoding="utf-8") as f:
            post = json.load(f)

        cnt += 1
        if(cnt == 100):
            return
        shortcode = post.get("node", {}).get("shortcode")
        url = f"https://www.instagram.com/p/{shortcode}/"
        author = post.get("node", {}).get("owner", {}).get("username", "desconocido")
        caption_edges = post.get("node", {}).get("edge_media_to_caption", {}).get("edges", [])
        caption = caption_edges[0]["node"]["text"] if caption_edges else ""
        posted_at = post.get("node", {}).get("taken_at_timestamp")
        likes = post.get("node", {}).get("edge_liked_by", {}).get("count", 0)

        # Leer multimedia en binario
        image = None
        video = None
        base_path = json_file.with_suffix("")  # quita .xz
        jpg_file = base_path.with_suffix(".jpg")
        mp4_file = base_path.with_suffix(".mp4")

        if jpg_file.exists():
            image = jpg_file.read_bytes()
        if mp4_file.exists():
            video = mp4_file.read_bytes()

        # Analizar con Ollama
        title, folder = analyze_post(caption, author)
        create_folder(folder)

        recipe = {
            "url": url,
            "shortcode": shortcode,
            "author": author,
            "caption": caption,
            "image": image,
            "video": video,
            "posted_at": posted_at,
            "likes": likes,
            "title": title,
            "folder": folder,
        }
        upsert_recipe(recipe)
        print(f"✅ Guardado {cnt}: {title} en carpeta {folder}")

if __name__ == "__main__":
    import_saved()
