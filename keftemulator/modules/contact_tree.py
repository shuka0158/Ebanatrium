"""Contact Tree Database - Shows dossiers and images in sidebar"""
import sqlite3
import os
import re
from urllib.parse import quote
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
                # Name search - filter by query text
                if ent.type == "name":
                    matched = [doc for doc in all_docs if q.lower() in (doc['text_content'] or "").lower()]

            # Emit each matched result (skip PDF dossiers - only show images)
            for doc in matched:
                filename = doc['filename']
                ftype = doc['file_type']
                content = doc['text_content'] or ""

                # Skip PDF dossiers - don't show them in results
                if ftype == 'pdf':
                    continue

                elif ftype == 'image':
                    # Emit images with URL-encoded filename (spaces must be %20)
                    encoded_filename = quote(filename, safe='')
                    image_url = f"/api/contact-tree/image/{encoded_filename}"
                    img_data = {
                        "source": "contact_tree",
                        "filename": filename,
                        "preview": image_url  # This renders the image thumbnail
                    }
                    ctx.emit("image_url", f"📸 {filename}", image_url, img_data)

            # Only show images that matched the search, don't emit ALL images

            conn.close()

        except Exception as e:
            ctx.log(f"error: {str(e)[:60]}", "warn")

