"""Georgian Property Cadastre - Real property records"""
import requests
from ..core import Module

class GeorgianCadastre(Module):
    name = "georgian_cadastre"
    title = "Georgian Property Cadastre"
    category = "Georgia"
    description = "Search property records - addresses, owners, property details"
    accepts = ("name", "address", "email")

    def run(self, ent, ctx):
        query = ent.value.strip()
        ctx.log(f"Searching cadastre: {query}", "info")
        
        try:
            # Georgian cadastre public API
            resp = requests.get(
                f"https://api.kadastri.ge/api/search",
                params={"q": query},
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0 (Keftemulator)"}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                
                if data.get('properties'):
                    ctx.log(f"✅ Found {len(data['properties'])} properties", "info")
                    
                    for prop in data['properties'][:5]:
                        address = prop.get('address', 'Unknown')
                        owner = prop.get('owner', 'Unknown')
                        area = prop.get('area', 'N/A')
                        
                        ctx.emit("location",
                            f"🏠 {address} - Owner: {owner}",
                            query, {
                                "address": address,
                                "owner": owner,
                                "area_m2": area,
                                "cadastre_id": prop.get('cadastre_id'),
                                "property_type": prop.get('type'),
                                "registration_date": prop.get('reg_date'),
                                "source": "cadastre_georgia"
                            }, rel="property_georgia")
        except Exception as e:
            ctx.log(f"Cadastre error: {str(e)[:50]}", "warn")

