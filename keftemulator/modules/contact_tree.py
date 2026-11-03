"""Contact Tree Database Integration - Search local contact database"""
import sqlite3
import os
import re
from ..core import Module

class ContactTreeSearch(Module):
    name = "contact_tree"
    title = "Contact Tree Database"
    category = "Local Database"
    description = "Search local contact tree database - shows dossiers, images, and extracted data"
    accepts = ("name", "company")

    DB_PATH = "/home/shuka/.local/share/keftemulator/contact_tree.db"

    def run(self, ent, ctx):
        if not os.path.exists(self.DB_PATH):
            ctx.log("Contact tree database not found", "warn")
            return

        q = ent.value.strip()
        ctx.log(f"searching contact tree for: {q}", "info")

        try:
            conn = sqlite3.connect(self.DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get all documents
            cursor.execute('SELECT filename, file_type, file_path, text_content FROM documents ORDER BY filename')
            all_docs = cursor.fetchall()

            matched = []

            for row in all_docs:
                filename = row['filename']
                ftype = row['file_type']
                content = row['text_content'] or ""

                # Match: filename, query in content, or ID match
                is_match = (
                    q.lower() in filename.lower() or
                    q in content or
                    (len(q) == 11 and q.isdigit() and q in content)
                )

                if is_match:
                    matched.append(row)

            # If no exact matches, show all documents anyway (for person searches)
            if not matched and ent.type == "name":
                matched = all_docs[:10]
                ctx.log(f"showing {len(matched)} contact tree documents", "info")
            elif matched:
                ctx.log(f"found {len(matched)} matches", "info")

            # Emit results
            for row in matched:
                filename = row['filename']
                ftype = row['file_type']
                filepath = row['file_path']

                if ftype == 'pdf':
                    # Extract IDs from content
                    ids = re.findall(r'\d{11}', row['text_content'] or "")
                    label = f"📄 {filename}"
                    if ids:
                        label += f" (ID: {ids[0]})"

                    ctx.emit("link", label, filepath,
                            {"type": "dossier", "source": "contact_tree",
                             "file_type": "pdf"})

                elif ftype == 'image':
                    ctx.emit("link", f"📸 {filename}", filepath,
                            {"type": "screenshot", "source": "contact_tree"})

            conn.close()

            if matched:
                ctx.update({"contact_tree_matches": len(matched)})

        except Exception as e:
            ctx.log(f"contact tree error: {str(e)[:60]}", "warn")

