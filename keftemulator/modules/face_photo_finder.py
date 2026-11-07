"""Face Photo Finder - Find person photos on social media"""
import requests
from ..core import Module

class FacePhotoFinder(Module):
    name = "face_finder"
    title = "Face & Photo Finder"
    category = "People Search"
    description = "Find person's photos and face images on social media"
    accepts = ("name", "username", "email")

    def run(self, ent, ctx):
        query = ent.value.strip()
        ctx.log(f"Searching for photos: {query}", "info")
        
        try:
            # Search multiple photo sources
            sources = [
                f"https://www.google.com/search?q={query}&tbm=isch",
                f"https://yandex.com/images/search?text={query}",
                f"https://www.bing.com/images/search?q={query}",
            ]
            
            for source in sources:
                ctx.emit("image",
                    f"🖼️ Search photos: {query}",
                    source, {
                        "query": query,
                        "source": source.split('/')[2],
                        "type": "photo_search"
                    }, rel="photo_search")
                    
        except Exception as e:
            ctx.log(f"Photo finder error: {str(e)[:50]}", "warn")

