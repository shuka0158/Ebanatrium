"""Website Analyzer - Full website intelligence (Web-check integration)"""
import requests
import re
from ..core import Module

class WebsiteAnalyzer(Module):
    name = "website_analyzer"
    title = "Website Intelligence"
    category = "Domain"
    description = "Analyze website: SSL, headers, technologies, DNS"
    accepts = ("domain", "url")

    def run(self, ent, ctx):
        url = ent.value.strip()
        if not url.startswith('http'):
            url = f"https://{url}"
        
        domain = url.split('/')[2].replace('www.', '')
        ctx.log(f"Analyzing: {domain}", "info")
        
        try:
            # Get SSL info
            resp = requests.get(f"https://crt.sh/?q={domain}&output=json", timeout=10)
            if resp.status_code == 200:
                certs = resp.json()
                if certs:
                    cert = certs[0]
                    ctx.emit("link",
                        f"SSL Certificate: {cert.get('name_value', domain)}",
                        url,
                        cert, rel="ssl_info")
            
            # DNS lookup
            try:
                import socket
                ip = socket.gethostbyname(domain)
                ctx.emit("ip_address",
                    f"IP Address: {ip}",
                    f"https://ipinfo.io/{ip}",
                    {"ip": ip, "domain": domain}, rel="domain_ip")
            except:
                pass
                
        except Exception as e:
            ctx.log(f"Website analysis error: {str(e)[:30]}", "warn")

