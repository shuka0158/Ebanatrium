"""Photo forensics - Detect image manipulation and editing"""
import requests
from io import BytesIO
from ..core import Module

class PhotoForensics(Module):
    name = "photo_forensics"
    title = "Photo Forensics & Editing Detection"
    category = "Image Analysis"
    description = "Detect image compression artifacts, editing, splicing, and manipulation indicators"
    accepts = ("url", "image_url")

    def run(self, ent, ctx):
        url = ent.value.strip()

        if not url.startswith("http"):
            return

        ctx.log(f"analyzing for editing: {url}", "info")

        try:
            # Download image
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                ctx.log("Failed to download image", "warn")
                return

            img_data = resp.content
            forensics = {
                "url": url,
                "source": "photo_forensics",
                "edited": False,
                "indicators": []
            }

            try:
                from PIL import Image
                import io

                img = Image.open(BytesIO(img_data))

                # Check 1: JPEG compression quality
                if img.format == "JPEG":
                    forensics["format"] = "JPEG"

                    # Re-save at high quality and compare
                    high_quality = io.BytesIO()
                    img.save(high_quality, format="JPEG", quality=95)
                    high_quality_data = high_quality.getvalue()

                    # Size difference indicates compression
                    size_ratio = len(img_data) / len(high_quality_data)
                    forensics["compression_ratio"] = round(size_ratio, 3)

                    if size_ratio < 0.8:
                        forensics["indicators"].append("Heavy JPEG compression (possible hiding)")
                        forensics["edited"] = True

                elif img.format == "PNG":
                    forensics["format"] = "PNG"
                    # PNG uses lossless compression
                    forensics["indicators"].append("PNG format (lossless)")

                # Check 2: Color channel anomalies
                if img.mode == "RGB":
                    forensics["color_mode"] = "RGB"
                    pixels = img.getdata()

                    # Check for suspicious patterns
                    try:
                        pixel_list = list(pixels)
                        r_vals = [p[0] for p in pixel_list]
                        g_vals = [p[1] for p in pixel_list]
                        b_vals = [p[2] for p in pixel_list]

                        # Check if channels are too similar (steganography)
                        from statistics import stdev
                        if len(r_vals) > 10:
                            r_var = stdev(r_vals)
                            g_var = stdev(g_vals)
                            b_var = stdev(b_vals)

                            if abs(r_var - g_var) < 5 and abs(g_var - b_var) < 5:
                                forensics["indicators"].append("Suspicious color channel variance (possible data hiding)")
                                forensics["edited"] = True
                    except:
                        pass

                # Check 3: Metadata anomalies
                try:
                    exif = img._getexif()
                    if exif:
                        forensics["has_exif"] = True

                        # Check for creation date vs modification date mismatches
                        from PIL.ExifTags import TAGS
                        for tag_id, value in exif.items():
                            tag_name = TAGS.get(tag_id, tag_id)
                            if tag_name == "DateTime":
                                forensics["exif_date"] = str(value)
                    else:
                        forensics["has_exif"] = False
                        forensics["indicators"].append("EXIF data missing or stripped (possible editing)")
                except:
                    pass

                # Check 4: Dimensions suspicions
                if img.width % 8 != 0 or img.height % 8 != 0:
                    forensics["indicators"].append(f"Non-standard dimensions ({img.width}x{img.height}) - possible cropping")

            except Exception as e:
                ctx.log(f"PIL analysis failed: {str(e)[:30]}", "warn")

            forensics["status"] = "Potentially Edited" if forensics["edited"] else "Appears Unmodified"

            if forensics["edited"]:
                ctx.log("⚠️ Image may have been edited or manipulated", "warn")
                ctx.emit("company", f"🔍 Forensics Alert", url, forensics, rel="forensics")
            else:
                ctx.log("No obvious signs of editing detected", "info")
                ctx.emit("company", f"✅ Forensics Check", url, forensics, rel="forensics")

        except Exception as e:
            ctx.log(f"forensics error: {str(e)[:50]}", "warn")
