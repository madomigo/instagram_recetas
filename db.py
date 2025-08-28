import mysql.connector as mysql
from mysql.connector import Error
from config import settings


_conn = None


def get_conn():
    global _conn
    if _conn and _conn.is_connected():
        return _conn
    _conn = mysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset="utf8mb4"
    )
    return _conn




def fetch_all_recipes():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM recipes ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
    return rows




def fetch_recipe(recipe_id: int):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM recipes WHERE id=%s", (recipe_id,))
    row = cur.fetchone()
    cur.close()
    return row




def upsert_recipe(data: dict):
    """Inserta o actualiza por shortcode."""
    conn = get_conn()
    cur = conn.cursor()
    sql = (
        "INSERT INTO recipes (url, shortcode, author, caption, image_url, posted_at, likes) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s) "
        "ON DUPLICATE KEY UPDATE url=VALUES(url), author=VALUES(author), caption=VALUES(caption), "
        "image_url=VALUES(image_url), posted_at=VALUES(posted_at), likes=VALUES(likes)"
    )
    cur.execute(sql, (
    data.get("url"),
    data.get("shortcode"),
    data.get("author"),
    data.get("caption"),
    data.get("image_url"),
    data.get("posted_at"),
    data.get("likes")
    ))
    conn.commit()
    cur.close()




def delete_recipe(recipe_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM recipes WHERE id=%s", (recipe_id,))
    conn.commit()
    cur.close()