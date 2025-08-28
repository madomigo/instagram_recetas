import instaloader

class ScrapeError(Exception):
    pass

def scrape_instagram_post(url: str) -> dict:
    try:
        L = instaloader.Instaloader()
        shortcode = url.strip("/").split("/")[-1]

        post = instaloader.Post.from_shortcode(L.context, shortcode)

        data = {
            "url": url,
            "shortcode": shortcode,
            "author": post.owner_username,
            "caption": post.caption or "",
            "image_url": post.url,
            "posted_at": post.date_utc.isoformat(),
            "likes": post.likes,
        }
        return data

    except Exception as e:
        raise ScrapeError(str(e))
