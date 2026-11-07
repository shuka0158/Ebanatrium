"""Instagram OSINT - Find Instagram profiles (Osintgram integration)"""
import requests
from ..core import Module

class InstagramOSINT(Module):
    name = "instagram_osint"
    title = "Instagram Profile Search"
    category = "People Search"
    description = "Find Instagram profiles and public information"
    accepts = ("username", "name")

    def run(self, ent, ctx):
        query = ent.value.strip().lower()
        
        try:
            # Instagram public API endpoint
            resp = requests.get(
                f"https://www.instagram.com/web/search/topsearch/?query={query}",
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                
                if data.get('users'):
                    for user in data['users'][:10]:
                        user_data = user.get('user', {})
                        if user_data.get('username'):
                            ctx.emit("account",
                                f"Instagram: {user_data.get('full_name', user_data['username'])}",
                                f"https://instagram.com/{user_data['username']}",
                                user_data, rel="instagram_profile")
                            ctx.log(f"✅ Found Instagram: {user_data['username']}", "info")
        except:
            pass

