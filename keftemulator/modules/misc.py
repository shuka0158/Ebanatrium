"""Phone, person/name, vehicle (VIN/plate), crypto modules."""
import re
from urllib.parse import quote

import phonenumbers
from phonenumbers import carrier, geocoder, timezone, PhoneNumberType

from ..core import Module
from ..util import get_json, find_tool, run_cmd, strip_ansi, api_key

PTYPES = {v: k for k, v in PhoneNumberType.__dict__.items() if isinstance(v, int)}


# ====================================================================== PHONE
class PhoneBasics(Module):
    name = "phone_basics"
    title = "Phone number analysis"
    category = "Phone"
    description = "Validity, country, region, carrier, line type, time zones, formats (libphonenumber) + lookup links."
    accepts = ("phone",)

    def run(self, ent, ctx):
        raw = ent.value
        try:
            n = phonenumbers.parse(raw if raw.startswith("+") else "+" + re.sub(r"\D", "", raw), None)
        except phonenumbers.NumberParseException as e:
            ctx.update({"error": str(e)})
            return
        e164 = phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.E164)
        info = {
            "valid": phonenumbers.is_valid_number(n),
            "possible": phonenumbers.is_possible_number(n),
            "e164": e164,
            "international": phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            "national": phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.NATIONAL),
            "country_code": n.country_code,
            "region": phonenumbers.region_code_for_number(n),
            "location": geocoder.description_for_number(n, "en"),
            "carrier": carrier.name_for_number(n, "en"),
            "line_type": PTYPES.get(phonenumbers.number_type(n), "UNKNOWN"),
            "timezones": list(timezone.time_zones_for_number(n)),
        }
        ctx.update(info)
        if info["location"]:
            ctx.emit("location", info["location"], rel="number region", pivot=False,
                     data={"query": info["location"], "accuracy": "region of numbering plan"})
        digits = e164.lstrip("+")
        nat = re.sub(r"\D", "", info["national"])
        links = [
            ("WhatsApp", f"https://wa.me/{digits}"),
            ("Telegram", f"https://t.me/+{digits}"),
            ("Viber", f"viber://chat?number=%2B{digits}"),
            ("Google", f"https://www.google.com/search?q=%22{quote(e164)}%22+OR+%22{nat}%22+OR+%22{quote(info['international'])}%22"),
            ("Truecaller", f"https://www.truecaller.com/search/{info['region'].lower() if info['region'] else 'us'}/{nat}"),
            ("Sync.me", f"https://sync.me/search/?number={digits}"),
            ("NumLookup", f"https://www.numlookup.com/?number={digits}"),
            ("Facebook", f"https://www.facebook.com/search/top?q={quote(e164)}"),
        ]
        for t, u in links:
            ctx.emit("link", u, f"{t}: {e164}", {"kind": "lookup"}, rel="lookup", pivot=False)
        if info["region"] == "GE":
            self.georgia(nat, ctx)

    @staticmethod
    def georgia(nat, ctx):
        """Georgian sources: caller-ID base + sites where numbers are published (ads, jobs)."""
        n = nat.lstrip("0")  # 9 digits, e.g. 555123456
        forms = [n, f"{n[:3]} {n[3:5]} {n[5:7]} {n[7:]}", f"{n[:3]}-{n[3:5]}-{n[5:7]}-{n[7:]}",
                 f"{n[:3]} {n[3:6]} {n[6:]}", f"+995{n}", f"+995 {n[:3]} {n[3:5]} {n[5:7]} {n[7:]}"]
        anyform = "+OR+".join(quote(f'"{f}"') for f in forms)
        ctx.update({"ge_formats": forms,
                    "nomrebi_tip": f"nomrebi.com has no search URL: paste {n} into its search box"})
        links = [
            ("nomrebi.com — caller-ID base (paste number)", "https://nomrebi.com/?lang=geo"),
            ("Google (all GE formats)", f"https://www.google.com/search?q={anyform}"),
            ("ss.ge / myhome.ge (real-estate ads)", f"https://www.google.com/search?q=({anyform})+(site:ss.ge+OR+site:myhome.ge)"),
            ("myauto.ge / mymarket.ge (car & market ads)", f"https://www.google.com/search?q=({anyform})+(site:myauto.ge+OR+site:mymarket.ge)"),
            ("jobs.ge / hr.ge (job posts)", f"https://www.google.com/search?q=({anyform})+(site:jobs.ge+OR+site:hr.ge)"),
            ("Facebook (Georgian formats)", f"https://www.google.com/search?q=({anyform})+site:facebook.com"),
        ]
        for t, u in links:
            ctx.emit("link", u, t, {"kind": "lookup", "country": "GE"}, rel="lookup (GE)", pivot=False)


