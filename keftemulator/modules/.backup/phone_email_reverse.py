"""Phone & Email Reverse Lookup - Deep intelligence from free sources"""
import requests
import re
from ..core import Module

class PhoneEmailReverse(Module):
    name = "phone_email_reverse"
    title = "Phone & Email Reverse Lookup"
    category = "People Search"
    description = "Reverse lookup phone/email to find names, addresses, co-residents"
    accepts = ("phone", "email_address")

    def run(self, ent, ctx):
        query = ent.value.strip()
        
        # Phone number extraction
        phone_match = re.findall(r'\d{10}|\d{3}-\d{3}-\d{4}', query)
        if phone_match:
            phone = phone_match[0].replace('-', '')
            ctx.log(f"Phone reverse lookup: {phone}", "info")
            
            # Free phone lookup sources
            sources = [
                ("TrueCaller", f"https://www.truecaller.com/search/{phone}"),
                ("Sync.me", f"https://www.sync.me/phone/{phone}"),
                ("WhitePages (Free)", f"https://www.whitepages.com/phone/{phone}"),
                ("Reverse Phone", f"https://www.reversephonecheck.com/{phone}"),
                ("Phone Validator", f"https://phonevalidator.com/{phone}"),
            ]
            
            for source, url in sources:
                try:
                    resp = requests.head(url, timeout=5)
                    if resp.status_code == 200:
                        ctx.emit("link",
                            f"Phone Lookup: {source}",
                            url,
                            {"phone": phone, "source": source},
                            rel="phone_lookup")
                        ctx.log(f"✅ {source} - found", "info")
                except:
                    pass
        
        # Email reverse lookup
        if "@" in query:
            email = query
            ctx.log(f"Email reverse lookup: {email}", "info")
            
            sources = [
                ("Hunter.io (Free)", f"https://hunter.io/search?domain={email.split('@')[1]}"),
                ("RocketReach", f"https://rocketreach.com/search?q={email}"),
                ("Clearbit", f"https://clearbit.com/search?q={email}"),
                ("Holehe", f"https://www.holehe.me/search?email={email}"),
                ("Email Finder", f"https://emailfinder.co/search/{email}"),
            ]
            
            for source, url in sources:
                try:
                    resp = requests.head(url, timeout=5)
                    if resp.status_code == 200:
                        ctx.emit("link",
                            f"Email Lookup: {source}",
                            url,
                            {"email": email, "source": source},
                            rel="email_lookup")
                except:
                    pass

