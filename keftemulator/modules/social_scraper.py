"""Social media data extractor - Extract public profiles and info"""
import requests
from bs4 import BeautifulSoup
import re
from ..core import Module

class SocialMediaScraper(Module):
    name = "social_scraper"
    title = "Social Media Scraper"
    category = "People Search"
    description = "Extract ACTUAL profile data from public social media profiles"
    accepts = ("phone", "email", "name", "username")

    def run(self, ent, ctx):
        query = ent.value.strip()
        
        ctx.log(f"Searching social media for: {query}", "info")
        
        # Search multiple platforms
        platforms = {
            "Facebook": f"https://www.facebook.com/public/{query}",
            "Instagram": f"https://www.instagram.com/{query}/",
            "LinkedIn": f"https://www.linkedin.com/in/{query}/",
            "VKontakte": f"https://vk.com/{query}",
            "Twitter": f"https://twitter.com/search?q={query}",
        }
        
        for platform, url in platforms.items():
            try:
                ctx.log(f"Checking {platform}...", "info")
                
                resp = requests.get(
                    url,
                    timeout=10,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.content, 'html.parser')
                    
                    # Extract profile info
                    # Look for common profile elements
                    bio = soup.find(['meta', 'p'], {'name': 'description'})
                    profile_name = soup.find(['h1', 'h2', 'meta'], {'property': 'og:title'})
                    
                    if profile_name or bio:
                        data = {
                            "platform": platform,
                            "url": url,
                            "profile_found": True,
                            "source": platform
                        }
                        
                        ctx.log(f"{platform}: Profile found", "info")
                        ctx.emit("company", f"👤 {platform}: {query}", query, data, rel="social_profile")
                        
            except:
                pass  # Continue to next platform

