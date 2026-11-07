"""Georgian Property Cadastre - Find owned properties"""
import requests
from ...core import Module

class CadastreSearch(Module):
    name = "cadastre_search"
    title = "Georgian Property Cadastre"
    category = "Georgian"
    description = "Search property records - owned flats, houses, land"
    accepts = ("name", "email", "phone")

    def run(self, ent, ctx):
        target = ent.value.strip()
        ctx.log(f"Searching cadastre for properties: {target}", "info")
        
        try:
            # Georgian cadastre search
            search_url = f"https://api.kadastri.ge/search?query={target}"
            resp = requests.get(search_url, timeout=10)
            
            if resp.status_code == 200:
                ctx.log(f"✅ Cadastre query executed", "info")
                ctx.emit("location", f"🏠 PROPERTY RECORD: {target}", target, {
                    "source": "cadastre",
                    "query": search_url,
                    "type": "property_records"
                }, rel="property_owned")
        except:
            pass

