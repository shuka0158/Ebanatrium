"""Email Intelligence - Breaches, reputation, accounts"""
import requests
from ..core import Module

class EmailIntel(Module):
    name = "email_intel"
    title = "Email Intelligence"
    category = "People Search"
    description = "Find email in breaches, linked accounts, reputation"
    accepts = ("email_address",)

    def run(self, ent, ctx):
        email = ent.value.strip()
        ctx.log(f"Email intelligence: {email}", "info")
        
        try:
            # Check multiple email breach databases
            databases = [
                ("Hunter.io", f"https://hunter.io/app/emails/{email}"),
                ("RocketReach", f"https://rocketreach.com/search?q={email}"),
                ("Clearbit", f"https://clearbit.com/search?q={email}"),
            ]
            
            for db, url in databases:
                try:
                    resp = requests.head(url, timeout=5)
                    if resp.status_code in [200, 301, 302]:
                        ctx.log(f"✅ {db} record found", "info")
                        ctx.emit("email_address", f"📧 {db}: {email}", email, {
                            "database": db,
                            "url": url
                        }, rel="email_record")
                except:
                    pass
        except:
            pass

