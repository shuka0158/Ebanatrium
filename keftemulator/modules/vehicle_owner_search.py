"""Vehicle Owner Search - Find vehicle owner information"""
import requests
from ..core import Module

class VehicleOwnerSearch(Module):
    name = "vehicle_owner_search"
    title = "Vehicle Owner Search"
    category = "People Search"
    description = "Search for vehicle owner information (public records)"
    accepts = ("vin", "plate")

    def run(self, ent, ctx):
        query = ent.value.strip().upper()
        
        ctx.log(f"Vehicle owner search: {query}", "info")
        
        # Public vehicle owner databases
        sources = [
            ("AutoCheck", f"https://www.autocheck.com/vehiclehistory/search"),
            ("CarFax", f"https://www.carfax.com/"),
            ("VIN Decoder", f"https://www.vindecoder.com/search/{query}"),
            ("VINQuery", f"https://vinquery.com/search/{query}"),
            ("NHTSA Vehicle Search", f"https://vpic.nhtsa.dot.gov/"),
        ]
        
        for source, url in sources:
            ctx.emit("link",
                f"Vehicle Owner Database: {source}",
                url,
                {"query": query, "type": "vehicle_owner", "source": source},
                rel="vehicle_owner")
            ctx.log(f"✅ {source}", "info")