class NumVerify(Module):
    name = "numverify"
    title = "NumVerify"
    category = "Phone"
    description = "Live carrier/line-type validation (requires numverify/apilayer key)."
    accepts = ("phone",)
    requires_key = "numverify"

    def run(self, ent, ctx):
        num = re.sub(r"\D", "", ent.value)
        d = get_json(f"http://apilayer.net/api/validate?access_key={api_key('numverify')}&number={num}")
        if d and d.get("valid") is not None:
            ctx.update({"nv_valid": d.get("valid"), "nv_carrier": d.get("carrier"),
                        "nv_line_type": d.get("line_type"), "nv_location": d.get("location")})


class PhoneInfoga(Module):
    name = "phoneinfoga"
    title = "PhoneInfoga"
    category = "Phone"
    description = "Advanced phone scanning: local/numverify/googlesearch/OVH scanners (sundowndev/phoneinfoga)."
    accepts = ("phone",)
    requires_tool = "phoneinfoga"
    external = True
    homepage = "https://github.com/sundowndev/phoneinfoga"

    def run(self, ent, ctx):
        num = "+" + re.sub(r"\D", "", ent.value)
        code, out = run_cmd([find_tool("phoneinfoga"), "scan", "-n", num])
        out = strip_ansi(out)
        ctx.update({"phoneinfoga_report": out[-6000:]})
        for url in set(re.findall(r"https?://\S+", out)):
            ctx.emit("link", url.rstrip(".,)"), rel="phoneinfoga dork", pivot=False)


