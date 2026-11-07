"""Social Accounts Real - Find person's actual accounts"""
import requests
from ..core import Module

class SocialAccountsReal(Module):
    name = "social_accounts_real"
    title = "Social Media Accounts (Real)"
    category = "People Search"
    description = "Find person's actual social media profiles"
    accepts = ("username", "name", "email_address")

    def run(self, ent, ctx):
        query = ent.value.strip().lower()
        
        # Check real platforms
        platforms = [
            ("Twitter", f"https://twitter.com/{query}", "twitter"),
            ("Instagram", f"https://instagram.com/{query}", "instagram"),
            ("Reddit", f"https://reddit.com/u/{query}", "reddit"),
            ("GitHub", f"https://github.com/{query}", "github"),
            ("LinkedIn", f"https://linkedin.com/in/{query}", "linkedin"),
            ("TikTok", f"https://tiktok.com/@{query}", "tiktok"),
            ("Twitch", f"https://twitch.tv/{query}", "twitch"),
        ]
        
        for platform, url, key in platforms:
            try:
                resp = requests.head(url, timeout=5, allow_redirects=True)
                if resp.status_code == 200:
                    ctx.emit("account",
                        f"👥 {platform}: {query}",
                        url,
                        {
                            "platform": platform,
                            "username": query,
                            "url": url,
                            "found": True,
                            "source": "social_search"
                        }, rel="social_account")
            except:
                pass

