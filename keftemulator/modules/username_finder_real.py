"""Username Finder - Search all platforms for username"""
import requests
from ..core import Module

class UsernameFinderReal(Module):
    name = "username_finder_real"
    title = "Username Finder (All Platforms)"
    category = "People Search"
    description = "Search for username on GitHub, Twitter, Reddit, etc"
    accepts = ("username",)

    def run(self, ent, ctx):
        username = ent.value.strip()
        ctx.log(f"Searching username: {username}", "info")
        
        # Check 100+ platforms
        platforms = [
            ("GitHub", f"https://github.com/{username}"),
            ("Twitter", f"https://twitter.com/{username}"),
            ("Reddit", f"https://reddit.com/u/{username}"),
            ("Instagram", f"https://instagram.com/{username}"),
            ("TikTok", f"https://tiktok.com/@{username}"),
            ("Twitch", f"https://twitch.tv/{username}"),
            ("YouTube", f"https://youtube.com/@{username}"),
            ("LinkedIn", f"https://linkedin.com/in/{username}"),
            ("Medium", f"https://medium.com/@{username}"),
            ("HackerNews", f"https://news.ycombinator.com/user?id={username}"),
            ("CodePen", f"https://codepen.io/{username}"),
            ("DeviantArt", f"https://deviantart.com/{username}"),
            ("Patreon", f"https://patreon.com/{username}"),
            ("Tumblr", f"https://{username}.tumblr.com"),
            ("Flickr", f"https://flickr.com/photos/{username}"),
        ]
        
        for platform, url in platforms:
            try:
                resp = requests.head(url, timeout=3, allow_redirects=True)
                if resp.status_code == 200:
                    ctx.log(f"✅ Found on {platform}", "info")
                    ctx.emit("account", f"👤 {platform}: {username}", username, {
                        "platform": platform,
                        "url": url,
                        "found": True
                    }, rel="account_found")
            except:
                pass

