import instaloader
import requests
from io import BytesIO

class ScrapeError(Exception):
    pass

def scrape_instagram_post(url: str) -> dict:
    try:
        L = instaloader.Instaloader()
        shortcode = url.strip("/").split("/")[-1]

        post = instaloader.Post.from_shortcode(L.context, shortcode)

        # Descargar imagen
        image_bytes = None
        if post.url:
            r = requests.get(post.url)
            r.raise_for_status()
            image_bytes = r.content

        # Descargar video
        video_bytes = None
        if post.video_url:
            r = requests.get(post.video_url)
            r.raise_for_status()
            video_bytes = r.content

        data = {
            "url": url,
            "shortcode": shortcode,
            "author": post.owner_username,
            "caption": post.caption or "",
            "image_bytes": image_bytes,
            "video_bytes": video_bytes,
            "posted_at": post.date_utc.isoformat(),
            "likes": post.likes,
        }
        return data

    except Exception as e:
        raise ScrapeError(str(e))
