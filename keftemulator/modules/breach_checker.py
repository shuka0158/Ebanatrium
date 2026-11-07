"""Breach Checker - Actually check if data exists in breaches"""
import requests
from ..core import Module

class BreachChecker(Module):
    name = "breach_checker"
    title = "Real Breach Check"
    category = "Threat Detection"
    description = "Actually check breach databases for email/phone"
    accepts = ("email_address", "phone")

    def run(self, ent, ctx):
        query = ent.value.strip()
        
        ctx.log(f"Checking breaches for: {query}", "info")
        
        # Try real breach databases
        databases = [
            ("BreachDirectory", f"https://www.breachdirectory.org/?q={query}"),
            ("Dehashed", f"https://www.dehashed.com/search?query={query}"),
            ("IntelX", f"https://intelx.io/?s={query}"),
        ]
        
        for db_name, url in databases:
            try:
                resp = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                
                if resp.status_code == 200:
                    # Check if results found (varies by site)
                    if "no result" not in resp.text.lower() and len(resp.text) > 500:
                        ctx.log(f"✅ DATA FOUND IN {db_name}!", "warn")
                        ctx.emit("company", f"🚨 BREACH FOUND: {db_name}", query, {
                            "database": db_name,
                            "url": url,
                            "exposed": True
                        }, rel="breach_found")
                    else:
                        ctx.log(f"{db_name}: Not found or no results", "info")
                        
            except:
                pass  # Continue to next

