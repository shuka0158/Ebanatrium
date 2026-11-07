"""Domain WHOIS - Owner information, registrar, dates - REAL data"""
import requests
import re
from ..core import Module

class DomainWHOISReal(Module):
    name = "domain_whois_real"
    title = "Domain WHOIS Lookup"
    category = "Domain"
    description = "Get domain owner, registrar, dates - returns REAL WHOIS data"
    accepts = ("url", "domain")

    def run(self, ent, ctx):
        url_or_domain = ent.value.strip()
        
        # Extract domain
        domain = re.sub(r'https?://|/.*', '', url_or_domain)
        domain = re.sub(r'^www\.', '', domain)
        
        ctx.log(f"WHOIS lookup: {domain}", "info")
        
        try:
            # WHOIS.API - FREE tier, returns REAL domain data
            resp = requests.get(
                f"https://www.whoisjson.com/api/v1/whois?domain={domain}",
                timeout=10
            )
            
            if resp.status_code == 200:
                data = resp.json()
                
                if data.get('registrar'):
                    ctx.log(f"✅ WHOIS found for {domain}", "info")
                    
                    # EMIT REAL WHOIS data
                    ctx.emit("domain",
                        f"🔗 {domain} - {data.get('registrar', 'Unknown')}",
                        domain, {
                            "domain": domain,
                            "registrar": data.get('registrar'),
                            "registrant": data.get('registrant_name'),
                            "registrant_email": data.get('registrant_email'),
                            "registrant_org": data.get('registrant_organization'),
                            "created": data.get('created_date'),
                            "expires": data.get('expiration_date'),
                            "updated": data.get('updated_date'),
                            "status": data.get('domain_status'),
                            "source": "whoisjson"
                        }, rel="whois_data")
                        
        except Exception as e:
            ctx.log(f"WHOIS error: {str(e)[:50]}", "warn")

