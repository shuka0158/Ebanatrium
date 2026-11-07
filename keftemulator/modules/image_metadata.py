"""Image EXIF and metadata extractor"""
import requests
from io import BytesIO
from datetime import datetime
from ..core import Module

class ImageMetadataExtractor(Module):
    name = "image_metadata"
    title = "Image EXIF & Metadata"
    category = "Image Analysis"
    description = "Extract EXIF data, GPS location, camera info, and file metadata from images"
    accepts = ("url", "image_url")

    def run(self, ent, ctx):
        url = ent.value.strip()

        if not url.startswith("http"):
            return

        ctx.log(f"extracting image metadata: {url}", "info")

        try:
            # Download image
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                ctx.log("Failed to download image", "warn")
                return

            # Try PIL for basic metadata
            try:
                from PIL import Image
                from PIL.ExifTags import TAGS
                import piexif

                img = Image.open(BytesIO(resp.content))

                metadata = {
                    "format": img.format,
                    "size": f"{img.width}x{img.height}",
                    "mode": img.mode,
                    "source": "image_metadata"
                }

                # Try to extract EXIF
                try:
                    exif_dict = piexif.load(BytesIO(resp.content))

                    # GPS data
                    if "GPS" in exif_dict:
                        gps_data = exif_dict["GPS"]
                        metadata["gps"] = str(gps_data)
                        ctx.log("GPS data found in image", "info")

                    # DateTime
                    if "0th" in exif_dict:
                        for tag, value in exif_dict["0th"].items():
                            tag_name = piexif.TAGS["0th"][tag]["name"]
                            if tag_name == "DateTime":
                                metadata["datetime"] = value.decode()
                                ctx.log(f"Image date: {value.decode()}", "info")
                            if tag_name == "Make":
                                metadata["camera_make"] = value.decode()
                            if tag_name == "Model":
                                metadata["camera_model"] = value.decode()
                except:
                    pass

                # File size
                metadata["file_size"] = len(resp.content)

                ctx.emit("company", f"📸 Image Metadata", url, metadata, rel="metadata")

            except ImportError:
                ctx.log("PIL not available - basic metadata only", "warn")
                metadata = {
                    "file_size": len(resp.content),
                    "content_type": resp.headers.get("content-type", "unknown")
                }
                ctx.emit("company", f"📸 Image Info", url, metadata, rel="metadata")

        except Exception as e:
            ctx.log(f"metadata extraction error: {str(e)[:50]}", "warn")
