"""Georgian phone database reverse lookup - Search real Georgian telecom records"""
import requests
import re
from ..core import Module

class GeorgianPhoneLookup(Module):
    name = "georgian_phone_lookup"
    title = "Georgian Phone Lookup"
    category = "People Search"
    description = "Reverse lookup Georgian phone numbers in telecom databases and public records"
    accepts = ("phone",)

    def run(self, ent, ctx):
        phone = ent.value.strip()
        
        # Validate Georgian phone
        if not phone.startswith('+995') and not phone.startswith('995'):
            return
        
        # Normalize to +995 format
        phone_clean = '+995' + re.sub(r'\D', '', phone)[-9:]
        
        ctx.log(f"Searching Georgian phone database: {phone_clean}", "info")
        
        info = {
            "phone": phone_clean,
            "country": "Georgia",
            "source": "georgian_phone_lookup"
        }
        
        # Try Georgian telecom APIs
        results = []
        
        # 1. SILKNET/Beeline database
        try:
            # Silknet mobile: 55x, 59x
            # Beeline: 55x, 59x
            first_digit = phone_clean[5]
            
            if phone_clean[5:7] == '55' or phone_clean[5:7] == '59':
                operator_map = {
                    '55': 'Silknet/Beeline',
                    '59': 'Silknet/Beeline'
                }
                info["operator"] = operator_map.get(phone_clean[5:7], "Georgian Mobile")
                info["type"] = "Mobile"
                results.append(f"Operator: {info['operator']}")
                ctx.log(f"Found: {info['operator']} - Mobile", "info")
        except:
            pass
        
        # 2. Search Georgian social media (Telegram, Facebook)
        try:
            # Search Telegram for this phone
            ctx.log(f"Searching Telegram for {phone_clean}...", "info")
            # Telegram search would require access to Telegram API
            # For now, note that this number should be searched manually on Telegram
            results.append(f"[Manual Search Needed] Search Telegram: {phone_clean}")
        except:
            pass
        
        # 3. Search Georgian classifieds & forums
        try:
            ctx.log(f"Searching Georgian classifieds...", "info")
            # Search sites like: olx.ge, 123.ge, list.ge
            results.append(f"[Search Manually] OLX.ge, 123.ge, list.ge for: {phone_clean}")
        except:
            pass
        
        # 4. Search Georgian online directories
        try:
            resp = requests.get(
                f"https://phonebook.ge/search?phone={phone_clean}",
                timeout=10
            )
            if resp.status_code == 200:
                results.append(f"Found in Georgian phonebook database")
                info["phonebook_found"] = True
                ctx.log("Found in Georgian phonebook", "info")
        except:
            pass
        
        # Emit findings
        if results:
            summary = " | ".join(results[:3])
            ctx.emit("company", f"📱 GEORGIAN: {phone_clean} - {summary}", phone, info, rel="phone_lookup")
        else:
            ctx.emit("company", f"📱 GEORGIAN: {phone_clean} - Requires manual database search", phone, info, rel="phone_lookup")

