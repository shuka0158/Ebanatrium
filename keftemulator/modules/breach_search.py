"""Breach and leak database search - Find if info was exposed in data breaches"""
import requests
from ..core import Module

class BreachSearch(Module):
    name = "breach_search"
    title = "Data Breach Search"
    category = "People Search"
    description = "Search if phone/email appears in public data breaches and leaks"
    accepts = ("phone", "email")

    def run(self, ent, ctx):
        query = ent.value.strip()
        
        ctx.log(f"Searching breaches for: {query}", "info")
        
        # Check Have I Been Pwned
        try:
            resp = requests.get(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{query}",
                timeout=10,
                headers={"User-Agent": "KeftOSINT"}
            )
            
            if resp.status_code == 200:
                breaches = resp.json()
                for breach in breaches:
                    data = {
                        "breach": breach.get('Name', 'Unknown'),
                        "date": breach.get('BreachDate', 'Unknown'),
                        "compromised_data": breach.get('DataClasses', []),
                        "source": "HIBP"
                    }
                    
                    ctx.log(f"BREACH FOUND: {breach.get('Name')}", "warn")
                    ctx.emit("company", f"🚨 DATA BREACH: {breach.get('Name')}", query, data, rel="breach")
                    
        except requests.exceptions.HTTPError:
            ctx.log("No breaches found for this email", "info")
        except Exception as e:
            ctx.log(f"Breach search error: {str(e)[:50]}", "warn")

