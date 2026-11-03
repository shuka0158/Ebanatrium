"""Wrappers for full OSINT frameworks: SpiderFoot and Recon-ng."""
import json
import sqlite3
from pathlib import Path

from ..core import Module
from ..util import find_tool, run_cmd, strip_ansi

SF_MAP = {"EMAILADDR": "email", "IP_ADDRESS": "ip", "IPV6_ADDRESS": "ip", "INTERNET_NAME": "domain",
          "DOMAIN_NAME": "domain", "PHONE_NUMBER": "phone", "HUMAN_NAME": "name", "USERNAME": "username",
          "SOCIAL_MEDIA": "account", "ACCOUNT_EXTERNAL_OWNED": "account", "GEOINFO": "location",
          "PHYSICAL_ADDRESS": "location", "BITCOIN_ADDRESS": "btc", "ETHEREUM_ADDRESS": "eth",
          "LINKED_URL_EXTERNAL": "link", "VULNERABILITY_CVE_CRITICAL": "vuln", "VULNERABILITY_CVE_HIGH": "vuln",
          "TCP_PORT_OPEN": "port", "EMAILADDR_COMPROMISED": "breach", "LEAKSITE_CONTENT": "breach",
          "AFFILIATE_INTERNET_NAME": "domain", "CO_HOSTED_SITE": "domain", "SIMILARDOMAIN": "domain"}


class SpiderFoot(Module):
    name = "spiderfoot"
    title = "SpiderFoot (passive, 200+ modules)"
    category = "Framework"
    description = ("Runs a full SpiderFoot passive scan on the target and imports every event "
                   "into the graph. Slow (minutes) but very broad.")
    accepts = ("domain", "ip", "email", "username", "phone", "name", "btc")
    requires_tool = "spiderfoot"
    default = True
    external = True
    homepage = "https://github.com/smicallef/spiderfoot"

    def run(self, ent, ctx):
        if ent.depth > 0:
            return  # only on the root target: SpiderFoot recurses on its own
        target = f'"{ent.value}"' if ent.type in ("name", "username") else ent.value
        code, out = run_cmd([find_tool("spiderfoot"), "-s", target, "-u", "passive", "-o", "json", "-q"],
                            timeout=1800)
        events = []
        txt = out.strip()
        try:
            events = json.loads(txt[txt.index("["):]) if "[" in txt else []
        except ValueError:
            for line in txt.splitlines():
                try:
                    events.append(json.loads(line.strip().rstrip(",")))
                except ValueError:
                    pass
        n = 0
        for e in events:
            if not isinstance(e, dict):
                continue
            t = SF_MAP.get(e.get("type"))
            data = e.get("data", "")
            if not t or not data or len(data) > 400:
                continue
            n += 1
            ctx.emit(t, data, data={"sf_type": e.get("type"), "sf_module": e.get("module"),
                                    "sf_source": e.get("source")}, rel=f"sf:{e.get('module', '')}", pivot=False)
        ctx.log(f"imported {n} SpiderFoot events")


RECON_MODULES = {
    "domain": ["recon/domains-hosts/hackertarget", "recon/domains-hosts/certificate_transparency"],
}


class ReconNG(Module):
    name = "reconng"
    title = "Recon-ng"
    category = "Framework"
    description = "Runs Recon-ng marketplace modules (hackertarget, certificate_transparency) and imports hosts."
    accepts = ("domain",)
    requires_tool = "recon-cli"
    default = True
    external = True
    homepage = "https://github.com/lanmaster53/recon-ng"

    def run(self, ent, ctx):
        if ent.depth > 0:
            return
        ws = f"keft_{ctx.scan.id}"
        for mod in RECON_MODULES["domain"]:
            code, out = run_cmd([find_tool("recon-cli"), "-w", ws, "-m", mod, "-o", f"SOURCE={ent.value}", "-x"],
                                timeout=600)
            if "Invalid module" in out or "not found" in out.lower():
                ctx.log(f"{mod} not installed in recon-ng marketplace", "warn")
        dbf = Path.home() / ".recon-ng" / "workspaces" / ws / "data.db"
        if not dbf.exists():
            ctx.log("no workspace db", "warn")
            return
        con = sqlite3.connect(dbf)
        for host, ip in con.execute("SELECT host, ip_address FROM hosts"):
            nid = ctx.emit("domain", host, rel="recon-ng host", pivot=False)
            if ip:
                ctx.emit("ip", ip, rel="resolves to", parent=nid, pivot=False)
        con.close()
