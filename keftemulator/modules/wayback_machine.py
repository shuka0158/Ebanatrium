"""Wayback Machine - Historical Intelligence"""

import requests

class WaybackMachine:
    name = "Wayback Machine Archive"
    category = "Intelligence"
    accepts = ["domain", "url"]
    
    def investigate(self, target, ctx):
        """Search Wayback Machine for historical versions"""
        try:
            ctx.emit("status", f"Searching Wayback Machine: {target}")
            
            # Wayback Machine API
            api_url = f"https://archive.org/wayback/available?url={target}"
            
            resp = requests.get(api_url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('archived_snapshots'):
                    count = len(data['archived_snapshots']['snapshots'])
                    ctx.emit("link", "Archived Snapshots", f"{count} versions found",
                            {"url": target, "count": count},
                            rel="wayback_archive")
            
            ctx.emit("link", "Wayback Machine Portal",
                    f"https://web.archive.org/web/*/{target}",
                    {"type": "archive", "source": "wayback"},
                    rel="benediction_feature")
                    
        except Exception as e:
            ctx.emit("link", "Archive Error", str(e)[:100],
                    {"error": str(e)}, rel="benediction_error")


MODULE = WaybackMachine()
