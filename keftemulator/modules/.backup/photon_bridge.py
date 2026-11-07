"""Photon Bridge - Fast web crawler and link extraction"""
import sys
sys.path.insert(0, '/media/mount/OSINT_SOURCES/Photon')

from ..core import Module
import requests

class PhotonBridge(Module):
    name = "photon_bridge"
    title = "Photon - Web Crawler"
    category = "Web"
    description = "Fast web crawler for discovering links, emails, and data"
    accepts = ("domain", "url")

    def run(self, ent, ctx):
        target = ent.value.strip()
        
        if not target.startswith('http'):
            target = f"https://{target}"
        
        ctx.log(f"Running Photon crawler on: {target}", "info")
        
        try:
            # Extract links, emails, etc from webpage
            resp = requests.get(target, timeout=10)
            if resp.status_code != 200:
                return
            
            content = resp.text
            
            # Extract emails
            import re
            emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content))
            for email in emails:
                ctx.emit("email_address",
                    f"Email: {email}",
                    email,
                    {"source": "Photon", "found_on": target},
                    rel="crawler_email")
            
            # Extract URLs
            urls = set(re.findall(r'https?://[^\s<>"{}|\\^`\[\]]*', content))
            for url in list(urls)[:50]:
                ctx.emit("link",
                    f"Link: {url}",
                    url,
                    {"source": "Photon"},
                    rel="crawler_link")
            
            ctx.log(f"✅ Found {len(emails)} emails, {len(urls)} links", "info")
            
        except Exception as e:
            ctx.log(f"Photon error: {str(e)[:50]}", "warn")

