"""Shodan - Search for exposed internet-connected devices and data"""
import requests
from ..core import Module

class ShodanSearch(Module):
    name = "shodan_search"
    title = "Shodan Internet Search"
    category = "Threat Detection"
    description = "Search Shodan.io for exposed devices, services, and data"
    accepts = ("ip_address", "domain", "company")

    def run(self, ent, ctx):
        query = ent.value.strip()
        
        ctx.log(f"Shodan search: {query}", "info")
        
        try:
            # Shodan free search (no API key needed for basic HTML search)
            resp = requests.get(
                f"https://www.shodan.io/search?query={query}",
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            if resp.status_code == 200:
                # Check if results found
                if "No results" not in resp.text and resp.text:
                    ctx.log(f"Shodan: Found results for {query}", "info")
                    ctx.emit("company", f"🔍 Shodan Results", query, {
                        "query": query,
                        "source": "shodan",
                        "url": f"https://www.shodan.io/search?query={query}"
                    }, rel="shodan_search")
                else:
                    ctx.log("Shodan: No results", "info")
                    
        except Exception as e:
            ctx.log(f"Shodan error: {str(e)[:50]}", "warn")

