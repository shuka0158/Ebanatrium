"""GitHub Comprehensive - Full profile analysis"""
import requests
from ..core import Module

class GitHubComprehensive(Module):
    name = "github_comprehensive"
    title = "GitHub Comprehensive Profile"
    category = "People Search"
    description = "Get full GitHub profile: repos, followers, activity, contributions"
    accepts = ("username",)

    def run(self, ent, ctx):
        username = ent.value.strip()
        
        try:
            # Get user
            resp = requests.get(f"https://api.github.com/users/{username}", timeout=10)
            if resp.status_code != 200:
                return
            
            user = resp.json()
            if not user.get('login'):
                return
            
            ctx.log(f"✅ GitHub profile: {user.get('name', username)}", "info")
            
            # Emit profile
            ctx.emit("profile",
                f"GitHub: {user.get('name', username)} ({user['login']})",
                user.get('html_url', ''),
                user, rel="github_profile")
            
            # Get repos
            repos_resp = requests.get(
                f"https://api.github.com/users/{username}/repos?sort=stars&per_page=50",
                timeout=10
            )
            if repos_resp.status_code == 200:
                repos = repos_resp.json()
                for repo in repos[:20]:
                    ctx.emit("link",
                        f"Repo: {repo['name']} ({repo.get('stargazers_count', 0)} stars)",
                        repo.get('html_url', ''),
                        repo, rel="github_repo")
            
            # Get followers
            followers_resp = requests.get(
                f"https://api.github.com/users/{username}/followers?per_page=30",
                timeout=10
            )
            if followers_resp.status_code == 200:
                followers = followers_resp.json()
                for follower in followers[:10]:
                    ctx.emit("profile",
                        f"Follower: {follower.get('login')}",
                        follower.get('html_url', ''),
                        follower, rel="follower")
                        
        except Exception as e:
            ctx.log(f"GitHub error: {str(e)[:30]}", "warn")

