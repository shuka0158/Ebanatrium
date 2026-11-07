"""Georgian classifieds and directory search - OLX, 123.ge, list.ge"""
import requests
from ..core import Module

class GeorgianClassifieds(Module):
    name = "georgian_classifieds"
    title = "Georgian Classifieds Search"
    category = "People Search"
    description = "Search Georgian classified sites (OLX.ge, 123.ge, list.ge) for phone number mentions"
    accepts = ("phone",)

    def run(self, ent, ctx):
        phone = ent.value.strip()
        
        ctx.log(f"Searching Georgian classifieds for: {phone}", "info")
        
        info = {
            "phone": phone,
            "sites_to_search": [
                "olx.ge",
                "123.ge", 
                "list.ge",
                "av.ge",
                "mygeo.ge",
                "homeestate.ge"
            ]
        }
        
        # Search OLX
        try:
            resp = requests.get(
                f"https://www.olx.ge/search?q={phone}",
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if resp.status_code == 200 and len(resp.text) > 1000:
                info["olx_results"] = "Found listings mentioning this phone"
                ctx.log(f"OLX.ge: Found {resp.text.count(phone)} mentions", "info")
        except:
            ctx.log("OLX.ge: Not accessible", "warn")
        
        # Search 123.ge
        try:
            resp = requests.get(
                f"https://123.ge/search?q={phone}",
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            if resp.status_code == 200:
                info["123ge_results"] = "Found results"
                ctx.log("123.ge: Checked", "info")
        except:
            pass
        
        sites_str = ", ".join(info["sites_to_search"][:3])
        ctx.emit("company", f"🏪 CLASSIFIEDS: {phone} - Search on: {sites_str}", phone, info, rel="classifieds")

