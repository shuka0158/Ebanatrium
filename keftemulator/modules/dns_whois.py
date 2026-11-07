"""DNS and WHOIS lookup for domains"""
import socket
import requests
from ..core import Module

class DNSWhoIsLookup(Module):
    name = "dns_whois"
    title = "DNS & WHOIS Lookup"
    category = "Domain Intelligence"
    description = "Lookup DNS records, nameservers, and WHOIS registration info for domains"
    accepts = ("domain",)

    def run(self, ent, ctx):
        domain = ent.value.strip().lower()

        if not ('.' in domain):
            return

        ctx.log(f"dns/whois lookup: {domain}", "info")

        info = {
            "domain": domain,
            "source": "dns_whois"
        }

        # DNS A Record - ACTUAL DATA
        try:
            ip = socket.gethostbyname(domain)
            info["ip_address"] = ip
            info["record_type"] = "A"

            # Get IP geolocation with actual data
            try:
                import urllib.request, json
                response = urllib.request.urlopen(f"http://ip-api.com/json/{ip}?fields=country,city,org,isp", timeout=5)
                geo_data = json.loads(response.read())
                info["ip_country"] = geo_data.get("country", "Unknown")
                info["ip_city"] = geo_data.get("city", "Unknown")
                info["ip_org"] = geo_data.get("org", "Unknown")
                info["ip_isp"] = geo_data.get("isp", "Unknown")

                ctx.log(f"IP: {ip} | Location: {geo_data.get('city')}, {geo_data.get('country')} | ISP: {geo_data.get('isp')}", "info")
                label = f"A Record: {ip} ({geo_data.get('country')})"
            except:
                ctx.log(f"IP: {ip}", "info")
                label = f"A Record: {ip}"

            ctx.emit("ip_address", label, parent=ent.id, rel="resolves_to")
        except:
            ctx.log("DNS A record not found", "warn")

        # MX Records - ACTUAL EMAIL SERVERS
        try:
            try:
                import dns.resolver
                mx_records = dns.resolver.resolve(domain, 'MX')
                info["mx_records"] = [str(mx.exchange) for mx in mx_records]

                if info["mx_records"]:
                    mx_list = ", ".join(info["mx_records"][:3])  # Show first 3
                    ctx.log(f"MX Records: {mx_list}", "info")
                    ctx.emit("company", f"📧 Mail Servers", domain, {"mx_servers": info["mx_records"]}, rel="mail_servers")
            except ImportError:
                pass
        except:
            pass

        # WHOIS via API
        try:
            resp = requests.get(f"https://whois.arin.net/rest/ip/{domain}.json", timeout=10)
            if resp.status_code == 200:
                whois_data = resp.json()
                info["whois"] = whois_data
                ctx.log("WHOIS data retrieved", "info")
        except:
            pass

        # Alternative WHOIS lookup
        try:
            resp = requests.get(f"https://api.whoisxml.com/api/v2/whois?domain={domain}&apiKey=at_free", timeout=10)
            if resp.status_code == 200:
                whois_data = resp.json()
                if 'WhoisRecord' in whois_data:
                    record = whois_data['WhoisRecord']
                    if 'registrant' in record:
                        info["registrant"] = record['registrant'].get('name', 'N/A')
                    if 'createdDate' in record:
                        info["created_date"] = record['createdDate']
                    if 'expiresDate' in record:
                        info["expires_date"] = record['expiresDate']

                    ctx.log(f"WHOIS: {info.get('registrant', 'Unknown')}", "info")
        except:
            pass

        ctx.emit("company", f"🌐 Domain Info", domain, info, rel="domain_info")
