"""Dark Web Search - Search dark web and pastes (TorBot integration)"""
import requests
from ..core import Module

class DarkWebSearch(Module):
    name = "darkweb_search"
    title = "Dark Web & Paste Search"
    category = "Leaks"
    description = "Search dark web, pastes, and leak databases"
    accepts = ("email_address", "username", "name")

    def run(self, ent, ctx):
        query = ent.value.strip()
        
        try:
            # IntelligenceX API (free tier)
            resp = requests.get(
                f"https://public.intelx.io/api/1/phonenumbersearch?p=0&s={query}",
                timeout=10
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get('selectors'):
                    for item in data['selectors'][:5]:
                        ctx.emit("leak",
                            f"Leak found: {item.get('selectortext', query)}",
                            f"https://intelx.io",
                            item, rel="leak_found")
        except:
            pass

