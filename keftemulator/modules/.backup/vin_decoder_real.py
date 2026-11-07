"""VIN Decoder - Real data extraction from NHTSA"""
import requests
from ..core import Module

class VINDecoderReal(Module):
    name = "vin_decoder_real"
    title = "VIN Decoder - Real Vehicle Data"
    category = "Intelligence"
    description = "Decode VIN and extract REAL vehicle specifications"
    accepts = ("vin",)

    def run(self, ent, ctx):
        vin = ent.value.strip().upper()
        
        if len(vin) != 17:
            ctx.log(f"Invalid VIN: must be 17 chars", "warn")
            return
        
        ctx.log(f"Decoding VIN: {vin}", "info")
        
        # NHTSA VPIC API - official, free, no auth
        try:
            url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"
            resp = requests.get(url, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                
                if data.get("Results"):
                    result = data["Results"][0]
                    
                    # Extract REAL data
                    make = result.get("Make", "").strip()
                    model = result.get("Model", "").strip()
                    year = result.get("ModelYear", "").strip()
                    body = result.get("BodyClass", "").strip()
                    engine = result.get("EngineModel", "").strip()
                    transmission = result.get("TransmissionStyle", "").strip()
                    fuel_type = result.get("FuelTypePrimary", "").strip()
                    series = result.get("Series", "").strip()
                    
                    # Build detailed report
                    if make and model:
                        label = f"VIN Decoded: {year} {make} {model}"
                        data_obj = {
                            "vin": vin,
                            "make": make,
                            "model": model,
                            "year": year,
                            "body_class": body,
                            "engine": engine,
                            "transmission": transmission,
                            "fuel_type": fuel_type,
                            "series": series
                        }
                        
                        ctx.emit("link",
                            label,
                            f"NHTSA Official Data",
                            data_obj,
                            rel="vin_real_data")
                        
                        ctx.log(f"✅ VIN Decoded: {year} {make} {model}", "info")
                        
                        # Emit individual fields
                        if body:
                            ctx.emit("link", f"Body Type: {body}", body, {}, rel="body_type")
                        if engine:
                            ctx.emit("link", f"Engine: {engine}", engine, {}, rel="engine")
                        if fuel_type:
                            ctx.emit("link", f"Fuel Type: {fuel_type}", fuel_type, {}, rel="fuel_type")
                    else:
                        ctx.log(f"VIN not found in NHTSA database", "info")
                else:
                    ctx.log(f"No decoding results", "info")
        except Exception as e:
            ctx.log(f"VIN decode error: {str(e)[:50]}", "warn")

