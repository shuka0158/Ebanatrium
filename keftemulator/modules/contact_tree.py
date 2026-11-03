"""Contact Tree Database - Shows dossiers and images in sidebar"""
import sqlite3
import os
import re
from ..core import Module

class ContactTreeSearch(Module):
    name = "contact_tree"
    title = "Contact Tree Database"
    category = "Local Database"
    description = "Shows all Contact Tree dossiers and images with extracted data"
    accepts = ("name", "company")

    DB_PATH = "/home/shuka/.local/share/keftemulator/contact_tree.db"
    default = True

    def run(self, ent, ctx):
        if not os.path.exists(self.DB_PATH):
            ctx.log("Contact tree not found", "warn")
            return

        q = ent.value.strip()
        ctx.log(f"contact tree: {q}", "info")

        try:
            conn = sqlite3.connect(self.DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('SELECT filename, file_type, file_path, text_content FROM documents')
            all_docs = cursor.fetchall()

            cursor.execute('SELECT * FROM individuals')
            all_individuals = cursor.fetchall()

            # Determine what to show
            matched = []

            if len(q) == 11 and q.isdigit():
                # ID search - find matching docs
                for doc in all_docs:
                    if q in (doc['text_content'] or ""):
                        matched.append(doc)

                # Emit individual record
                for ind in all_individuals:
                    if ind['national_id'] == q:
                        # Emit as company node so it shows in sidebar
                        data = {
                            "id": q,
                            "dob": ind['date_of_birth'],
                            "gender": ind['gender'],
                            "status": str(ind.get('status', 'N/A')) if hasattr(ind, 'get') else 'N/A'
                        }
                        ctx.emit("company", f"👤 Individual {q}", q, data)
                        break
            else:
                # Name search - show ALL
                if ent.type == "name":
                    matched = all_docs

            # Emit each dossier as COMPANY node (shows in sidebar with all data)
            for doc in matched:
                filename = doc['filename']
                ftype = doc['file_type']
                content = doc['text_content'] or ""

                if ftype == 'pdf':
                    # Extract all data
                    ids = re.findall(r'\d{11}', content)
                    gender_match = re.search(r'Gender\s+([^\n]+)', content, re.IGNORECASE)
                    dob_match = re.search(r'Date of birth\s+([^\n]+)', content, re.IGNORECASE)
                    district_match = re.search(r'District:\s*([^\n]+)', content)

                    id_str = ids[0] if ids else "Unknown"

                    # Build rich metadata for sidebar display
                    metadata = {
                        "file": doc['file_path'],
                        "type": "dossier",
                        "source": "contact_tree",
                        "id": id_str,
                    }

                    if gender_match:
                        metadata["gender"] = gender_match.group(1).strip()
                    if dob_match:
                        metadata["dob"] = dob_match.group(1).strip()
                    if district_match:
                        metadata["district"] = district_match.group(1).strip()

                    # Full content as preview
                    preview = content[:300].replace('\n', ' ')
                    metadata["content"] = preview

                    # Emit as COMPANY (shows nicely in sidebar with all metadata)
                    label = f"📄 {filename} ({id_str})"
                    ctx.emit("company", label, filename, metadata, rel="dossier")

                elif ftype == 'image':
                    # Emit images as URL type
                    image_url = f"/api/contact-tree/image/{filename}"
                    img_data = {
                        "type": "screenshot",
                        "source": "contact_tree",
                        "url": image_url
                    }
                    ctx.emit("url", f"📸 {filename}", image_url, img_data)

            # For name searches: also emit ALL images
            if ent.type == "name":
                for doc in all_docs:
                    if doc['file_type'] == 'image':
                        image_url = f"/api/contact-tree/image/{doc['filename']}"
                        img_data = {"type": "screenshot", "source": "contact_tree", "url": image_url}
                        ctx.emit("url", f"📸 {doc['filename']}", image_url, img_data)

            conn.close()

        except Exception as e:
            ctx.log(f"error: {str(e)[:60]}", "warn")

