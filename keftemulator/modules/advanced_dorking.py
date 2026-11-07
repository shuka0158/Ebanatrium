"""Advanced Google Dorking - Deep web search intelligence"""
import requests
from urllib.parse import quote
from ..core import Module

class AdvancedDorking(Module):
    name = "advanced_dorking"
    title = "Advanced Google Dorking"
    category = "Web"
    description = "Google dorks to find exposed documents, databases, personal info"
    accepts = ("name", "email_address", "domain")

    def run(self, ent, ctx):
        target = ent.value.strip()
        
        ctx.log(f"Google dorking: {target}", "info")
        
        # Effective Google dorks
        dorks = [
            f'"{target}" filetype:pdf',
            f'"{target}" filetype:xlsx',
            f'"{target}" filetype:docx',
            f'"{target}" inurl:linkedin',
            f'"{target}" inurl:facebook',
            f'"{target}" site:pastebin.com',
            f'"{target}" site:archive.org',
            f'site:github.com "{target}"',
            f'site:gist.github.com "{target}"',
            f'intext:"{target}" password',
        ]
        
        for dork in dorks:
            url = f"https://www.google.com/search?q={quote(dork)}"
            ctx.emit("link",
                f"Google Dork: {dork[:50]}...",
                url,
                {"dork": dork, "type": "google_dorking"},
                rel="dork_search")
            ctx.log(f"✅ Dork: {dork[:40]}", "info")

