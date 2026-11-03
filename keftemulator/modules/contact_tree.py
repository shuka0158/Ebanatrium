"""Contact Tree Database - Shows ALL dossiers and images for person searches"""
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
            ctx.log("Contact tree database not found", "warn")
            return

        q = ent.value.strip()
        ctx.log(f"searching contact tree: {q}", "info")

        try:
            conn = sqlite3.connect(self.DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get ALL data
            cursor.execute('SELECT filename, file_type, file_path, text_content FROM documents ORDER BY filename')
            all_docs = cursor.fetchall()

            cursor.execute('SELECT * FROM individuals ORDER BY national_id')
            all_individuals = cursor.fetchall()

            # Section header
            ctx.emit("person", "📂 CONTACT TREE", f"{len(all_docs)} docs, {len(all_individuals)} individuals",
                    {"type": "section_header", "source": "contact_tree", "priority": "high"})

            # ID search
            if len(q) == 11 and q.isdigit():
                for ind in all_individuals:
                    if ind['national_id'] == q:
                        status = dict(ind).get('status', 'N/A')
                        ctx.emit("person", f"👤 {q}",
                                f"DOB: {ind['date_of_birth']} | Gender: {ind['gender']}",
                                {"type": "person", "source": "contact_tree_individual", "id": q})
                        break

                # Find dossiers
                matched = []
                for doc in all_docs:
                    if q in (doc['text_content'] or ""):
                        matched.append(doc)
            else:
                # Name search - show ALL for person searches
                matched = all_docs if ent.type == "name" else []

            # Emit all matched
            for doc in matched:
                filename = doc['filename']
                ftype = doc['file_type']
                content = doc['text_content'] or ""

                if ftype == 'pdf':
                    # Extract data
                    ids = re.findall(r'\d{11}', content)
                    gender_match = re.search(r'Gender\s+([^\n]+)', content, re.IGNORECASE)
                    dob_match = re.search(r'Date of birth\s+([^\n]+)', content, re.IGNORECASE)

                    label = f"📄 {filename}"
                    if ids:
                        label += f" (ID: {ids[0]})"

                    # Emit as company
                    data = {"type": "dossier", "source": "contact_tree", "file": doc['file_path']}
                    if ids:
                        data["id"] = ids[0]
                    if gender_match:
                        data["gender"] = gender_match.group(1).strip()
                    if dob_match:
                        data["dob"] = dob_match.group(1).strip()

                    ctx.emit("company", label, label, data, rel="dossier")

                    # Emit fields
                    if ids:
                        ctx.emit("info", "🆔 ID", ids[0], {"source": "contact_tree_pdf"})
                    if gender_match:
                        ctx.emit("info", "⚧ Gender", gender_match.group(1).strip(), {"source": "contact_tree_pdf"})
                    if dob_match:
                        ctx.emit("info", "📅 DOB", dob_match.group(1).strip(), {"source": "contact_tree_pdf"})

                elif ftype == 'image':
                    image_url = f"/api/contact-tree/image/{filename}"
                    # Don't include emoji in the key, only in label
                    ctx.emit("image_url", f"📸 Screenshot", image_url, {"type": "screenshot", "source": "contact_tree", "filename": filename})

            # For name search: ALWAYS show ALL images
            if ent.type == "name":
                for doc in all_docs:
                    if doc['file_type'] == 'image':
                        image_url = f"/api/contact-tree/image/{doc['filename']}"
                        ctx.emit("image_url", f"📸 Screenshot", image_url, {"type": "screenshot", "source": "contact_tree", "filename": doc['filename']})

            conn.close()

        except Exception as e:
            ctx.log(f"error: {str(e)[:60]}", "warn")

