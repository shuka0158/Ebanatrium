"""Email - ONLY verified real data"""
import requests
from ..core import Module

class EmailVerified(Module):
    name = "email_verified"
    title = "Email (Real Data Only)"
    category = "Email"
    description = "Get REAL email data - only if data exists"
    accepts = ("email_address",)

    def run(self, ent, ctx):
        email = ent.value.strip().lower()
        ctx.log(f"Verifying email: {email}", "info")
        
        try:
            # EmailRep - returns REAL data
            resp = requests.get(f"https://emailrep.io/query?email={email}", timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                
                # ONLY emit if we have REAL data
                if data.get('email'):
                    breaches = data.get('num_breaches', 0)
                    exposures = data.get('num_exposures', 0)
                    reputation = data.get('reputation', 0)
                    
                    # Only emit if there's actual data
                    if breaches > 0 or exposures > 0:
                        ctx.emit("breach",
                            f"Email Breach: {email} - {breaches} breaches, {exposures} exposed",
                            email,
                            {
                                "email": email,
                                "breaches": breaches,
                                "exposures": exposures,
                                "reputation": reputation,
                                "verified": True
                            }, rel="verified_breach")
                        ctx.log(f"✅ VERIFIED: Email in breaches - {breaches} breaches", "info")
                    else:
                        ctx.log(f"Email clean - no breaches found", "info")
        except Exception as e:
            ctx.log(f"Email verification error: {str(e)[:30]}", "warn")