# ====================================================================== PERSON
class PersonSearch(Module):
    name = "person"
    title = "Person / bio lookup"
    category = "Person"
    description = ("Wikipedia/Wikidata biography (public figures), username permutations, "
                   "social-platform people search and search-engine dorks.")
    accepts = ("name",)

    def run(self, ent, ctx):
        name = ent.value.strip()
        self.wikidata(name, ctx)
        parts = [p for p in re.split(r"\s+", name.lower()) if p.isalpha()]
        if len(parts) >= 2:
            f, l = parts[0], parts[-1]
            for u in dict.fromkeys([f + l, f + "." + l, f + "_" + l, f[0] + l, f + l[0], l + f, l + "." + f]):
                ctx.emit("username", u, rel="possible username", data={"generated": True}, pivot=False)
        q = quote(f'"{name}"')
        links = [
            ("Google", f"https://www.google.com/search?q={q}"),
            ("Google Images", f"https://www.google.com/search?tbm=isch&q={q}"),
            ("Bing", f"https://www.bing.com/search?q={q}"),
            ("Yandex", f"https://yandex.com/search/?text={q}"),
            ("LinkedIn", f"https://www.linkedin.com/search/results/people/?keywords={quote(name)}"),
            ("Facebook", f"https://www.facebook.com/search/people/?q={quote(name)}"),
            ("Instagram (Google)", f"https://www.google.com/search?q=site:instagram.com+{q}"),
            ("X / Twitter", f"https://x.com/search?q={q}&f=user"),
            ("VK", f"https://vk.com/search?c%5Bq%5D={quote(name)}&c%5Bsection%5D=people"),
            ("Documents (pdf/doc)", f"https://www.google.com/search?q={q}+filetype:pdf+OR+filetype:doc+OR+filetype:docx"),
            ("CV / Resume", f"https://www.google.com/search?q={q}+(resume+OR+cv+OR+curriculum)"),
            ("News", f"https://news.google.com/search?q={q}"),
            ("OpenCorporates (officer)", f"https://opencorporates.com/officers?q={quote(name)}"),
            ("Court/Gov (Google)", f"https://www.google.com/search?q={q}+site:gov+OR+site:court"),
        ]
        for t, u in links:
            ctx.emit("link", u, f"{t}: {name}", {"kind": "search"}, rel="search", pivot=False)

    def wikidata(self, name, ctx):
        h = {"User-Agent": "Keftemulator/1.0 (OSINT research tool; python-requests)"}
        d = get_json(f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={quote(name)}"
                     f"&language=en&type=item&limit=3&format=json", headers=h)
        for hit in (d or {}).get("search", [])[:3]:
            desc = hit.get("description", "")
            if not desc:
                continue
            ent = get_json(f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={hit['id']}"
                           f"&props=claims&format=json", headers=h)
            claims = ((ent or {}).get("entities", {}).get(hit["id"], {}) or {}).get("claims", {})
            if "Q5" not in [c["mainsnak"].get("datavalue", {}).get("value", {}).get("id") for c in claims.get("P31", [])]:
                continue  # not a human

            def val(p):
                out = []
                for c in claims.get(p, []):
                    v = c["mainsnak"].get("datavalue", {}).get("value")
                    if isinstance(v, dict):
                        v = v.get("time") or v.get("id") or v.get("text")
                    if v:
                        out.append(str(v).lstrip("+").split("T")[0])
                return out
            bio = {"description": desc, "wikidata": f"https://www.wikidata.org/wiki/{hit['id']}",
                   "born": val("P569"), "died": val("P570"), "twitter": val("P2002"),
                   "instagram": val("P2003"), "facebook": val("P2013"), "github": val("P2037"),
                   "website": val("P856"), "youtube": val("P2397"), "telegram": val("P3789")}
            wp = get_json(f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(hit.get('label', name))}",
                          headers=h)
            if wp and wp.get("extract"):
                bio["summary"] = wp["extract"]
                bio["avatar"] = (wp.get("thumbnail") or {}).get("source")
            pid = ctx.emit("profile", bio["wikidata"], f"Wikidata: {hit.get('label')} — {desc}", bio,
                           rel="public profile", pivot=False)
            for k in ("twitter", "instagram", "github", "telegram"):
                for h in bio.get(k) or []:
                    ctx.emit("username", h, rel=f"{k} (wikidata)", parent=pid)
            for w in bio.get("website") or []:
                ctx.emit("url", w, rel="official site", parent=pid)


# ====================================================================== VEHICLE
class VINDecode(Module):
    name = "vin"
    title = "VIN decoder + recalls"
    category = "Vehicle"
    description = "Decodes a 17-char VIN (make, model, year, engine, plant) via NHTSA vPIC, plus safety recalls."
    accepts = ("vin",)

    def run(self, ent, ctx):
        vin = ent.value.upper()
        d = get_json(f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}?format=json", timeout=25)
        r = ((d or {}).get("Results") or [{}])[0]
        keep = ["Make", "Model", "ModelYear", "Trim", "BodyClass", "VehicleType", "DriveType",
                "EngineCylinders", "DisplacementL", "FuelTypePrimary", "TransmissionStyle", "Doors",
                "Manufacturer", "PlantCountry", "PlantCity", "Series", "ErrorText"]
        info = {k: r.get(k) for k in keep if r.get(k)}
        info["checksum_ok"] = self.checksum(vin)
        ctx.update(info)
        if r.get("Make") and r.get("Model") and r.get("ModelYear"):
            rc = get_json(f"https://api.nhtsa.gov/recalls/recallsByVehicle?make={quote(r['Make'])}"
                          f"&model={quote(r['Model'])}&modelYear={r['ModelYear']}")
            for x in (rc or {}).get("results", [])[:30]:
                ctx.emit("info", f"recall:{x.get('NHTSACampaignNumber')}", f"Recall {x.get('NHTSACampaignNumber')}: {x.get('Component')}",
                         {"summary": x.get("Summary"), "date": x.get("ReportReceivedDate")}, rel="recall", pivot=False)
        for t, u in [("Google", f"https://www.google.com/search?q=%22{vin}%22"),
                     ("Copart/IAAI auctions (Google)", f"https://www.google.com/search?q=%22{vin}%22+copart+OR+iaai"),
                     ("NICB VINCheck (theft/salvage, US)", "https://www.nicb.org/vincheck"),
                     ("Carfax", f"https://www.carfax.com/vehicle/{vin}")]:
            ctx.emit("link", u, t, rel="lookup", pivot=False)

    @staticmethod
    def checksum(vin):
        tr = {**{str(i): i for i in range(10)}, **dict(zip("ABCDEFGH", range(1, 9))),
              **dict(zip("JKLMN", range(1, 6))), "P": 7, "R": 9, **dict(zip("STUVWXYZ", range(2, 10)))}
        w = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
        try:
            s = sum(tr[c] * w[i] for i, c in enumerate(vin)) % 11
        except KeyError:
            return False
        return vin[8] == ("X" if s == 10 else str(s))


