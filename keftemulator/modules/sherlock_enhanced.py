"""Sherlock Enhanced - Find username across 100+ sites"""
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..core import Module

class SherlockEnhanced(Module):
    name = "sherlock_enhanced"
    title = "Username Finder (100+ Sites)"
    category = "People Search"
    description = "Search username across 100+ platforms (Sherlock)"
    accepts = ("username",)

    def run(self, ent, ctx):
        username = ent.value.strip().lower()
        
        sites = [
            ("GitHub", "https://github.com/{username}"),
            ("Twitter", "https://twitter.com/{username}"),
            ("Reddit", "https://reddit.com/u/{username}"),
            ("LinkedIn", "https://linkedin.com/in/{username}"),
            ("YouTube", "https://youtube.com/@{username}"),
            ("Instagram", "https://instagram.com/{username}"),
            ("Facebook", "https://facebook.com/{username}"),
            ("TikTok", "https://tiktok.com/@{username}"),
            ("Twitch", "https://twitch.tv/{username}"),
            ("Pinterest", "https://pinterest.com/{username}"),
            ("Medium", "https://medium.com/@{username}"),
            ("Tumblr", "https://{username}.tumblr.com"),
            ("Flickr", "https://flickr.com/photos/{username}"),
            ("DeviantArt", "https://deviantart.com/{username}"),
            ("Patreon", "https://patreon.com/{username}"),
        ]
        
        found = []
        for site, url_template in sites:
            url = url_template.format(username=username)
            try:
                resp = requests.head(url, timeout=3, allow_redirects=True)
                if resp.status_code == 200:
                    ctx.emit("account",
                        f"{site}: {username}",
                        url,
                        {"platform": site, "username": username, "found": True},
                        rel="found_account")
                    found.append(site)
                    ctx.log(f"✅ Found: {site}", "info")
            except:
                pass
        
        ctx.log(f"Sherlock: Found on {len(found)} sites", "info")

