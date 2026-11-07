"""License Plate Lookup - Decode license plates"""
import requests
from ..core import Module

class PlateLookup(Module):
    name = "plate_lookup"
    title = "License Plate Lookup"
    category = "Intelligence"
    description = "Decode license plate to get vehicle info (where available)"
    accepts = ("plate",)

    def run(self, ent, ctx):
        plate = ent.value.strip().upper().replace(" ", "")
        
        ctx.log(f"Plate lookup: {plate}", "info")
        
        # Search public vehicle databases
        sources = [
            ("PlateSearchDB", f"https://platesearch.com/search/{plate}"),
            ("OpenPlates", f"https://openplates.org/search?q={plate}"),
            ("PlateDatabase", f"https://www.platedatabase.com/search/{plate}"),
            ("VehicleCheck", f"https://vehiclecheck.co.uk/number-plate-check/{plate}"),
        ]
        
        for source, url in sources:
            try:
                resp = requests.head(url, timeout=5)
                if resp.status_code == 200:
                    ctx.emit("link",
                        f"Plate Database: {source}",
                        url,
                        {"plate": plate, "source": source},
                        rel="plate_lookup")
                    ctx.log(f"✅ {source} - accessible", "info")
            except:
                pass

