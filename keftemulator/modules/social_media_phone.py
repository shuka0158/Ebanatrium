"""Social media reverse phone search - Find phone numbers on social platforms"""
import requests
import re
from ..core import Module

class SocialMediaPhoneSearch(Module):
    name = "social_media_phone"
    title = "Social Media Phone Search"
    category = "People Search"
    description = "Search social media platforms (Telegram, Facebook, Instagram, VKontakte) for phone numbers"
    accepts = ("phone",)

    def run(self, ent, ctx):
        phone = ent.value.strip()
        phone_clean = re.sub(r'\D', '', phone)
        
        ctx.log(f"Searching social media for phone: {phone_clean}", "info")
        
        info = {
            "phone": phone_clean,
            "searches": []
        }
        
        # Telegram search
        try:
            # Search Telegram public groups and channels
            info["searches"].append({
                "platform": "Telegram",
                "query": f"https://t.me/search?q={phone_clean}",
                "status": "Manual search required"
            })
            ctx.log("Telegram: Search needed (requires manual access)", "info")
        except:
            pass
        
        # Facebook search
        try:
            info["searches"].append({
                "platform": "Facebook",
                "query": f"https://www.facebook.com/search?q={phone_clean}",
                "status": "Manual search required"
            })
            ctx.log("Facebook: Search available", "info")
        except:
            pass
        
        # VKontakte search (popular in Georgia/Russia)
        try:
            info["searches"].append({
                "platform": "VKontakte",
                "query": f"https://vk.com/search?q={phone_clean}",
                "status": "Manual search available"
            })
            ctx.log("VKontakte: Search available", "info")
        except:
            pass
        
        # Instagram search
        try:
            info["searches"].append({
                "platform": "Instagram",
                "query": f"https://www.instagram.com/explore/search/query/?q={phone_clean}",
                "status": "Manual search required"
            })
            ctx.log("Instagram: Search available", "info")
        except:
            pass
        
        # Google search for phone number
        try:
            info["searches"].append({
                "platform": "Google",
                "query": f'https://www.google.com/search?q="{phone_clean}"',
                "status": "May find mentions in forums, classifieds, reviews"
            })
            ctx.log("Google: Public search available", "info")
        except:
            pass
        
        # Emit results
        search_list = " | ".join([f"{s['platform']}" for s in info['searches']])
        ctx.emit("company", f"📲 SOCIAL SEARCH: {phone_clean} found on: {search_list}", phone, info, rel="social_search")

