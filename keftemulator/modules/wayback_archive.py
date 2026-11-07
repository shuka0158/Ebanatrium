"""Wayback Machine - Historical data from Internet Archive"""
import requests
from ..core import Module

class WaybackArchive(Module):
    name = "wayback_archive"
    title = "Wayback Machine Archive"
    category = "Threat Detection"
    description = "Search Internet Archive for historical website data"
    accepts = ("url", "domain", "company")

    def run(self, ent, ctx):
        query = ent.value.strip()
        
        # Ensure it looks like a domain
        if not '.' in query:
            return
        
        ctx.log(f"Wayback archive search: {query}", "info")
        
        try:
            # Check if domain is archived
            resp = requests.get(
                f"https://archive.org/wayback/available?url={query}",
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                
                if data.get('archived_snapshots'):
                    snapshots = data['archived_snapshots']
                    
                    ctx.log(f"Wayback: Found archived versions", "info")
                    ctx.emit("company", f"📚 Wayback Archive Data", query, {
                        "snapshots": snapshots,
                        "source": "wayback",
                        "url": f"https://web.archive.org/web/*/{query}"
                    }, rel="archive_data")
                else:
                    ctx.log("Wayback: No archive found", "info")
                    
        except Exception as e:
            ctx.log(f"Wayback error: {str(e)[:50]}", "warn")

