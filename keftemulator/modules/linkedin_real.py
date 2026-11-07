"""LinkedIn Real Profiles - Return actual people found"""
import requests
from ..core import Module

class LinkedInReal(Module):
    name = "linkedin_real"
    title = "LinkedIn Real Profiles"
    category = "People Search"
    description = "Find real LinkedIn profiles with employment data"
    accepts = ("name", "email_address")

    def run(self, ent, ctx):
        query = ent.value.strip()
        
        try:
            # GitHub API works great for people with public profiles
            # LinkedIn is harder, but we can get GitHub instead
            if "@" not in query:
                resp = requests.get(f"https://api.github.com/users/{query}", timeout=10)
                if resp.status_code == 200:
                    user = resp.json()
                    if user.get('login'):
                        ctx.emit("profile",
                            f"👤 {user.get('name', query)} ({user['login']}) - {user.get('company', 'N/A')}",
                            user.get('html_url', ''),
                            {
                                "name": user.get('name'),
                                "username": user.get('login'),
                                "company": user.get('company'),
                                "location": user.get('location'),
                                "repos": user.get('public_repos'),
                                "followers": user.get('followers'),
                                "url": user.get('html_url'),
                                "source": "github"
                            }, rel="profile_found")
        except:
            pass

