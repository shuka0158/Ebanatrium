"""Breach Search - Check if username in breaches"""
import requests
from ..core import Module

class BreachSearch(Module):
    name = "breach_search"
    title = "Breach Database Search"
    category = "Security"
    description = "Search if username found in data breaches"
    accepts = ("username", "email_address")

    def run(self, ent, ctx):
        query = ent.value.strip().lower()
        
        # Try multiple breach databases
        databases = [
            ("LeakCheck", f"https://leakcheck.net/api/public?query={query}"),
        ]
        
        for db_name, url in databases:
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('found'):
                        ctx.emit("breach",
                            f"Breach: {query} found in {db_name}",
                            url,
                            data, rel="breach_found")
            except:
                pass

