"""Username Patterns - Generate and search variations"""
import requests
from ..core import Module

class UsernamePatterns(Module):
    name = "username_patterns"
    title = "Username Variations"
    category = "People Search"
    description = "Search for username variations and patterns"
    accepts = ("username",)

    def run(self, ent, ctx):
        username = ent.value.strip().lower()
        
        # Generate variations
        variations = [
            username,
            username.replace("0", "o").replace("1", "i").replace("3", "e"),
            username + "123",
            username + "_",
            username.replace("_", ""),
            username.replace("-", ""),
        ]
        
        # Check Pastebin for mentions
        for var in variations[:3]:
            try:
                resp = requests.get(f"https://www.google.com/search?q=site:pastebin.com {var}", timeout=5)
                if resp.status_code == 200 and len(resp.text) > 100:
                    ctx.emit("link",
                        f"Pastebin mention: {var}",
                        f"https://www.pastebin.com/search/{var}",
                        {"variation": var}, rel="pastebin_mention")
            except:
                pass
        
        ctx.log(f"Checked {len(variations)} variations", "info")

