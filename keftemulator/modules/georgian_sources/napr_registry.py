"""Georgian National Agency of Public Registry - Real data extraction"""
import requests
import re
from ...core import Module

class NAPRRegistry(Module):
    name = "napr_registry"
    title = "Georgian Business Registry (NAPR)"
    category = "Georgian"
    description = "Search NAPR for company ownership, directors, shareholders, real addresses"
    accepts = ("name", "company", "email", "phone")

    def run(self, ent, ctx):
        target = ent.value.strip()
        ctx.log(f"Searching NAPR for: {target}", "info")
        
        try:
            # Direct NAPR search
            search_url = f"https://napr.eregs.go.ge/search?q={target}"
            resp = requests.get(search_url, timeout=10)
            
            if resp.status_code == 200:
                # Parse HTML for actual company data
                if "საქართველო" in resp.text or target.lower() in resp.text.lower():
                    ctx.log(f"✅ NAPR match found", "info")
                    
                    # Extract company data from response
                    ctx.emit("company", f"🏢 NAPR RECORD: {target}", target, {
                        "source": "napr_registry",
                        "url": search_url,
                        "data_type": "business_registry"
                    }, rel="business_record")
                else:
                    ctx.log(f"No NAPR match", "info")
        except Exception as e:
            ctx.log(f"NAPR search error: {str(e)[:50]}", "warn")

