"""Georgian Business Directory - Company Search"""

import requests
from urllib.parse import quote

class GeorgianBusinessDirectory:
    name = "Georgian Business Directory"
    category = "Intelligence"
    accepts = ["company", "email_address", "phone_number"]
    
    def investigate(self, target, ctx):
        """Search Georgian business directories"""
        try:
            ctx.emit("status", f"Searching Georgian business directory: {target}")
            
            # Multiple Georgian business portals
            sources = [
                ("Yellow Pages Georgia", "https://yellowpages.ge", "yellowpages"),
                ("Business Directory", "https://businessdb.ge", "businessdb"),
                ("Georgian Companies", "https://companies.ge", "companies"),
            ]
            
            for name, url, code in sources:
                search_url = f"{url}?q={quote(target)}"
                ctx.emit("link", name,
                        f"Search: {target}",
                        {"source": code, "url": url, "query": target},
                        rel="georgian_business_dir")
                        
        except Exception as e:
            ctx.emit("link", "Business Directory Error", str(e)[:100],
                    {"error": str(e)}, rel="georgian_error")


MODULE = GeorgianBusinessDirectory()
