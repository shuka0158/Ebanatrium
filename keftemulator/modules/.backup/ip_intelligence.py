"""IP Intelligence - Location, ASN, abuse history - REAL data"""
import requests
import re
from ..core import Module

class IPIntelligence(Module):
    name = "ip_intelligence"
    title = "IP Intelligence & Geolocation"
    category = "IP"
    description = "Get IP location, ISP, abuse history - returns REAL geolocation data"
    accepts = ("ip_address",)

    def run(self, ent, ctx):
        ip = ent.value.strip()
        
        # Validate IP format
        if not re.match(r'^[\d.]+$|^[a-f0-9:]+$', ip):
            return
        
        ctx.log(f"IP intelligence: {ip}", "info")
        
        try:
            # IP API - FREE, returns REAL geolocation data
            resp = requests.get(
                f"https://ipapi.co/{ip}/json/",
                timeout=10
            )
            
            if resp.status_code == 200:
                data = resp.json()
                
                if data.get('ip'):
                    ctx.log(f"✅ Found IP: {data.get('city')}, {data.get('country_name')}", "info")
                    
                    # EMIT REAL geolocation data
                    ctx.emit("ip_address",
                        f"🌍 {ip}: {data.get('city', '?')}, {data.get('country_name', '?')}",
                        ip, {
                            "ip": ip,
                            "country": data.get('country_name'),
                            "country_code": data.get('country_code'),
                            "region": data.get('region'),
                            "city": data.get('city'),
                            "latitude": data.get('latitude'),
                            "longitude": data.get('longitude'),
                            "isp": data.get('org'),
                            "timezone": data.get('timezone'),
                            "postal": data.get('postal'),
                            "source": "ipapi"
                        }, rel="ip_location")
            
            # Also check abuse database
            resp2 = requests.get(
                f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}&maxAgeInDays=90",
                timeout=10,
                headers={
                    "Key": "free",
                    "Accept": "application/json"
                }
            )
            
            if resp2.status_code == 200:
                abuse_data = resp2.json()
                if abuse_data.get('data'):
                    data_obj = abuse_data['data']
                    if data_obj.get('abuseConfidenceScore', 0) > 0:
                        ctx.emit("ip_address",
                            f"🚨 ABUSE: {ip} - {data_obj.get('abuseConfidenceScore')}% confidence",
                            ip, {
                                "abuse_score": data_obj.get('abuseConfidenceScore'),
                                "reports": data_obj.get('totalReports'),
                                "source": "abuseipdb"
                            }, rel="ip_abuse")
                            
        except Exception as e:
            ctx.log(f"IP intelligence error: {str(e)[:50]}", "warn")

