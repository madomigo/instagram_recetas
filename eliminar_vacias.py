import sqlite3
from pathlib import Path

# --- CONFIG ---
DB_FILE = Path(__file__).resolve().parent / "recetas_dev.db"

def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def delete_empty_folders():
    conn = get_conn()
    cur = conn.cursor()

    # Encuentra carpetas sin recetas
    cur.execute("""
        SELECT f.id, f.name
        FROM folders f
        LEFT JOIN recipes r ON f.name = r.folder
        WHERE r.id IS NULL
    """)
    empty_folders = cur.fetchall()

    if not empty_folders:
        print("✅ No hay carpetas vacías.")
        conn.close()
        return

    print(f"🗑 Se encontraron {len(empty_folders)} carpetas vacías.")
    for f in empty_folders:
        print(f"   - {f['name']}")
        cur.execute("DELETE FROM folders WHERE id=?", (f["id"],))

    conn.commit()
    conn.close()
    print("✅ Carpetas vacías eliminadas correctamente.")

if __name__ == "__main__":
    delete_empty_folders()
