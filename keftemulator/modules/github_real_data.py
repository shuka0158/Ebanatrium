"""GitHub Real Data - Returns actual profile information (not links)"""
import requests
import json
from ..core import Module

class GitHubRealData(Module):
    name = "github_real_data"
    title = "GitHub - Real Profile Data"
    category = "People Search"
    description = "Get REAL GitHub profile data: repos, stars, followers, code"
    accepts = ("username",)

    def run(self, ent, ctx):
        username = ent.value.strip().lower()
        ctx.log(f"Fetching GitHub profile: {username}", "info")
        
        try:
            # Get user profile
            url = f"https://api.github.com/users/{username}"
            resp = requests.get(url, timeout=10)
            
            if resp.status_code == 200:
                profile = resp.json()
                
                # REAL DATA: Emit actual profile info
                ctx.emit("link", 
                    f"Name: {profile.get('name', username)}",
                    profile.get('name', 'N/A'),
                    {"field": "name", "value": profile.get('name', 'N/A')},
                    rel="profile_data")
                
                if profile.get('location'):
                    ctx.emit("link",
                        f"Location: {profile['location']}",
                        profile['location'],
                        {"field": "location", "value": profile['location']},
                        rel="location")
                
                if profile.get('company'):
                    ctx.emit("link",
                        f"Company: {profile['company']}",
                        profile['company'],
                        {"field": "company", "value": profile['company']},
                        rel="employment")
                
                if profile.get('bio'):
                    ctx.emit("link",
                        f"Bio: {profile['bio'][:80]}",
                        profile['bio'],
                        {"field": "bio", "value": profile['bio']},
                        rel="bio")
                
                # REAL DATA: Get repos with stars
                repos_url = f"https://api.github.com/users/{username}/repos?sort=stars&per_page=20"
                repos_resp = requests.get(repos_url, timeout=10)
                
                if repos_resp.status_code == 200:
                    repos = repos_resp.json()
                    ctx.log(f"✅ Found {len(repos)} public repositories", "info")
                    
                    for repo in repos[:15]:
                        stars = repo.get('stargazers_count', 0)
                        fork_count = repo.get('forks_count', 0)
                        lang = repo.get('language', 'Unknown')
                        
                        label = f"Repo: {repo['name']} ({stars}⭐ {fork_count}⚒️)"
                        
                        ctx.emit("link",
                            label,
                            repo.get('description', repo['name']),
                            {
                                "repo": repo['name'],
                                "stars": stars,
                                "forks": fork_count,
                                "language": lang,
                                "url": repo['html_url'],
                                "description": repo.get('description', '')
                            },
                            rel="github_repo")
                
                # REAL DATA: Followers
                followers = profile.get('followers', 0)
                ctx.emit("link",
                    f"Followers: {followers}",
                    str(followers),
                    {"field": "followers", "value": followers},
                    rel="network")
                
                # REAL DATA: Public gists
                gists = profile.get('public_gists', 0)
                if gists > 0:
                    ctx.emit("link",
                        f"Public Gists: {gists}",
                        str(gists),
                        {"field": "public_gists", "value": gists},
                        rel="code_snippets")
                
            elif resp.status_code == 404:
                ctx.log(f"GitHub user not found: {username}", "info")
            else:
                ctx.log(f"GitHub API error: {resp.status_code}", "warn")
                
        except Exception as e:
            ctx.log(f"GitHub error: {str(e)[:50]}", "warn")

