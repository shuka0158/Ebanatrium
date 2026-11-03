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

    default = True  # Run by default to show Contact Tree always

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

            # Emit section header
            ctx.emit("person", f"📂 CONTACT TREE DATABASE",
                    f"Local database with {len(all_docs)} documents",
                    {"type": "section_header", "source": "contact_tree", "priority": "high"})

            # Emit results
            for row in matched:
                filename = row['filename']
                ftype = row['file_type']
                filepath = row['file_path']
                content = row['text_content'] or ""

                if ftype == 'pdf':
                    # Extract IDs and info from dossier
                    ids = re.findall(r'\d{11}', content)
                    name_match = re.search(r'Name\s+([^\n]+)', content, re.IGNORECASE)
                    gender_match = re.search(r'Gender\s+([^\n]+)', content, re.IGNORECASE)
                    dob_match = re.search(r'Date of birth\s+([^\n]+)', content, re.IGNORECASE)

                    label = f"📄 {filename}"
                    if ids:
                        label += f" (ID: {ids[0]})"

                    # Emit PDF link
                    ctx.emit("link", label, filepath,
                            {"type": "dossier", "source": "contact_tree",
                             "file_type": "pdf"})

                    # Emit extracted dossier data
                    if ids:
                        ctx.emit("info", f"🆔 ID", ids[0],
                                {"type": "id", "source": "contact_tree_pdf"})
                    if name_match:
                        ctx.emit("info", f"👤 Name", name_match.group(1).strip(),
                                {"type": "name", "source": "contact_tree_pdf"})
                    if gender_match:
                        ctx.emit("info", f"⚧ Gender", gender_match.group(1).strip(),
                                {"type": "gender", "source": "contact_tree_pdf"})
                    if dob_match:
                        ctx.emit("info", f"📅 DOB", dob_match.group(1).strip(),
                                {"type": "date_of_birth", "source": "contact_tree_pdf"})

                    # Emit content preview
                    preview = content[:300].replace('\n', ' ')
                    ctx.emit("info", f"📋 Dossier", preview,
                            {"type": "document", "source": "contact_tree_pdf"})

                elif ftype == 'image':
                    # Serve image through HTTP instead of file://
                    # Use API endpoint to serve the image
                    image_url = f"/api/contact-tree/image/{filename}"
                    ctx.emit("image_url", f"📸 {filename}", image_url,
                            {"type": "screenshot", "source": "contact_tree"})

            conn.close()

            if matched:
                ctx.update({"contact_tree_matches": len(matched)})

        except Exception as e:
            ctx.log(f"contact tree error: {str(e)[:60]}", "warn")

