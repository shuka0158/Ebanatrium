"""Email Real Data - Return actual email intelligence"""
import requests
from ..core import Module

class EmailRealData(Module):
    name = "email_real_data"
    title = "Email Intelligence (Real Data)"
    category = "Email"
    description = "Get real email data - breaches, reputation, validation"
    accepts = ("email_address",)

    def run(self, ent, ctx):
        email = ent.value.strip().lower()
        ctx.log(f"Email intelligence: {email}", "info")
        
        try:
            # EmailRep - REAL breach data
            resp = requests.get(f"https://emailrep.io/query?email={email}", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                
                if data.get('email'):
                    # EMIT REAL DATA
                    breaches = data.get('num_breaches', 0)
                    exposures = data.get('num_exposures', 0)
                    reputation = data.get('reputation', 0)
                    
                    if breaches > 0:
                        ctx.emit("breach",
                            f"🚨 BREACHED: {email} ({breaches} breaches, {exposures} exposed)",
                            email, {
                                "breaches": breaches,
                                "exposures": exposures,
                                "reputation": reputation,
                                "source": "emailrep"
                            }, rel="email_breach")
                    else:
                        ctx.emit("email_address",
                            f"✅ Email: {email} - Clean (rep: {reputation}/100)",
                            email, {
                                "email": email,
                                "reputation": reputation,
                                "source": "emailrep"
                            }, rel="email_data")
        except:
            pass

