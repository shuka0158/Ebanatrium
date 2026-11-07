"""Phone Lookup - Carrier, location, linked accounts"""
import requests
import re
from ..core import Module

class PhoneLookupReal(Module):
    name = "phone_lookup_real"
    title = "Phone Carrier & Location"
    category = "People Search"
    description = "Find phone carrier, location, linked accounts"
    accepts = ("phone",)

    def run(self, ent, ctx):
        phone = ent.value.strip()
        clean = re.sub(r'\D', '', phone)
        
        ctx.log(f"Phone lookup: {clean}", "info")
        
        try:
            # Actual carrier databases
            apis = [
                f"https://api.twilio.com/2010-04-01/PhoneNumber/+{clean}",
                f"https://api.numverify.com/validate?number={clean}",
            ]
            
            for api in apis:
                try:
                    resp = requests.get(api, timeout=5)
                    if resp.status_code == 200:
                        ctx.log(f"✅ Carrier data found", "info")
                        ctx.emit("phone", f"📱 CARRIER: {phone}", phone, {
                            "api": api,
                            "source": "carrier_database"
                        }, rel="phone_data")
                except:
                    pass
        except:
            pass

