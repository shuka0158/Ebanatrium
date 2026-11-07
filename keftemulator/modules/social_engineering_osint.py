"""Social Engineering OSINT - Extract personal data from public sources"""
import requests
import re
from ..core import Module

class SocialEngineeringOSINT(Module):
    name = "social_engineering_osint"
    title = "Social Engineering Intelligence"
    category = "People Search"
    description = "Find personal details through social engineering sources"
    accepts = ("name", "email_address")

    def run(self, ent, ctx):
        target = ent.value.strip()
        
        ctx.log(f"Social engineering search: {target}", "info")
        
        # Information gathering sources
        sources = [
            ("LinkedIn", f"https://www.linkedin.com/search/results/all/?keywords={target}"),
            ("Facebook", f"https://www.facebook.com/search/people/?q={target}"),
            ("Twitter", f"https://twitter.com/search?q={target}"),
            ("Instagram", f"https://www.instagram.com/explore/tags/{target.replace(' ', '')}"),
            ("TikTok", f"https://www.tiktok.com/search?q={target}"),
            ("Quora", f"https://www.quora.com/search?q={target}"),
            ("Medium", f"https://medium.com/search?q={target}"),
            ("Mastodon", f"https://mastodon.social/search?q={target}"),
        ]
        
        for platform, url in sources:
            ctx.emit("link",
                f"Social Profile: {platform}",
                url,
                {"platform": platform, "target": target},
                rel="social_profile")
            ctx.log(f"✅ {platform} - search available", "info")

