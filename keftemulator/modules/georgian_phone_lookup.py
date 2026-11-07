"""Georgian Phone Lookup - Identify person by phone number"""
import requests
import re
from ..core import Module

class GeorgianPhoneLookup(Module):
    name = "georgian_phone"
    title = "Georgian Phone Identifier"
    category = "Georgia"
    description = "Identify person by Georgian phone number - reverse lookup"
    accepts = ("phone",)

    def run(self, ent, ctx):
        phone = ent.value.strip()
        clean = re.sub(r'\D', '', phone)
        
        # Check if Georgian number (595, 568, 579, etc.)
        if not clean.startswith('995') and len(clean) < 12:
            clean = '995' + clean
        
        ctx.log(f"Georgian phone lookup: {clean}", "info")
        
        try:
            # Georgian phone identification API
            resp = requests.get(
                f"https://phonelookup.georgia/api/identify",
                params={"phone": clean},
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0 (Keftemulator)"}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                
                if data.get('person'):
                    person = data['person']
                    name = person.get('name', 'Unknown')
                    carrier = data.get('carrier', 'Unknown')
                    
                    ctx.log(f"✅ Found: {name}", "info")
                    
                    ctx.emit("name",
                        f"👤 {name} ({carrier}) - {phone}",
                        phone, {
                            "name": name,
                            "phone": clean,
                            "carrier": carrier,
                            "region": data.get('region'),
                            "city": data.get('city'),
                            "source": "georgian_phone"
                        }, rel="person_georgia")
        except Exception as e:
            ctx.log(f"Phone lookup error: {str(e)[:50]}", "warn")

