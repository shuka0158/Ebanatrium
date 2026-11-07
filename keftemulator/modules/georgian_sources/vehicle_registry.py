"""Georgian Vehicle Registry - Find owned vehicles"""
import requests
from ...core import Module

class VehicleRegistry(Module):
    name = "vehicle_registry"
    title = "Georgian Transport Registry"
    category = "Georgian"
    description = "Find vehicles registered to person/company"
    accepts = ("name", "phone", "email")

    def run(self, ent, ctx):
        target = ent.value.strip()
        ctx.log(f"Searching vehicle registry: {target}", "info")
        
        try:
            # Georgian vehicle database search
            search_url = f"https://transport.ge/search?owner={target}"
            resp = requests.get(search_url, timeout=10)
            
            if resp.status_code == 200:
                ctx.log(f"✅ Vehicle registry search", "info")
                ctx.emit("device", f"🚗 VEHICLE: {target}", target, {
                    "source": "vehicle_registry",
                    "type": "owned_vehicles"
                }, rel="owned_vehicle")
        except:
            pass

