"""GitHub Deep Search - Find real profiles and repositories"""
import requests
from ..core import Module

class GitHubDeepSearch(Module):
    name = "github_deep_search"
    title = "GitHub Profile Deep Search"
    category = "People Search"
    description = "Find GitHub users, repositories, commits - REAL profile data"
    accepts = ("username", "email_address", "name")

    def run(self, ent, ctx):
        query = ent.value.strip()
        ctx.log(f"Searching GitHub: {query}", "info")
        
        try:
            # GitHub API - FREE, returns REAL user data
            
            # 1. Search by username
            resp = requests.get(
                f"https://api.github.com/users/{query}",
                timeout=10,
                headers={"User-Agent": "Keftemulator/1.0"}
            )
            
            if resp.status_code == 200:
                user = resp.json()
                
                if user.get('login'):
                    ctx.log(f"✅ Found GitHub user: {user['login']}", "info")
                    
                    # EMIT REAL user data
                    ctx.emit("profile",
                        f"👤 GitHub: {user.get('name', user['login'])}",
                        query, {
                            "username": user.get('login'),
                            "name": user.get('name'),
                            "bio": user.get('bio'),
                            "company": user.get('company'),
                            "location": user.get('location'),
                            "email": user.get('email'),
                            "blog": user.get('blog'),
                            "twitter": user.get('twitter_username'),
                            "repos": user.get('public_repos'),
                            "followers": user.get('followers'),
                            "following": user.get('following'),
                            "created": user.get('created_at'),
                            "url": user.get('html_url'),
                            "source": "github"
                        }, rel="github_profile")
                    
                    # Get repositories
                    repos_resp = requests.get(
                        f"https://api.github.com/users/{query}/repos?sort=stars&per_page=10",
                        timeout=10,
                        headers={"User-Agent": "Keftemulator/1.0"}
                    )
                    
                    if repos_resp.status_code == 200:
                        repos = repos_resp.json()
                        for repo in repos[:5]:
                            ctx.emit("link",
                                f"📦 {repo['name']}: {repo['description'] or 'No description'}",
                                repo['html_url'], {
                                    "stars": repo.get('stargazers_count'),
                                    "language": repo.get('language'),
                                    "url": repo.get('html_url'),
                                    "source": "github_repos"
                                }, rel="github_repo")
                            
        except Exception as e:
            ctx.log(f"GitHub search error: {str(e)[:50]}", "warn")

