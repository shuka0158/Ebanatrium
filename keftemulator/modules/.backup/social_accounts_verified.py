"""Social Accounts - ONLY verified real accounts"""
import requests
from ..core import Module

class SocialAccountsVerified(Module):
    name = "social_accounts_verified"
    title = "Social Media (Verified Only)"
    category = "People Search"
    description = "Find REAL accounts only - verifies each one exists"
    accepts = ("username", "name")

    def run(self, ent, ctx):
        username = ent.value.strip().lower()
        ctx.log(f"Searching real accounts for: {username}", "info")
        
        found_count = 0
        
        # ONLY these platforms, with proper verification
        platforms = [
            ("GitHub", f"https://github.com/{username}"),
            ("Twitter", f"https://twitter.com/{username}"),
            ("Reddit", f"https://reddit.com/u/{username}"),
        ]
        
        for platform, url in platforms:
            try:
                # VERIFY it actually exists
                resp = requests.head(url, timeout=5, allow_redirects=True)
                
                # ONLY emit if HTTP 200 (account exists)
                if resp.status_code == 200:
                    found_count += 1
                    ctx.log(f"✅ VERIFIED: {platform} - {username}", "info")
                    
                    ctx.emit("account",
                        f"{platform}: {username}",
                        url,
                        {
                            "platform": platform,
                            "username": username,
                            "url": url,
                            "verified": True,
                            "status_code": resp.status_code
                        }, rel="verified_account")
                else:
                    # NOT found - don't emit anything
                    ctx.log(f"❌ NOT FOUND: {platform} - {username} (HTTP {resp.status_code})", "info")
                    
            except Exception as e:
                # Error checking - don't emit
                ctx.log(f"Error checking {platform}: {str(e)[:30]}", "info")
        
        # Log result
        if found_count == 0:
            ctx.log(f"No accounts found for: {username}", "info")

