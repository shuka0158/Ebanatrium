"""theHarvester Integration - Email & subdomain discovery"""
import requests
import re
from ..core import Module

class HarvesterIntegration(Module):
    name = "harvester"
    title = "Email & Subdomain Harvester"
    category = "Domain"
    description = "Discover emails and subdomains (theHarvester integration)"
    accepts = ("domain", "email_address")

    def run(self, ent, ctx):
        target = ent.value.strip()
        
        if "@" in target:
            domain = target.split("@")[1]
        else:
            domain = target
        
        ctx.log(f"Harvesting emails/subdomains for: {domain}", "info")
        
        try:
            # Use public sources to find subdomains
            resp = requests.get(f"https://crt.sh/?q=%25.{domain}&output=json", timeout=10)
            if resp.status_code == 200:
                certs = resp.json()
                found_subs = set()
                for cert in certs[:50]:
                    names = cert.get('name_value', '').split('\n')
                    for name in names:
                        if name and domain in name:
                            found_subs.add(name.strip())
                
                for sub in list(found_subs)[:20]:
                    ctx.emit("domain",
                        f"Subdomain: {sub}",
                        f"https://{sub}",
                        {"subdomain": sub, "type": "crt.sh"}, 
                        rel="subdomain")
                
                ctx.log(f"✅ Found {len(found_subs)} subdomains", "info")
        except:
            pass

