import json
import sqlite3
import subprocess
from pathlib import Path

# --- CONFIG ---
DB_FILE = Path(__file__).resolve().parent / "recetas_dev.db"
OLLAMA_EXEC = "C:/Users/MATEO/AppData/Local/Programs/Ollama/ollama.exe"  # ruta completa si no está en PATH
MODEL = "llama3.2"

CATEGORIAS = [
    "Bizcochos", "Tartas", 
    "Cupcakes", "Donuts", "Galletas", "Brownies", "Helados",
    "Tortitas, crepes y gofres", "Bollería", "Buttercream, ganaches y otros rellenos",
    "Panes", "Masas", "Banana Bread", "Macarons", "Recetas saludables", "Roscones y briox", "Navidad",
    "Costura y crochet", "Otros"
]

# ----------------- DATABASE -----------------
def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def update_recipe(recipe_id, title, folder):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE recipes SET title=?, folder=? WHERE id=?", (title, folder, recipe_id))
    conn.commit()
    conn.close()

# ----------------- OLLAMA -----------------
def ollama_generate(prompt: str) -> str:
    """Llama a Ollama local usando subprocess, devuelve texto generado."""
    result = subprocess.run(
        [OLLAMA_EXEC, "run", MODEL],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=120
    )
    if result.returncode != 0:
        print("❌ Error Ollama:", result.stderr)
        return '{"title":"Receta sin título","folder":"General"}'
    return result.stdout.strip()

def analyze_post(caption: str, author: str):
    prompt = f"""
Eres un asistente que organiza recetas de Instagram en carpetas.

Dada la publicación:

Descripción: {caption}

1. Genera un título breve para la receta. 
2. Asigna la receta a UNA sola categoría de la siguiente lista (elige solo una, sin inventar nuevas):

{", ".join(CATEGORIAS)}

Si no encaja claramente en ninguna, asigna "Otros".

Responde SOLO en formato JSON:
{{"title": "...", "folder": "..."}}
"""
    raw = ollama_generate(prompt)
    try:
        data = json.loads(raw)
        return data.get("title", "Receta sin título"), data.get("folder", "General")
    except Exception:
        return "Receta sin título", "General"

# ----------------- ACTUALIZADOR -----------------
def reassign_folders():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, author, caption FROM recipes")
    recipes = cur.fetchall()
    conn.close()

    total = len(recipes)
    print(f"🟢 Encontradas {total} recetas para procesar...")

    for i, r in enumerate(recipes, 1):
        recipe_id = r["id"]
        author = r["author"]
        caption = r["caption"]
        title, folder = analyze_post(caption, author)
        update_recipe(recipe_id, title, folder)
        print(f"[{i}/{total}] ✅ Actualizado ID {recipe_id}: {title} -> {folder}")

if __name__ == "__main__":
    reassign_folders()
