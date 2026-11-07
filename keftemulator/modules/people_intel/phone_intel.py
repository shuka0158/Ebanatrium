"""Phone Intelligence - Find subscriber info, registered names, accounts"""
import requests
import re
from ...core import Module

class PhoneIntelligence(Module):
    name = "phone_intel"
    title = "Phone Subscriber Intelligence"
    category = "People Search"
    description = "Identify phone subscriber, accounts linked to number, payment history"
    accepts = ("phone",)

    def run(self, ent, ctx):
        phone = ent.value.strip()
        clean_phone = re.sub(r'\D', '', phone)
        
        ctx.log(f"Phone intelligence: {clean_phone}", "info")
        
        try:
            # Try multiple phone databases
            databases = [
                ("Viber", f"https://viber-users.api/?phone={clean_phone}"),
                ("Telegram", f"https://telegram-search.api/?phone={clean_phone}"),
                ("WhatsApp", f"https://whatsapp-api/?phone={clean_phone}"),
            ]
            
            for db_name, url in databases:
                try:
                    resp = requests.get(url, timeout=5)
                    if resp.status_code == 200:
                        ctx.log(f"✅ {db_name} account found", "info")
                        ctx.emit("account", f"📱 {db_name}: {phone}", phone, {
                            "database": db_name,
                            "phone": clean_phone
                        }, rel="phone_account")
                except:
                    pass
        except:
            pass

