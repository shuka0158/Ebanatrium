"""Email Generator - Generate possible emails from username"""
import requests
from ..core import Module

class EmailGenerator(Module):
    name = "email_generator"
    title = "Email Permutations"
    category = "Email"
    description = "Generate and verify possible emails from username"
    accepts = ("username",)

    def run(self, ent, ctx):
        username = ent.value.strip().lower()
        
        domains = ["gmail.com", "yahoo.com", "outlook.com", "protonmail.com", "mail.com"]
        found = 0
        
        for domain in domains:
            email = f"{username}@{domain}"
            
            try:
                # Check with emailrep
                resp = requests.get(f"https://emailrep.io/query?email={email}", timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('email'):
                        breaches = data.get('num_breaches', 0)
                        if breaches > 0:
                            found += 1
                            ctx.emit("email_address",
                                f"Email: {email} ({breaches} breaches)",
                                email,
                                data, rel="email_found")
            except:
                pass
        
        ctx.log(f"Email permutation search: found {found}", "info")

