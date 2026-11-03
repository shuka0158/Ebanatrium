"""Domain / IP / URL intelligence + theHarvester wrapper."""
import re
import socket
import tempfile
import json
from pathlib import Path
from urllib.parse import urlparse, urljoin

import dns.resolver
import dns.reversename

from ..core import Module
from ..util import get, get_json, find_tool, run_cmd, api_key, RE_DOMAIN

RE_EMAIL_IN = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
SOCIAL = re.compile(r"https?://(?:www\.)?(facebook|instagram|twitter|x|linkedin|youtube|tiktok|t|github|vk)"
                    r"\.(?:com|me|ru)/[A-Za-z0-9_.\-/@]+", re.I)


def _resolve(name, rtype):
    try:
        return [r.to_text() for r in dns.resolver.resolve(name, rtype, lifetime=8)]
    except Exception:
        return []


class DNSRecords(Module):
    name = "dns"
    title = "DNS records"
    category = "Domain"
    description = "A/AAAA/MX/NS/TXT/SOA/CAA, SPF & DMARC; resolves to IPs."
    accepts = ("domain",)

    def run(self, ent, ctx):
        d = ent.value
        rec = {t: _resolve(d, t) for t in ("A", "AAAA", "MX", "NS", "TXT", "SOA", "CAA")}
        rec["DMARC"] = _resolve("_dmarc." + d, "TXT")
        rec["SPF"] = [t for t in rec["TXT"] if "v=spf1" in t]
        ctx.update({"dns": {k: v for k, v in rec.items() if v}})
        for ip in rec["A"] + rec["AAAA"]:
            ctx.emit("ip", ip, rel="resolves to")
        for txt in rec["TXT"]:
            for m in re.findall(r"(?:include|redirect)[:=]([\w.\-]+)", txt):
                ctx.emit("domain", m, rel="SPF include", pivot=False)
            if "verification" in txt.lower():
                ctx.emit("info", txt.strip('"'), "Site verification token", rel="TXT", pivot=False)


class WhoisRDAP(Module):
    name = "whois"
    title = "WHOIS / RDAP"
    category = "Domain"
    description = "Registrar, creation/expiry dates, registrant contacts (when not redacted)."
    accepts = ("domain", "ip")

    def run(self, ent, ctx):
        kind = "ip" if ent.type == "ip" else "domain"
        d = get_json(f"https://rdap.org/{kind}/{ent.value}", timeout=20)
        if not d:
            return
        info = {}
        for e in d.get("events", []):
            info[e.get("eventAction")] = e.get("eventDate")
        if kind == "ip":
            info.update({"network": d.get("name"), "range": f"{d.get('startAddress')} - {d.get('endAddress')}",
                         "country": d.get("country"), "net_type": d.get("type")})
        for ent_ in d.get("entities", []):
            roles = ",".join(ent_.get("roles", []))
            vc = ent_.get("vcardArray", [None, []])[1]
            card = {}
            for item in vc:
                if item[0] in ("fn", "org", "email", "tel", "adr"):
                    val = item[3]
                    if isinstance(val, list):
                        val = ", ".join(x for x in val if isinstance(x, str) and x)
                    card[item[0]] = val
            if card:
                info[roles or "entity"] = card
                if card.get("email") and "redacted" not in card["email"].lower() and "abuse" not in roles:
                    ctx.emit("email", card["email"].lower(), rel=f"WHOIS {roles}")
                if card.get("fn") and "registrant" in roles and "redacted" not in card["fn"].lower():
                    ctx.emit("name", card["fn"], rel="registrant")
        ctx.update({"whois": info})


class CrtSh(Module):
    name = "crtsh"
    title = "Subdomains (CT logs)"
    category = "Domain"
    description = "Certificate Transparency (crt.sh, CertSpotter) + HackerTarget → subdomains."
    accepts = ("domain",)

    def run(self, ent, ctx):
        dom = ent.value
        if dom.count(".") > 2:
            return
        names, sources = set(), []
        d = get_json(f"https://crt.sh/?q=%25.{dom}&output=json", timeout=40)
        if d:
            sources.append("crt.sh")
            for row in d:
                names.update(row.get("name_value", "").split("\n"))
        d = get_json(f"https://api.certspotter.com/v1/issuances?domain={dom}&include_subdomains=true"
                     f"&expand=dns_names", timeout=30)
        if isinstance(d, list):
            sources.append("certspotter")
            for row in d:
                names.update(row.get("dns_names", []))
        try:
            r = get(f"https://api.hackertarget.com/hostsearch/?q={dom}", timeout=25)
            if r.status_code == 200 and "," in r.text:
                sources.append("hackertarget")
                names.update(line.split(",")[0] for line in r.text.splitlines())
        except Exception:
            pass
        subs = set()
        for n in names:
            n = n.strip().lower().lstrip("*.")
            if n.endswith("." + dom) and RE_DOMAIN.match(n):
                subs.add(n)
        ctx.update({"subdomain_count": len(subs), "subdomain_sources": sources})
        for s in sorted(subs)[:150]:
            ctx.emit("domain", s, rel="subdomain", pivot=False)


