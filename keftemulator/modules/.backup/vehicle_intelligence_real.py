"""Vehicle Intelligence - Real data from multiple sources"""
import requests
from ..core import Module

class VehicleIntelligenceReal(Module):
    name = "vehicle_intelligence_real"
    title = "Vehicle Intelligence - Real Data"
    category = "Intelligence"
    description = "Find real vehicle data: recalls, specifications, history"
    accepts = ("vin", "plate")

    def run(self, ent, ctx):
        query = ent.value.strip().upper()
        is_vin = len(query) == 17
        
        ctx.log(f"Vehicle intelligence search: {query}", "info")
        
        # Get NHTSA data
        if is_vin:
            try:
                # Decode VIN for specifications
                url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{query}?format=json"
                resp = requests.get(url, timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("Results"):
                        specs = data["Results"][0]
                        
                        # Emit all available specs as real data
                        for key, val in specs.items():
                            if val and str(val).strip():
                                ctx.emit("link",
                                    f"{key}: {val}",
                                    str(val),
                                    {"field": key, "value": val, "source": "NHTSA"},
                                    rel="vehicle_spec")
                        
                        ctx.log(f"✅ Found {len([v for v in specs.values() if v])} vehicle specs", "info")
            except Exception as e:
                ctx.log(f"Vehicle spec error: {str(e)[:40]}", "debug")
        
        # Search for recalls
        try:
            if is_vin:
                recall_url = f"https://api.nhtsa.dot.gov/recalls/vehicleRecalls?format=json&vin={query}"
            else:
                recall_url = f"https://api.nhtsa.dot.gov/recalls/vehicleRecalls?format=json&plate={query}"
            
            resp = requests.get(recall_url, timeout=10)
            
            if resp.status_code == 200:
                recall_data = resp.json()
                
                if recall_data.get("Results"):
                    for recall in recall_data["Results"][:10]:
                        summary = recall.get("Summary", "Recall")
                        component = recall.get("Component", "")
                        
                        label = f"⚠️ RECALL: {summary[:80]}"
                        if component:
                            label += f" ({component})"
                        
                        ctx.emit("link",
                            label,
                            "NHTSA Recall Database",
                            recall,
                            rel="active_recall")
                        
                        ctx.log(f"✅ Recall found: {summary[:50]}", "warn")
        except:
            pass

