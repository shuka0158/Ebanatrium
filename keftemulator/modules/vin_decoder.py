"""VIN Decoder - Decode vehicle identification numbers"""
import requests
import json
from ..core import Module

class VINDecoder(Module):
    name = "vin_decoder"
    title = "VIN Decoder"
    category = "Intelligence"
    description = "Decode VIN to get vehicle make, model, year, specs"
    accepts = ("vin",)

    def run(self, ent, ctx):
        vin = ent.value.strip().upper()
        
        if len(vin) != 17:
            ctx.log(f"Invalid VIN length: {len(vin)}", "warn")
            return
        
        ctx.log(f"Decoding VIN: {vin}", "info")
        
        # Use multiple free VIN decoder APIs
        apis = [
            {
                "name": "VINDecoder.com",
                "url": f"https://www.vindecoder.com/api/v2/decode?vin={vin}&key=free",
                "parse": lambda r: r.json() if r.status_code == 200 else None
            },
            {
                "name": "VINQuery Free",
                "url": f"https://api.vinquery.com/decode?vin={vin}",
                "parse": lambda r: r.json() if r.status_code == 200 else None
            },
            {
                "name": "VPIC (NHTSA)",
                "url": f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json",
                "parse": lambda r: r.json() if r.status_code == 200 else None
            },
        ]
        
        for api in apis:
            try:
                resp = requests.get(api["url"], timeout=10)
                if resp.status_code == 200:
                    data = api["parse"](resp)
                    
                    if data:
                        # Parse results
                        if "Results" in data:  # NHTSA format
                            results = data.get("Results", [{}])[0]
                            make = results.get("Make", "")
                            model = results.get("Model", "")
                            year = results.get("ModelYear", "")
                            
                            if make or model:
                                label = f"Vehicle: {year} {make} {model}"
                                ctx.emit("link",
                                    label,
                                    f"https://www.vindecoder.com/decode/{vin}",
                                    {"vin": vin, "make": make, "model": model, "year": year, "source": api["name"]},
                                    rel="vin_decode")
                                ctx.log(f"✅ {api['name']}: {label}", "info")
                        
                        elif "decode" in data or "result" in data:  # Other formats
                            result = data.get("decode") or data.get("result", {})
                            if result:
                                make = result.get("make", "")
                                model = result.get("model", "")
                                year = result.get("year", "")
                                
                                if make or model:
                                    label = f"Vehicle: {year} {make} {model}"
                                    ctx.emit("link",
                                        label,
                                        f"https://www.vindecoder.com/decode/{vin}",
                                        {"vin": vin, "make": make, "model": model, "year": year, "source": api["name"]},
                                        rel="vin_decode")
                                    ctx.log(f"✅ {api['name']}: {label}", "info")
            except Exception as e:
                ctx.log(f"{api['name']}: {str(e)[:50]}", "debug")

