"""PDF metadata extractor"""
import requests
from io import BytesIO
from ..core import Module

class PDFMetadataExtractor(Module):
    name = "pdf_metadata"
    title = "PDF Metadata Extractor"
    category = "Document Analysis"
    description = "Extract author, creation date, software, and embedded metadata from PDF files"
    accepts = ("url",)

    def run(self, ent, ctx):
        url = ent.value.strip()

        if not url.lower().endswith('.pdf') and 'pdf' not in url.lower():
            return

        ctx.log(f"extracting PDF metadata: {url}", "info")

        try:
            # Download PDF
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200:
                ctx.log("Failed to download PDF", "warn")
                return

            pdf_data = resp.content

            metadata = {
                "url": url,
                "file_size": len(pdf_data),
                "source": "pdf_metadata"
            }

            # Try PyPDF2
            try:
                try:
                    import PyPDF2
                    reader = PyPDF2.PdfReader(BytesIO(pdf_data))

                    if reader.metadata:
                        meta = reader.metadata

                        if meta.title:
                            metadata["title"] = meta.title
                        if meta.author:
                            metadata["author"] = meta.author
                            ctx.log(f"Author: {meta.author}", "info")
                        if meta.creator:
                            metadata["creator"] = meta.creator
                        if meta.producer:
                            metadata["producer"] = meta.producer
                            ctx.log(f"Producer: {meta.producer}", "info")
                        if meta.creation_date:
                            metadata["created"] = str(meta.creation_date)
                        if meta.modification_date:
                            metadata["modified"] = str(meta.modification_date)

                    metadata["pages"] = len(reader.pages)
                except ImportError:
                    pass
            except:
                pass

            # Try pdfplumber
            try:
                import pdfplumber

                with pdfplumber.open(BytesIO(pdf_data)) as pdf:
                    if pdf.metadata:
                        metadata.update({k: str(v) for k, v in pdf.metadata.items()})

                    # Extract text preview
                    if pdf.pages:
                        first_page_text = pdf.pages[0].extract_text()
                        if first_page_text:
                            metadata["preview"] = first_page_text[:200]
            except:
                pass

            # Check for embedded files/attachments
            if b'EmbeddedFile' in pdf_data or b'/Filespec' in pdf_data:
                metadata["indicators"] = ["Embedded files/attachments detected"]
                ctx.log("⚠️ PDF contains embedded files", "warn")

            ctx.emit("company", f"📄 PDF Metadata", url, metadata, rel="pdf_meta")

        except Exception as e:
            ctx.log(f"PDF extraction error: {str(e)[:50]}", "warn")
