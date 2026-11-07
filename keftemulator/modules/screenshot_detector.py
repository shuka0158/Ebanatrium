"""Screenshot detector - Identify if image is a screenshot"""
import requests
from io import BytesIO
from ..core import Module

class ScreenshotDetector(Module):
    name = "screenshot_detector"
    title = "Screenshot Detector"
    category = "Image Analysis"
    description = "Identify if image is a screenshot and which OS/platform it came from"
    accepts = ("url", "image_url")

    def run(self, ent, ctx):
        url = ent.value.strip()

        if not url.startswith("http"):
            return

        ctx.log(f"analyzing for screenshot: {url}", "info")

        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                return

            img_data = resp.content
            analysis = {
                "url": url,
                "source": "screenshot_detector",
                "is_screenshot": False,
                "indicators": [],
                "os": "Unknown"
            }

            try:
                from PIL import Image
                img = Image.open(BytesIO(img_data))

                # Check 1: Aspect ratio (screenshots often have standard resolutions)
                aspect_ratio = img.width / img.height if img.height > 0 else 0
                analysis["aspect_ratio"] = round(aspect_ratio, 2)
                analysis["resolution"] = f"{img.width}x{img.height}"

                # Common screenshot resolutions
                screenshot_resolutions = [
                    (1920, 1080), (1366, 768), (1440, 900), (1280, 720),  # Desktop
                    (768, 1024), (1024, 768), (1536, 2048),  # iPad
                    (1125, 2436), (1170, 2532), (1080, 1920),  # iPhone
                ]

                for w, h in screenshot_resolutions:
                    if (img.width == w and img.height == h) or (img.width == h and img.height == w):
                        analysis["is_screenshot"] = True
                        analysis["indicators"].append(f"Standard screenshot resolution: {img.width}x{img.height}")
                        ctx.log("Standard resolution detected", "info")
                        break

                # Check 2: Color space (screenshots usually RGB or RGBA)
                if img.mode in ["RGB", "RGBA", "RGBX"]:
                    if img.mode == "RGBA":
                        analysis["indicators"].append("RGBA color space (transparency support)")

                # Check 3: Metadata for screenshot indicators
                try:
                    metadata = img.info

                    # macOS screenshots have specific software tag
                    if 'Software' in metadata:
                        software = str(metadata['Software'])
                        if 'macOS' in software or 'screencapture' in software.lower():
                            analysis["os"] = "macOS"
                            analysis["is_screenshot"] = True
                            analysis["indicators"].append(f"macOS screenshot (software: {software})")
                            ctx.log("macOS screenshot detected", "info")

                    # Check comment field
                    if 'Comment' in metadata:
                        comment = str(metadata['Comment']).lower()
                        if 'screenshot' in comment or 'screen shot' in comment:
                            analysis["is_screenshot"] = True
                            analysis["indicators"].append("Screenshot metadata found in comments")
                except:
                    pass

                # Check 4: Windows screenshot characteristics
                # Windows screenshots often have slightly different EXIF patterns
                try:
                    exif = img._getexif()
                    if exif:
                        from PIL.ExifTags import TAGS
                        for tag_id, value in exif.items():
                            tag_name = TAGS.get(tag_id, tag_id)
                            if tag_name == "Software" and "Windows" in str(value):
                                analysis["os"] = "Windows"
                                analysis["is_screenshot"] = True
                                analysis["indicators"].append("Windows OS metadata")
                except:
                    pass

                # Check 5: Filename indicators
                if any(x in url.lower() for x in ['screenshot', 'screen shot', 'snap', 'capture']):
                    analysis["is_screenshot"] = True
                    analysis["indicators"].append("Screenshot keyword in filename")

                # Check 6: PNG vs JPEG (screenshots often PNG)
                if img.format == "PNG":
                    analysis["indicators"].append("PNG format (common for screenshots)")
                    if not analysis["is_screenshot"]:
                        analysis["is_screenshot"] = True

            except Exception as e:
                ctx.log(f"PIL analysis failed: {str(e)[:30]}", "warn")

            analysis["confidence"] = "High" if analysis["is_screenshot"] else "Low"

            if analysis["is_screenshot"]:
                ctx.log(f"⚠️ Screenshot detected (OS: {analysis['os']})", "info")
                ctx.emit("company", f"📸 Screenshot Detected", url, analysis, rel="screenshot")
            else:
                ctx.emit("company", f"✅ Screenshot Check", url, analysis, rel="screenshot")

        except Exception as e:
            ctx.log(f"screenshot detection error: {str(e)[:50]}", "warn")