class Wayback(Module):
    name = "wayback"
    title = "Wayback Machine"
    category = "Domain"
    description = "First/last archive snapshots and archived URL count."
    accepts = ("domain",)

    def run(self, ent, ctx):
        rows = get_json(f"https://web.archive.org/cdx/search/cdx?url={ent.value}&output=json"
                        f"&fl=timestamp&limit=1", timeout=25)
        last = get_json(f"https://web.archive.org/cdx/search/cdx?url={ent.value}&output=json"
                        f"&fl=timestamp&limit=-1", timeout=25)
        if rows and len(rows) > 1:
            ctx.update({"wayback_first": rows[1][0], "wayback_last": (last or [[], [""]])[-1][0]})
            ctx.emit("link", f"https://web.archive.org/web/*/{ent.value}*", "Wayback archive",
                     rel="archive", pivot=False)


class WebPage(Module):
    name = "webpage"
    title = "Website scrape"
    category = "Domain"
    description = "Fetches homepage: title, server/tech headers, emails, phone numbers and social links on the page."
    accepts = ("domain", "url")

    def run(self, ent, ctx):
        url = ent.value if ent.type == "url" else f"https://{ent.value}"
        try:
            r = get(url, timeout=15)
        except Exception:
            try:
                url = url.replace("https://", "http://")
                r = get(url, timeout=15)
            except Exception as e:
                ctx.log(f"fetch failed: {e}", "warn")
                return
        html = r.text[:600000]
        title = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
        gen = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', html, re.I)
        hdr = {k: v for k, v in r.headers.items() if k.lower() in
               ("server", "x-powered-by", "via", "x-generator", "cf-ray", "x-aspnet-version")}
        ctx.update({"http_status": r.status_code, "final_url": r.url,
                    "title": title.group(1).strip()[:200] if title else None,
                    "generator": gen.group(1) if gen else None, "headers": hdr})
        host = urlparse(r.url).hostname or ""
        if ent.type == "url" and host:
            ctx.emit("domain", host.removeprefix("www."), rel="host")
        for em in set(RE_EMAIL_IN.findall(html)):
            em = em.lower()
            if not em.endswith((".png", ".jpg", ".gif", ".svg", ".webp")) and "example" not in em:
                ctx.emit("email", em, rel="found on page")
        for tel in set(re.findall(r'href=["\']tel:([+\d\s\-().]{7,20})', html)):
            ctx.emit("phone", tel.strip(), rel="found on page")
        for s in {m.group(0) for m in SOCIAL.finditer(html)}:
            ctx.emit("link", s.rstrip("/"), rel="social link", pivot=False)
        robots = None
        try:
            rr = get(urljoin(url, "/robots.txt"), timeout=8)
            if rr.status_code == 200 and "disallow" in rr.text.lower():
                robots = [l.split(":", 1)[1].strip() for l in rr.text.splitlines()
                          if l.lower().startswith("disallow") and ":" in l][:40]
        except Exception:
            pass
        if robots:
            ctx.update({"robots_disallow": robots})


class IPInfo(Module):
    name = "ipinfo"
    title = "IP geolocation & ASN"
    category = "IP"
    description = "Geolocation, ISP, ASN, reverse DNS, proxy/hosting flags (ipwho.is + PTR)."
    accepts = ("ip",)

    def run(self, ent, ctx):
        d = get_json(f"https://ipwho.is/{ent.value}") or {}
        info = {}
        if d.get("success"):
            conn = d.get("connection") or {}
            info = {"country": d.get("country"), "region": d.get("region"), "city": d.get("city"),
                    "lat": d.get("latitude"), "lon": d.get("longitude"), "isp": conn.get("isp"),
                    "org": conn.get("org"), "asn": conn.get("asn"), "timezone": (d.get("timezone") or {}).get("id")}
        try:
            ptr = socket.gethostbyaddr(ent.value)[0]
            info["ptr"] = ptr
            ctx.emit("domain", ptr, rel="reverse DNS", pivot=False)
        except Exception:
            pass
        ctx.update(info)
        if info.get("lat") is not None:
            ctx.emit("location", f"{info.get('city')}, {info.get('country')}", rel="geolocated",
                     data={"lat": info["lat"], "lon": info["lon"], "accuracy": "city-level (IP)"}, pivot=False)


