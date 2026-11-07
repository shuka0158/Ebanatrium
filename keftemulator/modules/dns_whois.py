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

        # DNS A Record
        try:
            ip = socket.gethostbyname(domain)
            info["ip_address"] = ip
            ctx.log(f"IP: {ip}", "info")
            ctx.emit("ip_address", ip, parent=ent.id, rel="resolves_to")
        except:
            ctx.log("DNS A record not found", "warn")

        # MX Records
        try:
            try:
                import dns.resolver
                mx_records = dns.resolver.resolve(domain, 'MX')
                info["mx_records"] = [str(mx.exchange) for mx in mx_records]
                ctx.log(f"MX records found: {len(info['mx_records'])}", "info")
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
