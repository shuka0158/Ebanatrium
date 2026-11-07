"""Censys - Search certificate and IP data"""
import requests
from ..core import Module

class CensysSearch(Module):
    name = "censys_search"
    title = "Censys Certificate Search"
    category = "Domain Intelligence"
    description = "Search Censys.io for SSL certificates and IP data"
    accepts = ("domain", "ip_address", "email")

    def run(self, ent, ctx):
        query = ent.value.strip()
        
        ctx.log(f"Censys search: {query}", "info")
        
        try:
            # Censys free search
            resp = requests.get(
                f"https://censys.io/ipv4?q={query}",
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            if resp.status_code == 200:
                ctx.log("Censys: Data available", "info")
                ctx.emit("company", f"🔐 Censys Results", query, {
                    "query": query,
                    "source": "censys",
                    "url": f"https://censys.io/ipv4?q={query}"
                }, rel="censys_data")
                
        except Exception as e:
            ctx.log(f"Censys error: {str(e)[:50]}", "warn")

