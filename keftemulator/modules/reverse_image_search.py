"""Reverse image search - Find where an image appears online"""
import requests
from urllib.parse import quote
from ..core import Module

class ReverseImageSearch(Module):
    name = "reverse_image_search"
    title = "Reverse Image Search"
    category = "Image Analysis"
    description = "Find where an image appears online using Google, TinEye, and Yandex reverse search"
    accepts = ("url", "image_url")

    def run(self, ent, ctx):
        url = ent.value.strip()

        if not url.startswith("http"):
            return

        ctx.log(f"reverse image search: {url}", "info")

        # Google Reverse Image Search
        google_url = f"https://www.google.com/searchbyimage?image_url={quote(url)}"

        # TinEye Reverse Image Search
        tineye_url = f"https://tineye.com/search?url={quote(url)}"

        # Yandex Reverse Image Search
        yandex_url = f"https://yandex.com/images/search?rpt=imageview&url={quote(url)}"

        # Emit reverse search links
        data = {
            "image_url": url,
            "google_url": google_url,
            "tineye_url": tineye_url,
            "yandex_url": yandex_url,
            "source": "reverse_image_search"
        }

        ctx.emit("url", f"🔍 Google Reverse Search", google_url, {"type": "search_engine"}, rel="reverse_search")
        ctx.emit("url", f"🔍 TinEye Reverse Search", tineye_url, {"type": "search_engine"}, rel="reverse_search")
        ctx.emit("url", f"🔍 Yandex Reverse Search", yandex_url, {"type": "search_engine"}, rel="reverse_search")

        ctx.log(f"Generated reverse search URLs", "info")
