"""Email Breach Checker - Find if email was in data breaches"""
import requests
from ..core import Module

class EmailBreachChecker(Module):
    name = "email_breach_checker"
    title = "Email Breach Check"
    category = "People Search"
    description = "Check if email found in data breaches - returns REAL breach data"
    accepts = ("email_address",)

    def run(self, ent, ctx):
        email = ent.value.strip().lower()
        ctx.log(f"Checking breaches for: {email}", "info")
        
        try:
            # EmailRep API - FREE, returns REAL breach data
            resp = requests.get(
                f"https://emailrep.io/query?email={email}",
                timeout=10,
                headers={"User-Agent": "Keftemulator/1.0"}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                
                if data.get('email'):
                    reputation = data.get('reputation', 0)
                    suspicious = data.get('suspicious', False)
                    num_breaches = data.get('num_breaches', 0)
                    num_exposures = data.get('num_exposures', 0)
                    
                    ctx.log(f"Found: {num_breaches} breaches, {num_exposures} exposures", "info")
                    
                    # EMIT REAL DATA
                    if num_breaches > 0 or num_exposures > 0:
                        ctx.emit("email_address", 
                            f"⚠️ BREACHED: {email} - {num_breaches} breaches, {num_exposures} exposed",
                            email, {
                                "breaches": num_breaches,
                                "exposures": num_exposures,
                                "reputation": reputation,
                                "suspicious": suspicious,
                                "source": "emailrep"
                            }, rel="breach_found")
                    else:
                        ctx.emit("email_address",
                            f"✅ CLEAN: {email} - No breaches found",
                            email, {
                                "breaches": 0,
                                "reputation": reputation,
                                "source": "emailrep"
                            }, rel="no_breach")
        except Exception as e:
            ctx.log(f"Breach check error: {str(e)[:50]}", "warn")

