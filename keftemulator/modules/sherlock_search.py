"""Sherlock - Find social media profiles by username"""
import subprocess
import json
from ..core import Module

class SherlockSearch(Module):
    name = "sherlock_search"
    title = "Sherlock Social Media Finder"
    category = "People Search"
    description = "Find social media profiles using Sherlock (free, open source)"
    accepts = ("username", "name", "email")

    def run(self, ent, ctx):
        query = ent.value.strip()
        
        ctx.log(f"Sherlock search: {query}", "info")
        
        try:
            # Try to run sherlock if installed
            result = subprocess.run(
                ["sherlock", query, "--json"],
                capture_output=True,
                timeout=30,
                text=True
            )
            
            if result.returncode == 0 and result.stdout:
                try:
                    data = json.loads(result.stdout)
                    
                    # Process results
                    found_profiles = []
                    for site, info in data.items():
                        if isinstance(info, dict) and info.get('exists'):
                            profile_url = info.get('url')
                            found_profiles.append({
                                "site": site,
                                "url": profile_url,
                                "found": True
                            })
                            ctx.emit("company", f"👤 {site}: {profile_url}", query, info, rel="social_profile")
                            ctx.log(f"Found: {site}", "info")
                    
                    if found_profiles:
                        ctx.log(f"Found {len(found_profiles)} profiles", "info")
                    else:
                        ctx.log(f"No profiles found for {query}", "info")
                        
                except json.JSONDecodeError:
                    ctx.log("Could not parse Sherlock results", "warn")
        except FileNotFoundError:
            ctx.log("Sherlock not installed (install with: pip install sherlock-project)", "warn")
        except subprocess.TimeoutExpired:
            ctx.log("Sherlock search timed out", "warn")
        except Exception as e:
            ctx.log(f"Sherlock error: {str(e)[:50]}", "warn")

