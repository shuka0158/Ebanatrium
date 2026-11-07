"""Georgian Court Records - Real Legal Intelligence"""

import requests
import re

class GeorgianCourtRecords:
    name = "Georgian Court Records"
    category = "Intelligence"
    accepts = ["name", "email_address", "company"]
    
    def investigate(self, target, ctx):
        """Search Georgian court records"""
        try:
            ctx.emit("status", f"Searching Georgian court records for: {target}")
            
            # Georgian courts portal
            url = "https://www.court.ge"
            
            # Try to search civil/criminal cases
            search_url = f"{url}/search?q={target}"
            
            resp = requests.get(search_url, timeout=10)
            
            if resp.status_code == 200:
                ctx.emit("link", "Georgian Courts Portal", 
                        f"Search results for: {target}",
                        {"source": "court.ge", "target": target},
                        rel="georgian_court")
            
            ctx.emit("link", "Court Records Access", 
                    "https://www.court.ge - Search civil/criminal cases",
                    {"url": "https://www.court.ge", "type": "court_records"},
                    rel="georgian_resource")
                    
        except Exception as e:
            ctx.emit("link", "Court Records Error", str(e)[:100],
                    {"error": str(e)}, rel="georgian_error")


MODULE = GeorgianCourtRecords()
