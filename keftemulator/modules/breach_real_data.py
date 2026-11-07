"""Breach Real Data - Returns actual breach information"""
import requests
from ..core import Module

class BreachRealData(Module):
    name = "breach_real_data"
    title = "Breach Database - Real Data"
    category = "Security"
    description = "Find REAL breach data: compromised emails, databases, years"
    accepts = ("email_address", "username")

    def run(self, ent, ctx):
        query = ent.value.strip().lower()
        ctx.log(f"Searching breaches: {query}", "info")
        
        try:
            # HaveIBeenPwned API (free, no auth needed)
            if "@" in query:
                # Email search
                url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{query}"
                headers = {'User-Agent': 'OSINT'}
                
                try:
                    resp = requests.get(url, headers=headers, timeout=10)
                    
                    if resp.status_code == 200:
                        breaches = resp.json()
                        ctx.log(f"✅ Found {len(breaches)} breaches", "warn")
                        
                        for breach in breaches[:20]:
                            title = breach.get('Title', 'Unknown')
                            date = breach.get('BreachDate', 'Unknown')
                            count = breach.get('PwnCount', 0)
                            
                            label = f"BREACH: {title} ({date}) - {count} records"
                            
                            ctx.emit("link",
                                label,
                                title,
                                {
                                    "breach_name": title,
                                    "date": date,
                                    "count": count,
                                    "data_classes": breach.get('DataClasses', [])
                                },
                                rel="breach_data")
                    elif resp.status_code == 404:
                        ctx.log(f"No breaches found for: {query}", "info")
                except:
                    pass
            
            # Try alternative breach databases
            try:
                breachdb_url = f"https://leakcheck.net/api/v2/search?q={query}"
                breachdb_resp = requests.get(breachdb_url, timeout=5)
                if breachdb_resp.status_code == 200:
                    breach_data = breachdb_resp.json()
                    if breach_data.get('result'):
                        for result in breach_data['result'][:10]:
                            ctx.emit("link",
                                f"Leak: {result.get('source', 'Unknown')}",
                                result.get('data', ''),
                                result,
                                rel="leak_data")
            except:
                pass
                
        except Exception as e:
            ctx.log(f"Breach search error: {str(e)[:50]}", "warn")

