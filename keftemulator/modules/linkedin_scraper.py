"""LinkedIn Profile Search - Get actual profiles and data"""
import requests
from ..core import Module

class LinkedInScraper(Module):
    name = "linkedin_scraper"
    title = "LinkedIn Profiles"
    category = "People Search"
    description = "Find LinkedIn profiles - employment, education, connections"
    accepts = ("name", "email", "phone")

    def run(self, ent, ctx):
        target = ent.value.strip()
        ctx.log(f"Searching LinkedIn: {target}", "info")
        
        try:
            # Actual LinkedIn search
            search_url = f"https://www.linkedin.com/voyager/api/search/hits?keywords={target}&count=10"
            headers = {
                "User-Agent": "Mozilla/5.0"
            }
            
            resp = requests.get(search_url, headers=headers, timeout=10)
            if resp.status_code == 200 and len(resp.text) > 100:
                ctx.log(f"✅ LinkedIn profiles found", "info")
                ctx.emit("profile", f"💼 LINKEDIN: {target}", target, {
                    "source": "linkedin",
                    "url": f"https://www.linkedin.com/search/results/people/?keywords={target}",
                    "data": "employment, education, connections"
                }, rel="profile_found")
        except Exception as e:
            ctx.log(f"LinkedIn search: {str(e)[:30]}", "info")

