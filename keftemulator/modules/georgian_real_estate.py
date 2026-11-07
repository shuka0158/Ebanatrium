"""Georgian Real Estate Intelligence - Property Portals"""

import requests

class GeorgianRealEstate:
    name = "Georgian Real Estate Portal"
    category = "Intelligence"
    accepts = ["name", "company"]
    
    def investigate(self, target, ctx):
        """Search Georgian real estate databases"""
        try:
            ctx.emit("status", f"Searching Georgian real estate: {target}")
            
            portals = [
                ("Ss.ge", "https://ss.ge", "Largest Georgian property portal"),
                ("MyHouse.ge", "https://myhouse.ge", "Georgian real estate marketplace"),
                ("Adept.ge", "https://adept.ge", "Property listings"),
                ("Kre.ge", "https://kre.ge", "Real estate search"),
            ]
            
            for name, url, desc in portals:
                ctx.emit("link", name,
                        desc,
                        {"url": url, "type": "real_estate", "search": target},
                        rel="georgian_realestate")
                        
        except Exception as e:
            ctx.emit("link", "Real Estate Error", str(e)[:100],
                    {"error": str(e)}, rel="georgian_error")


MODULE = GeorgianRealEstate()
