"""Steganography detection - Find hidden data in images"""
import requests
from io import BytesIO
from ..core import Module

class SteganographyDetector(Module):
    name = "steganography"
    title = "Steganography Detection"
    category = "Image Analysis"
    description = "Detect potential hidden data in images using statistical analysis and common stego patterns"
    accepts = ("url", "image_url")

    def run(self, ent, ctx):
        url = ent.value.strip()

        if not url.startswith("http"):
            return

        ctx.log(f"analyzing for steganography: {url}", "info")

        try:
            # Download image
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                ctx.log("Failed to download image", "warn")
                return

            img_data = resp.content

            findings = {
                "url": url,
                "source": "steganography",
                "suspicious": False,
                "indicators": []
            }

            # Check 1: File size anomalies
            try:
                from PIL import Image
                img = Image.open(BytesIO(img_data))

                # Expected size for uncompressed image
                pixel_count = img.width * img.height
                bytes_per_pixel = len(img_data) / pixel_count if pixel_count > 0 else 0

                if bytes_per_pixel > 3.5:  # More than RGB
                    findings["indicators"].append("Large file size for image dimensions (possible hidden data)")
                    findings["suspicious"] = True
            except:
                pass

            # Check 2: Entropy analysis (high entropy = compressed/encrypted data)
            try:
                from collections import Counter
                byte_freq = Counter(img_data)
                entropy = sum(-(freq/len(img_data)) * (freq/len(img_data))**0.5 for freq in byte_freq.values())

                if entropy > 7.5:  # High entropy suggests compression/encryption
                    findings["indicators"].append("High entropy detected (possible steganography)")
                    findings["suspicious"] = True
            except:
                pass

            # Check 3: Metadata discrepancies
            try:
                from PIL import Image
                img = Image.open(BytesIO(img_data))

                # Check for thumbnail data
                try:
                    if img.thumbnail((1, 1), Image.LANCZOS):
                        findings["indicators"].append("Embedded thumbnail detected")
                except:
                    pass
            except:
                pass

            # Check 4: Look for common stego file signatures
            if img_data[0:3] == b'GIF':
                if b'Steg' in img_data or b'steg' in img_data:
                    findings["indicators"].append("Potential Steg watermark found")
                    findings["suspicious"] = True

            findings["status"] = "Suspicious" if findings["suspicious"] else "Clean"

            if findings["suspicious"]:
                ctx.log("⚠️ Potential steganography indicators found!", "warn")
                ctx.emit("company", f"🔓 Steganography Alert", url, findings, rel="stego")
            else:
                ctx.log("No steganography indicators detected", "info")
                ctx.emit("company", f"✅ Steganography Check", url, findings, rel="stego")

        except Exception as e:
            ctx.log(f"stego detection error: {str(e)[:50]}", "warn")
