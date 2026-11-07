"""Phone number identifier - Get carrier, location, and type info"""
import re
import requests
from ..core import Module

class PhoneIdentifier(Module):
    name = "phone_identifier"
    title = "Phone Number Identifier"
    category = "People Search"
    description = "Identify phone carrier, location, and type (mobile/landline) from phone numbers"
    accepts = ("phone",)

    def run(self, ent, ctx):
        phone = ent.value.strip()

        # Clean phone number
        phone_clean = re.sub(r'\D', '', phone)

        ctx.log(f"identifying phone: {phone_clean}", "info")

        info = {
            "phone": phone,
            "phone_clean": phone_clean,
            "source": "phone_identifier"
        }

        # Get ACTUAL phone data - carrier, location, type
        try:
            resp = requests.get(
                f"https://neutrinoapi.com/phone-validate?number={phone_clean}",
                timeout=10,
                headers={"User-ID": "free"}
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get('valid'):
                    info["valid"] = True
                    info["country"] = data.get('country', 'Unknown')
                    info["country_code"] = data.get('country-code', 'N/A')
                    info["type"] = data.get('type', 'Unknown')  # mobile/landline/voip
                    info["carrier"] = data.get('carrier', 'Unknown')
                    info["location"] = data.get('location', 'Unknown')

                    # EMIT ACTUAL DATA with all details
                    phone_type = info.get('type', 'Unknown')
                    carrier = info.get('carrier', 'Unknown')
                    location = info.get('location', 'Unknown')
                    country = info.get('country', 'Unknown')

                    details = f"{phone_type.upper()} | Carrier: {carrier} | Location: {location}, {country}"
                    ctx.log(f"Phone: {details}", "info")
                    ctx.emit("company", f"📱 {phone_clean}: {details}", phone, info, rel="phone_info")
                    return
        except:
            pass

        # Try OpenCage Reverse Geocoding if we have area code
        if len(phone_clean) >= 3:
            area_code = phone_clean[:3]

            # US area code lookup
            try:
                resp = requests.get(
                    f"https://areacode.com/api/area_code.php?area_code={area_code}",
                    timeout=10
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data and len(data) > 0:
                        info["area_code"] = area_code
                        info["area_location"] = str(data[0]).replace("'", "")
                        ctx.log(f"Area code location: {info['area_location']}", "info")
            except:
                pass

        # Pattern analysis
        if phone_clean.startswith('1'):
            info["region"] = "United States/Canada"
        elif phone_clean.startswith('44'):
            info["region"] = "United Kingdom"
        elif phone_clean.startswith('33'):
            info["region"] = "France"

        if '555' in phone_clean:
            info["notes"] = "Fictional/Test number (555 exchange)"

        ctx.emit("company", f"📱 Phone Info", phone, info, rel="phone_info")
