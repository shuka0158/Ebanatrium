"""Leaked Database Search - Search for exposed personal data"""
import requests
from ..core import Module

class LeakedDatabaseDeep(Module):
    name = "leaked_database_deep"
    title = "Leaked Database Deep Search"
    category = "Leaks"
    description = "Search leaked/breached databases for exposed personal information"
    accepts = ("email_address", "name", "phone")

    def run(self, ent, ctx):
        query = ent.value.strip()
        
        ctx.log(f"Searching leaked databases: {query}", "info")
        
        # Free leaked database sources
        sources = [
            ("IntelligenceX", f"https://intelx.io/?s={query}"),
            ("LeakCheck", f"https://leakcheck.net/search?query={query}"),
            ("HaveIBeenPwned", f"https://haveibeenpwned.com/search?query={query}"),
            ("Dehashed (Free)", f"https://dehashed.com/search?query={query}"),
            ("BreachDirectory", f"https://breachdirectory.org/?s={query}"),
            ("Weleakinfo", f"https://weleakinfo.com/search/{query}"),
        ]
        
        for source, url in sources:
            try:
                resp = requests.head(url, timeout=10)
                if resp.status_code in [200, 301, 302]:
                    ctx.emit("leak",
                        f"Breach Database: {source}",
                        url,
                        {"source": source, "query": query},
                        rel="breach_database")
                    ctx.log(f"✅ {source} - checking", "info")
            except:
                pass

