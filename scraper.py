import instaloader
import requests
from pathlib import Path
from db_sqlite import UPLOAD_FOLDER

class ScrapeError(Exception): pass

def scrape_instagram_post(url: str) -> dict:
    """
    Devuelve un dict con keys:
      - shortcode, author, caption, posted_at (ISO), likes
      - image_bytes (bytes) si tiene imagen
      - video_bytes (bytes) si tiene vídeo

    Ya NO escribe ficheros en disco; la escritura la hace la app principal.
    """
    try:
        L = instaloader.Instaloader()
        shortcode = url.strip("/").split("/")[-1]
        # Instaloader necesita el shortcode sin parámetros
        if '?' in shortcode:
            shortcode = shortcode.split('?')[0]

        post = instaloader.Post.from_shortcode(L.context, shortcode)

        image_bytes = None
        video_bytes = None

        # post.url y post.video_url pueden ser None; usamos requests para obtener bytes
        # Nota: puede fallar si Instagram cambia su API o requiere sesión.
        if getattr(post, 'url', None):
            r = requests.get(post.url, timeout=15)
            r.raise_for_status()
            image_bytes = r.content

        if getattr(post, 'video_url', None):
            r = requests.get(post.video_url, timeout=15)
            r.raise_for_status()
            video_bytes = r.content

        return {
            "url": url,
            "shortcode": shortcode,
            "author": post.owner_username,
            "caption": post.caption or "",
            "image_bytes": image_bytes,
            "video_bytes": video_bytes,
            "posted_at": post.date_utc.isoformat() if getattr(post, 'date_utc', None) else None,
            "likes": getattr(post, 'likes', None)
        }

    except Exception as e:
        raise ScrapeError(str(e))