PLATE_FORMATS = [
    ("Georgia", r"^[A-Z]{2}-?\d{3}-?[A-Z]{2}$"),
    ("Ukraine", r"^[ABCEHIKMOPTX]{2}\d{4}[ABCEHIKMOPTX]{2}$"),
    ("Russia", r"^[ABEKMHOPCTYX]\d{3}[ABEKMHOPCTYX]{2}\d{2,3}$"),
    ("Armenia", r"^\d{2}[A-Z]{2}\d{3}$"),
    ("Azerbaijan", r"^\d{2}-?[A-Z]{2}-?\d{3}$"),
    ("Turkey", r"^\d{2}\s?[A-Z]{1,3}\s?\d{2,4}$"),
    ("Germany", r"^[A-ZÄÖÜ]{1,3}-?[A-Z]{1,2}-?\d{1,4}[EH]?$"),
    ("United Kingdom", r"^[A-Z]{2}\d{2}\s?[A-Z]{3}$"),
    ("France", r"^[A-Z]{2}-?\d{3}-?[A-Z]{2}$"),
    ("Italy", r"^[A-Z]{2}\d{3}[A-Z]{2}$"),
    ("Spain", r"^\d{4}\s?[BCDFGHJKLMNPRSTVWXYZ]{3}$"),
    ("Poland", r"^[A-Z]{2,3}\s?[0-9A-Z]{4,5}$"),
    ("Netherlands", r"^[A-Z0-9]{2}-?[A-Z0-9]{2,3}-?[A-Z0-9]{1,2}$"),
    ("USA (varies by state)", r"^[A-Z0-9]{2,8}$"),
]


class PlateInfo(Module):
    name = "plate"
    title = "License plate analysis"
    category = "Vehicle"
    description = ("Identifies likely country/format of a plate and builds search links "
                   "(public photo sightings, platesmania, forums). Registered-owner records are not public.")
    accepts = ("plate",)

    def run(self, ent, ctx):
        p = re.sub(r"[\s.]", "", ent.value.upper())
        matches = [c for c, rx in PLATE_FORMATS if re.match(rx, p)]
        ctx.update({"normalized": p, "possible_countries": matches,
                    "note": "Owner identity is held in government registries (protected by law); "
                            "use official channels / police report if needed."})
        if "Georgia" in matches:
            self.georgia(p, ctx)
        q = quote(f'"{ent.value}" OR "{p}"')
        for t, u in [("Google", f"https://www.google.com/search?q={q}"),
                     ("Google Images", f"https://www.google.com/search?tbm=isch&q={q}"),
                     ("Yandex Images", f"https://yandex.com/images/search?text={quote(p)}"),
                     ("Platesmania", f"https://platesmania.com/search?q={quote(p)}"),
                     ("Facebook posts", f"https://www.facebook.com/search/posts/?q={quote(p)}"),
                     ("UK: DVLA vehicle check (official)", "https://vehicleenquiry.service.gov.uk/"),
                     ("US: VIN via plate (faxvin)", "https://www.faxvin.com/license-plate-lookup")]:
            ctx.emit("link", u, t, rel="lookup", pivot=False)


    @staticmethod
    def georgia(p, ctx):
        """Georgian plate (AA-123-AA): public sightings + official self-service checks."""
        raw = p.replace("-", "")
        dashed = f"{raw[:2]}-{raw[2:5]}-{raw[5:]}"
        forms = [dashed, raw, f"{raw[:2]} {raw[2:5]} {raw[5:]}"]
        anyform = "+OR+".join(quote(f'"{f}"') for f in forms)
        ctx.update({"ge_formats": forms, "ge_note": (
            "Georgian owner records (MIA Service Agency) are protected personal data. Official checks "
            "below need the plate + tech-passport number, i.e. they are for the owner or with consent.")})
        for t, u in [
            ("GE: Google (all plate formats)", f"https://www.google.com/search?q={anyform}"),
            ("GE: Google Images", f"https://www.google.com/search?tbm=isch&q={anyform}"),
            ("GE: Facebook groups/posts", f"https://www.google.com/search?q=({anyform})+site:facebook.com"),
            ("GE: myauto.ge listings", f"https://www.google.com/search?q=({anyform})+site:myauto.ge"),
            ("GE: Platesmania (Google)", f"https://www.google.com/search?q=({anyform})+site:platesmania.com"),
            ("GE: Police fines & photos (official, needs tech passport no.)", "https://videos.police.ge/"),
            ("GE: Service Agency vehicle services (official)", "https://sa.gov.ge/"),
        ]:
            ctx.emit("link", u, t, {"kind": "lookup", "country": "GE"}, rel="lookup (GE)", pivot=False)
        # Live embed: loads in the viewer's own browser (the server is blocked by Cloudflare).
        pm = "https://platesmania.com/ge/gallery.php?fastsearch="
        ctx.emit("link", pm + quote(dashed), "Platesmania Georgia — vehicle photos", {
            "kind": "embed", "url": pm + quote(dashed),
            "embed": {"title": "Platesmania Georgia — vehicle photos", "variants": [[f, pm + quote(f)] for f in forms]}},
            rel="live search", pivot=False)


