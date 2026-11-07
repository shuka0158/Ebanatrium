"""Vehicle Recalls & Safety - Find recalls and safety issues"""
import requests
from ..core import Module

class VehicleRecalls(Module):
    name = "vehicle_recalls"
    title = "Vehicle Recalls & Safety"
    category = "Intelligence"
    description = "Check NHTSA recalls and safety data for vehicle"
    accepts = ("vin", "make", "model")

    def run(self, ent, ctx):
        query = ent.value.strip()
        
        ctx.log(f"Checking recalls: {query}", "info")
        
        # NHTSA API for recalls
        try:
            # Try VIN first
            if len(query) == 17:  # VIN
                url = f"https://api.nhtsa.dot.gov/recalls/vehicleRecalls?format=json&vin={query}"
            else:
                url = f"https://api.nhtsa.dot.gov/recalls/vehicleRecalls?format=json&model={query}"
            
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                
                if data.get("Results"):
                    for result in data["Results"][:10]:
                        recall = result.get("Summary", "Recall found")
                        ctx.emit("link",
                            f"Safety Recall: {recall[:60]}...",
                            f"https://www.nhtsa.gov/recalls",
                            {"query": query, "type": "recall", "data": result},
                            rel="vehicle_recall")
                        ctx.log(f"✅ Recall found", "info")
        except:
            pass
        
        # Alternative sources
        sources = [
            ("NHTSA", f"https://www.nhtsa.gov/vehicle/{query}"),
            ("SaferCar", f"https://www.safercar.gov/"),
        ]
        
        for source, url in sources:
            ctx.emit("link",
                f"Safety Database: {source}",
                url,
                {"query": query, "source": source},
                rel="vehicle_safety")

