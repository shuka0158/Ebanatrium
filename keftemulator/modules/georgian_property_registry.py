"""Georgian Property Registry - Real Estate Intelligence"""

import requests

class GeorgianPropertyRegistry:
    name = "Georgian Property Registry (Cadastre)"
    category = "Intelligence"
    accepts = ["company", "name"]
    
    def investigate(self, target, ctx):
        """Search Georgian property records"""
        try:
            ctx.emit("status", f"Searching Georgian property registry: {target}")
            
            # National Agency of Public Registry (NAPR)
            search_url = f"https://napr.gov.ge"
            
            ctx.emit("link", "Georgian Property Registry",
                    f"Property search: {target}",
                    {"source": "napr.gov.ge", "query": target},
                    rel="georgian_property")
            
            ctx.emit("link", "Cadastre Portal",
                    "https://napr.gov.ge - Real estate ownership records",
                    {"url": "https://napr.gov.ge", "type": "cadastre"},
                    rel="georgian_resource")
                    
        except Exception as e:
            ctx.emit("link", "Property Registry Error", str(e)[:100],
                    {"error": str(e)}, rel="georgian_error")


MODULE = GeorgianPropertyRegistry()