# ====================================================================== CRYPTO
class BTCAddress(Module):
    name = "btc"
    title = "Bitcoin address"
    category = "Crypto"
    description = "Balance, tx count, first/last activity, counterparties (blockstream.info)."
    accepts = ("btc",)

    def run(self, ent, ctx):
        a = ent.value
        d = get_json(f"https://blockstream.info/api/address/{a}")
        if not d:
            return
        cs = d.get("chain_stats", {})
        ctx.update({"tx_count": cs.get("tx_count"),
                    "received_btc": cs.get("funded_txo_sum", 0) / 1e8,
                    "sent_btc": cs.get("spent_txo_sum", 0) / 1e8,
                    "balance_btc": (cs.get("funded_txo_sum", 0) - cs.get("spent_txo_sum", 0)) / 1e8})
        txs = get_json(f"https://blockstream.info/api/address/{a}/txs") or []
        peers = {}
        for t in txs[:25]:
            for vin in t.get("vin", []):
                ad = (vin.get("prevout") or {}).get("scriptpubkey_address")
                if ad and ad != a:
                    peers[ad] = peers.get(ad, 0) + 1
            for vo in t.get("vout", []):
                ad = vo.get("scriptpubkey_address")
                if ad and ad != a:
                    peers[ad] = peers.get(ad, 0) + 1
        for ad, c in sorted(peers.items(), key=lambda x: -x[1])[:15]:
            ctx.emit("btc", ad, rel=f"transacted ({c})", data={"tx_together": c}, pivot=False)
        ctx.emit("link", f"https://www.blockchain.com/explorer/addresses/btc/{a}", "Blockchain.com explorer",
                 rel="explorer", pivot=False)


class ETHAddress(Module):
    name = "eth"
    title = "Ethereum address"
    category = "Crypto"
    description = "Balance and ENS reverse name (public RPC)."
    accepts = ("eth",)

    def run(self, ent, ctx):
        from ..util import http
        try:
            r = http().post("https://ethereum-rpc.publicnode.com", timeout=15, json={
                "jsonrpc": "2.0", "id": 1, "method": "eth_getBalance", "params": [ent.value, "latest"]}).json()
            ctx.update({"balance_eth": int(r["result"], 16) / 1e18})
        except Exception as e:
            ctx.log(f"rpc: {e}", "warn")
        ens = get_json(f"https://api.ensideas.com/ens/resolve/{ent.value}")
        if ens and ens.get("name"):
            ctx.emit("domain", ens["name"], rel="ENS name", pivot=False)
        for t, u in [("Etherscan", f"https://etherscan.io/address/{ent.value}")]:
            ctx.emit("link", u, t, rel="explorer", pivot=False)
