"""GitHub Profile Data Extraction - Real Intelligence"""

import requests
import time
import os

class GitHubRealData:
    name = "GitHub - Real Profile Data"
    category = "People Search"
    accepts = ["username"]
    
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN") or None
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({"Authorization": f"token {self.token}"})
    
    def investigate(self, target, ctx):
        """Extract real GitHub profile data"""
        
        try:
            ctx.emit("status", f"Fetching GitHub profile: {target}")
            
            url = f"https://api.github.com/users/{target}"
            headers = {
                "User-Agent": "Eba[Na]trium OSINT",
                "Accept": "application/vnd.github.v3+json"
            }
            
            if self.token:
                headers["Authorization"] = f"token {self.token}"
            
            resp = requests.get(url, headers=headers, timeout=10)
            
            # Check rate limit
            if resp.status_code == 403:
                reset = resp.headers.get("X-RateLimit-Reset", "unknown")
                ctx.emit("link", "GitHub Rate Limit", 
                        f"API rate limited. Reset: {reset}. Set GITHUB_TOKEN env var for higher limits.",
                        {"status": 403, "reset": reset},
                        rel="github_ratelimit")
                return
            
            if resp.status_code != 200:
                ctx.emit("link", "GitHub Error", 
                        f"Status {resp.status_code}: {resp.reason}",
                        {"status": resp.status_code},
                        rel="github_error")
                return
            
            profile = resp.json()
            
            # Extract profile data
            if profile.get("name"):
                ctx.emit("link", "Name", profile["name"], 
                        {"type": "name", "value": profile["name"]},
                        rel="profile_data")
            
            if profile.get("location"):
                ctx.emit("link", "Location", profile["location"], 
                        {"type": "location", "value": profile["location"]},
                        rel="profile_data")
            
            if profile.get("company"):
                ctx.emit("link", "Company", profile["company"], 
                        {"type": "company", "value": profile["company"]},
                        rel="profile_data")
            
            if profile.get("bio"):
                ctx.emit("link", "Bio", profile["bio"], 
                        {"type": "bio", "value": profile["bio"]},
                        rel="profile_data")
            
            if profile.get("public_repos"):
                ctx.emit("link", "Public Repos", str(profile["public_repos"]), 
                        {"type": "repo_count", "value": profile["public_repos"]},
                        rel="profile_stats")
            
            if profile.get("followers"):
                ctx.emit("link", "Followers", str(profile["followers"]), 
                        {"type": "followers", "value": profile["followers"]},
                        rel="profile_stats")
            
            if profile.get("following"):
                ctx.emit("link", "Following", str(profile["following"]), 
                        {"type": "following", "value": profile["following"]},
                        rel="profile_stats")
            
            if profile.get("created_at"):
                ctx.emit("link", "Account Created", profile["created_at"], 
                        {"type": "created", "value": profile["created_at"]},
                        rel="profile_data")
            
            if profile.get("updated_at"):
                ctx.emit("link", "Last Updated", profile["updated_at"], 
                        {"type": "updated", "value": profile["updated_at"]},
                        rel="profile_data")
            
            # Get repositories
            self._fetch_repos(target, ctx, headers)
            
        except requests.exceptions.Timeout:
            ctx.emit("link", "GitHub Timeout", 
                    "Request timed out after 10 seconds",
                    {"error": "timeout"},
                    rel="github_error")
        except Exception as e:
            ctx.emit("link", "GitHub Error", str(e)[:100], 
                    {"error": str(e)},
                    rel="github_error")
    
    def _fetch_repos(self, username, ctx, headers):
        """Fetch repositories"""
        try:
            url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=10"
            resp = requests.get(url, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                repos = resp.json()
                for repo in repos[:10]:
                    name = repo.get("name")
                    stars = repo.get("stargazers_count", 0)
                    url = repo.get("html_url")
                    
                    if name and url:
                        ctx.emit("link", f"Repository: {name} ({stars}⭐)", url,
                                {"type": "repository", "name": name, "stars": stars, "url": url},
                                rel="github_repo")
        except:
            pass


MODULE = GitHubRealData()