class InternetDB(Module):
    name = "internetdb"
    title = "Shodan InternetDB"
    category = "IP"
    description = "Free: open ports, CPEs, known CVEs, hostnames, tags for an IP."
    accepts = ("ip",)

    def run(self, ent, ctx):
        d = get_json(f"https://internetdb.shodan.io/{ent.value}")
        if not d or "ports" not in d:
            return
        ctx.update({"ports": d.get("ports"), "tags": d.get("tags"), "cpes": d.get("cpes")})
        for p in d.get("ports", []):
            ctx.emit("port", f"{ent.value}:{p}", f"Port {p}", rel="open port", pivot=False)
        for v in d.get("vulns", [])[:50]:
            ctx.emit("vuln", v, rel="vulnerable to", data={"url": f"https://nvd.nist.gov/vuln/detail/{v}"},
                     pivot=False)
        for h in d.get("hostnames", [])[:30]:
            ctx.emit("domain", h, rel="hostname", pivot=False)


class Shodan(Module):
    name = "shodan"
    title = "Shodan (full)"
    category = "IP"
    description = "Banners, services, organisation details (requires Shodan API key)."
    accepts = ("ip",)
    requires_key = "shodan"

    def run(self, ent, ctx):
        d = get_json(f"https://api.shodan.io/shodan/host/{ent.value}?key={api_key('shodan')}")
        if not d:
            return
        ctx.update({"shodan_org": d.get("org"), "shodan_os": d.get("os"), "shodan_last": d.get("last_update")})
        for s in d.get("data", [])[:40]:
            ctx.emit("port", f"{ent.value}:{s.get('port')}", f"{s.get('port')}/{s.get('transport')} {s.get('product') or ''}",
                     {"banner": (s.get("data") or "")[:500], "product": s.get("product"),
                      "version": s.get("version")}, rel="service", pivot=False)


class VirusTotal(Module):
    name = "virustotal"
    title = "VirusTotal"
    category = "Domain"
    description = "Reputation, malicious verdicts (requires VirusTotal key)."
    accepts = ("domain", "ip")
    requires_key = "virustotal"

    def run(self, ent, ctx):
        kind = "ip_addresses" if ent.type == "ip" else "domains"
        d = get_json(f"https://www.virustotal.com/api/v3/{kind}/{ent.value}",
                     headers={"x-apikey": api_key("virustotal")})
        if d:
            a = d.get("data", {}).get("attributes", {})
            ctx.update({"vt_stats": a.get("last_analysis_stats"), "vt_reputation": a.get("reputation")})


class AbuseIPDB(Module):
    name = "abuseipdb"
    title = "AbuseIPDB"
    category = "IP"
    description = "Abuse reports and confidence score (requires AbuseIPDB key)."
    accepts = ("ip",)
    requires_key = "abuseipdb"

    def run(self, ent, ctx):
        d = get_json(f"https://api.abuseipdb.com/api/v2/check?ipAddress={ent.value}&maxAgeInDays=365",
                     headers={"Key": api_key("abuseipdb"), "Accept": "application/json"})
        if d and d.get("data"):
            x = d["data"]
            ctx.update({"abuse_score": x.get("abuseConfidenceScore"), "abuse_reports": x.get("totalReports"),
                        "usage_type": x.get("usageType"), "is_tor": x.get("isTor")})


class TheHarvester(Module):
    name = "theharvester"
    title = "theHarvester"
    category = "Domain"
    description = "Emails, names, subdomains, IPs from public sources for a domain (laramies/theHarvester)."
    accepts = ("domain",)
    requires_tool = "theHarvester"
    external = True
    homepage = "https://github.com/laramies/theHarvester"

    def run(self, ent, ctx):
        if ent.value.count(".") > 2:
            return
        with tempfile.TemporaryDirectory() as td:
            base = str(Path(td) / "h")
            run_cmd([find_tool("theHarvester"), "-d", ent.value, "-b",
                     "crtsh,duckduckgo,hackertarget,otx,rapiddns,urlscan,yahoo,certspotter", "-f", base])
            f = Path(base + ".json")
            if not f.exists():
                ctx.log("no output", "warn")
                return
            d = json.loads(f.read_text())
            for em in d.get("emails", []):
                ctx.emit("email", em.lower(), rel="harvested")
            for h in d.get("hosts", [])[:200]:
                host = h.split(":")[0]
                ctx.emit("domain", host, rel="harvested host", pivot=False)
            for ip in d.get("ips", [])[:100]:
                ctx.emit("ip", ip, rel="harvested ip", pivot=False)
            for a in d.get("asns", []):
                ctx.emit("info", a, "ASN " + a, rel="asn", pivot=False)
