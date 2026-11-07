"""Georgian Merchant Registry - Business Intelligence"""

import requests

class GeorgianMerchantRegistry:
    name = "Georgian Merchant Registry"
    category = "Intelligence"
    accepts = ["company", "email_address"]
    
    def investigate(self, target, ctx):
        """Search Georgian business registry"""
        try:
            ctx.emit("status", f"Searching Georgian Merchant Registry: {target}")
            
            # eregs.mepa.gov.ge - Official registration system
            search_url = f"https://eregs.mepa.gov.ge/search?q={target}"
            
            ctx.emit("link", "Georgian Business Registry", 
                    f"Search: {target}",
                    {"source": "eregs.mepa.gov.ge", "company": target},
                    rel="georgian_business")
            
            ctx.emit("link", "Merchant Registry Portal",
                    "https://eregs.mepa.gov.ge - Business registration lookup",
                    {"url": "https://eregs.mepa.gov.ge", "type": "merchant_registry"},
                    rel="georgian_resource")
                    
        except Exception as e:
            ctx.emit("link", "Registry Error", str(e)[:100],
                    {"error": str(e)}, rel="georgian_error")


MODULE = GeorgianMerchantRegistry()
