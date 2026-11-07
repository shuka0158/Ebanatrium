"""Image intelligence: EXIF/GPS (Pillow + ExifTool), hashes, face detection, reverse image search."""
import hashlib
import json
import uuid
from pathlib import Path
from urllib.parse import quote

from PIL import Image, ExifTags

from ..core import Module
from ..util import get, find_tool, run_cmd, UPLOADS



def _cv2():
    try:
        import cv2  # optional dependency, may be installed while the app runs
        return cv2
    except Exception:  # noqa: BLE001
        return None


def _ratio(v):
    try:
        return float(v)
    except Exception:
        try:
            return v[0] / v[1]
        except Exception:
            return 0.0


def _gps(gps):
    def conv(dms, ref):
        d, m, s = (_ratio(x) for x in dms)
        val = d + m / 60 + s / 3600
        return -val if ref in ("S", "W") else val
    try:
        return conv(gps[2], gps[1]), conv(gps[4], gps[3])
    except Exception:
        return None


def reverse_links(url=None):
    if url:
        u = quote(url, safe="")
        return [("Google Lens", f"https://lens.google.com/uploadbyurl?url={u}"),
                ("Yandex Images", f"https://yandex.com/images/search?rpt=imageview&url={u}"),
                ("Bing Visual Search", f"https://www.bing.com/images/search?view=detailv2&iss=sbi&q=imgurl:{u}"),
                ("TinEye", f"https://tineye.com/search?url={u}")]
    return [("Google Lens (upload)", "https://lens.google.com/"),
            ("Yandex Images (upload)", "https://yandex.com/images/"),
            ("Bing Visual Search (upload)", "https://www.bing.com/visualsearch"),
            ("TinEye (upload)", "https://tineye.com/")]


class ImageAnalysis(Module):
    name = "image"
    title = "Image metadata & faces"
    category = "Image"
    description = ("EXIF (camera, software, timestamps, GPS → map), file hashes, face detection with crops, "
                   "reverse image search launchers (Google Lens, Yandex, Bing, TinEye).")
    accepts = ("image", "image_url")

    def run(self, ent, ctx):
        if ent.type == "image_url":
            try:
                r = get(ent.value, timeout=20)
                if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image"):
                    ctx.log("not an image / download failed", "warn")
                    return
                path = UPLOADS / f"{uuid.uuid4().hex}{Path(ent.value.split('?')[0]).suffix or '.jpg'}"
                path.write_bytes(r.content)
            except Exception as e:
                ctx.log(f"download: {e}", "warn")
                return
            for t, u in reverse_links(ent.value):
                ctx.emit("link", u, t, {"kind": "reverse image"}, rel="reverse search", pivot=False)
        else:
            path = Path(ent.value)
            for t, u in reverse_links():
                ctx.emit("link", u, t, {"kind": "reverse image"}, rel="reverse search", pivot=False)
        raw = path.read_bytes()
        info = {"file": path.name, "size_bytes": len(raw), "md5": hashlib.md5(raw).hexdigest(),
                "sha256": hashlib.sha256(raw).hexdigest(), "preview": f"/uploads/{path.name}"}
        try:
            im = Image.open(path)
            info.update({"format": im.format, "width": im.width, "height": im.height, "mode": im.mode})
            exif = im.getexif()
            tags = {}
            for k, v in exif.items():
                tags[ExifTags.TAGS.get(k, str(k))] = v
            for ifd_id in (0x8769,):  # Exif sub-IFD
                try:
                    for k, v in exif.get_ifd(ifd_id).items():
                        tags[ExifTags.TAGS.get(k, str(k))] = v
                except Exception:
                    pass
            gps_ifd = {}
            try:
                gps_ifd = exif.get_ifd(0x8825)
            except Exception:
                pass
            clean = {k: (v.decode(errors="replace") if isinstance(v, bytes) else str(v))[:200]
                     for k, v in tags.items() if k not in ("MakerNote", "UserComment", "PrintImageMatching")}
            info["exif"] = clean
            for k in ("Make", "Model", "Software", "DateTimeOriginal", "Artist", "Copyright", "LensModel"):
                if clean.get(k):
                    info[k.lower()] = clean[k]
            if clean.get("Make") or clean.get("Model"):
                ctx.emit("device", f"{clean.get('Make', '')} {clean.get('Model', '')}".strip(),
                         rel="taken with", pivot=False)
            if clean.get("Artist"):
                ctx.emit("name", clean["Artist"], rel="EXIF artist")
            g = _gps(gps_ifd) if gps_ifd else None
            if g and any(g):
                lat, lon = round(g[0], 6), round(g[1], 6)
                ctx.emit("location", f"{lat},{lon}", "Photo GPS location",
                         {"lat": lat, "lon": lon, "accuracy": "exact (EXIF GPS)",
                          "maps": f"https://www.google.com/maps?q={lat},{lon}"}, rel="photographed at", pivot=False)
        except Exception as e:
            ctx.log(f"PIL: {e}", "warn")
        if find_tool("exiftool"):
            code, out = run_cmd([find_tool("exiftool"), "-json", "-n", str(path)], timeout=60)
            try:
                full = json.loads(out)[0]
                info["exiftool"] = {k: str(v)[:200] for k, v in full.items() if k not in ("SourceFile",)}
                for k in ("Creator", "Author", "OwnerName", "By-line", "XPAuthor"):
                    if full.get(k):
                        ctx.emit("name", str(full[k]), rel=f"metadata {k}")
                if full.get("SerialNumber") or full.get("InternalSerialNumber"):
                    info["camera_serial"] = full.get("SerialNumber") or full.get("InternalSerialNumber")
            except Exception:
                pass
        if _cv2() is not None:
            self.faces(path, info, ctx)
        ctx.update(info)

    def faces(self, path, info, ctx):
        cv2 = _cv2()
        try:
            img = cv2.imread(str(path))
            if img is None:
                return
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            faces = casc.detectMultiScale(gray, 1.1, 6, minSize=(40, 40))
            info["faces_detected"] = len(faces)
            for i, (x, y, w, h) in enumerate(faces[:12]):
                pad = int(0.25 * w)
                crop = img[max(0, y - pad):y + h + pad, max(0, x - pad):x + w + pad]
                name = f"{path.stem}_face{i}.jpg"
                cv2.imwrite(str(UPLOADS / name), crop)
                ctx.emit("face", f"/uploads/{name}", f"Face #{i + 1}",
                         {"preview": f"/uploads/{name}", "box": [int(x), int(y), int(w), int(h)],
                          "tip": "Download and use the reverse-image links to find where this photo appears."},
                         rel="contains face", pivot=False)
        except Exception as e:
            ctx.log(f"face detection: {e}", "warn")
