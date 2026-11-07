"""Image hash calculator - Find duplicate and similar images"""
import requests
import hashlib
from io import BytesIO
from ..core import Module

class ImageHashCalculator(Module):
    name = "image_hash"
    title = "Image Hash & Fingerprint"
    category = "Image Analysis"
    description = "Calculate MD5, SHA256, and perceptual hashes for image comparison and duplicate detection"
    accepts = ("url", "image_url")

    def run(self, ent, ctx):
        url = ent.value.strip()

        if not url.startswith("http"):
            return

        ctx.log(f"calculating image hashes: {url}", "info")

        try:
            # Download image
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                ctx.log("Failed to download image", "warn")
                return

            img_data = resp.content

            # Calculate standard hashes
            md5_hash = hashlib.md5(img_data).hexdigest()
            sha256_hash = hashlib.sha256(img_data).hexdigest()

            hashes = {
                "md5": md5_hash,
                "sha256": sha256_hash,
                "file_size": len(img_data),
                "source": "image_hash"
            }

            ctx.log(f"MD5: {md5_hash}", "info")
            ctx.log(f"SHA256: {sha256_hash}", "info")

            # Try perceptual hash for duplicate detection
            try:
                from PIL import Image
                import hashlib

                img = Image.open(BytesIO(img_data))

                # Simple perceptual hash
                img_small = img.resize((8, 8), Image.LANCZOS)
                pixels = list(img_small.getdata())

                avg = sum(pixels) / len(pixels)
                phash = "".join(str(1) if pixel > avg else str(0) for pixel in pixels)
                hashes["perceptual_hash"] = phash

                ctx.log("Perceptual hash calculated", "info")
            except:
                ctx.log("Perceptual hash unavailable", "warn")

            ctx.emit("company", f"🔐 Image Hashes", url, hashes, rel="hash")

        except Exception as e:
            ctx.log(f"hash calculation error: {str(e)[:50]}", "warn")
