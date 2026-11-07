"""Georgian NAPR Registry - Real business and person records"""
import requests
import re
from ..core import Module

class GeorgianNAPRSearch(Module):
    name = "georgian_napr"
    title = "Georgian Business Registry (NAPR)"
    category = "Georgia"
    description = "Search NAPR for company ownership, directors, shareholders with real Georgian data"
    accepts = ("name", "email", "company")

    def run(self, ent, ctx):
        query = ent.value.strip()
        ctx.log(f"Searching NAPR: {query}", "info")
        
        try:
            # NAPR public search API
            search_url = f"https://napr.eregs.go.ge/api/search?q={query}"
            resp = requests.get(search_url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Keftemulator)"
            })
            
            if resp.status_code == 200:
                data = resp.json()
                
                if data.get('results'):
                    ctx.log(f"✅ Found {len(data['results'])} NAPR records", "info")
                    
                    for result in data['results'][:5]:
                        company = result.get('company_name', query)
                        tin = result.get('tin', 'N/A')
                        director = result.get('director', 'Unknown')
                        
                        ctx.emit("company",
                            f"🏢 {company} (TIN: {tin}) - Director: {director}",
                            query, {
                                "company": company,
                                "tin": tin,
                                "director": director,
                                "status": result.get('status'),
                                "type": result.get('type'),
                                "registration_date": result.get('reg_date'),
                                "source": "napr_georgia"
                            }, rel="napr_record")
                else:
                    ctx.log("No NAPR results", "info")
        except Exception as e:
            ctx.log(f"NAPR error: {str(e)[:50]}", "warn")

