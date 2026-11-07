"""Facebook & Social Media - Find accounts and public profiles"""
import requests
from ..core import Module

class FacebookFinder(Module):
    name = "facebook_finder"
    title = "Facebook & Social Media"
    category = "People Search"
    description = "Find Facebook, Instagram, Twitter profiles"
    accepts = ("name", "email", "phone")

    def run(self, ent, ctx):
        target = ent.value.strip()
        ctx.log(f"Searching social media: {target}", "info")
        
        try:
            # Check multiple platforms
            platforms = {
                "Facebook": f"https://www.facebook.com/public/{target}",
                "Instagram": f"https://www.instagram.com/{target}/",
                "Twitter": f"https://twitter.com/search?q={target}",
                "TikTok": f"https://www.tiktok.com/search?q={target}"
            }
            
            for platform, url in platforms.items():
                resp = requests.head(url, timeout=5)
                if resp.status_code in [200, 301, 302]:
                    ctx.log(f"✅ {platform} found", "info")
                    ctx.emit("profile", f"📱 {platform}: {target}", target, {
                        "platform": platform,
                        "url": url,
                        "source": "social_media"
                    }, rel="social_account")
        except:
            pass

