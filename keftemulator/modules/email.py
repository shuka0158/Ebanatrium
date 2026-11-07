"""Email intelligence: validation, MX, Gravatar, breaches, holehe registrations."""
import hashlib
import re

import dns.resolver

from ..core import Module
from ..util import get, get_json, find_tool, run_cmd, strip_ansi, api_key

DISPOSABLE = {"mailinator.com", "10minutemail.com", "guerrillamail.com", "tempmail.com", "temp-mail.org",
              "yopmail.com", "trashmail.com", "getnada.com", "sharklasers.com", "dispostable.com",
              "maildrop.cc", "throwawaymail.com", "fakeinbox.com", "mintemail.com", "emailondeck.com"}
FREE = {"gmail.com", "googlemail.com", "yahoo.com", "outlook.com", "hotmail.com", "live.com", "icloud.com",
        "me.com", "aol.com", "proton.me", "protonmail.com", "gmx.com", "gmx.de", "mail.ru", "yandex.ru",
        "yandex.com", "zoho.com", "tutanota.com", "mail.com", "inbox.ru", "bk.ru", "list.ru", "ukr.net"}


class EmailBasics(Module):
    name = "email_basics"
    title = "Email analysis"
    category = "Email"
    description = "Syntax, MX records, provider type, disposable check; pivots to domain and username part."
    accepts = ("email",)

    def run(self, ent, ctx):
        e = ent.value.lower()
        local, _, dom = e.partition("@")
        info = {"local_part": local, "domain": dom, "free_provider": dom in FREE,
                "disposable": dom in DISPOSABLE}
        try:
            mx = sorted(dns.resolver.resolve(dom, "MX", lifetime=8), key=lambda r: r.preference)
            info["mx"] = [str(r.exchange).rstrip(".") for r in mx]
            info["deliverable_domain"] = True
        except Exception:
            info["mx"] = []
            info["deliverable_domain"] = False
        ctx.update(info)
        if dom not in FREE and dom not in DISPOSABLE:
            ctx.emit("domain", dom, rel="email domain")
        base = re.sub(r"[+].*$", "", local)
        if len(base) >= 4 and re.match(r"^[a-z0-9._\-]+$", base):
            ctx.emit("username", base, rel="local part (possible username)")
        # Search links
        q = f'"{e}"'
        for t, u in [("Google", f"https://www.google.com/search?q={q}"),
                     ("Bing", f"https://www.bing.com/search?q={q}"),
                     ("DuckDuckGo", f"https://duckduckgo.com/?q={q}"),
                     ("Pastebin search (Google)", f"https://www.google.com/search?q=site:pastebin.com+{q}"),
                     ("Epieos (Google acct)", "https://epieos.com/?q=" + e),
                     ("IntelX", "https://intelx.io/?s=" + e)]:
            ctx.emit("link", u, f"{t}: {e}", {"kind": "search"}, rel="search", pivot=False)


class Gravatar(Module):
    name = "gravatar"
    title = "Gravatar profile"
    category = "Email"
    description = "Looks up the public Gravatar profile tied to the email (photo, name, linked accounts)."
    accepts = ("email",)

    def run(self, ent, ctx):
        e = ent.value.strip().lower()
        h = hashlib.sha256(e.encode()).hexdigest()
        d = get_json(f"https://api.gravatar.com/v3/profiles/{h}")
        if d and d.get("profile_url"):
            pid = ctx.emit("account", d["profile_url"], f"Gravatar: {d.get('display_name')}", {
                "site": "Gravatar", "url": d["profile_url"], "name": d.get("display_name"),
                "bio": d.get("description"), "location": d.get("location"), "job": d.get("job_title"),
                "company": d.get("company"), "avatar": d.get("avatar_url")}, rel="has account")
            if d.get("display_name"):
                ctx.emit("name", d["display_name"], rel="real name", parent=pid)
            if d.get("location"):
                ctx.emit("location", d["location"], rel="location", parent=pid)
            for a in d.get("verified_accounts") or []:
                ctx.emit("account", a.get("url"), f"{a.get('service_label')}: {a.get('url')}",
                         {"site": a.get("service_label"), "url": a.get("url")}, rel="verified account",
                         parent=pid, pivot=False)
            return
        md5 = hashlib.md5(e.encode()).hexdigest()
        r = get(f"https://www.gravatar.com/avatar/{md5}?d=404", timeout=10)
        if r.status_code == 200:
            ctx.emit("image_url", f"https://www.gravatar.com/avatar/{md5}?s=400", "Gravatar avatar",
                     {"note": "Avatar exists"}, rel="avatar", pivot=False)


class Holehe(Module):
    name = "holehe"
    title = "holehe"
    category = "Email"
    description = "Checks if the email is registered on 120+ sites via password-reset flows (megadose/holehe)."
    accepts = ("email",)
    requires_tool = "holehe"
    external = True
    homepage = "https://github.com/megadose/holehe"

    def run(self, ent, ctx):
        code, out = run_cmd([find_tool("holehe"), ent.value, "--only-used", "--no-color", "--no-clear"])
        n = 0
        for line in strip_ansi(out).splitlines():
            m = re.match(r"\[\+\]\s+(\S+)(.*)$", line.strip())
            if m and "Email used" not in line:
                n += 1
                extra = m.group(2).strip(" /")
                ctx.emit("account", f"{m.group(1)} ← {ent.value}", f"Registered: {m.group(1)}",
                         {"site": m.group(1), "details": extra, "source": "holehe"},
                         rel="registered on", pivot=False)
        ctx.log(f"{n} registrations for {ent.value}")


class HIBP(Module):
    name = "hibp"
    title = "Have I Been Pwned"
    category = "Email"
    description = "Data breaches and pastes containing this email (requires HIBP API key)."
    accepts = ("email",)
    requires_key = "hibp"
    homepage = "https://haveibeenpwned.com/API/Key"

    def run(self, ent, ctx):
        h = {"hibp-api-key": api_key("hibp"), "user-agent": "Keftemulator-OSINT"}
        r = get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{ent.value}?truncateResponse=false",
                headers=h)
        if r.status_code == 200:
            for b in r.json():
                ctx.emit("breach", f"{b['Name']}:{ent.value}", f"Breach: {b['Title']}", {
                    "breach": b["Title"], "domain": b.get("Domain"), "date": b.get("BreachDate"),
                    "pwn_count": b.get("PwnCount"), "data_classes": b.get("DataClasses"),
                    "verified": b.get("IsVerified")}, rel="in breach", pivot=False)
        elif r.status_code not in (404,):
            ctx.log(f"HIBP HTTP {r.status_code}", "warn")


class Hunter(Module):
    name = "hunter"
    title = "Hunter.io"
    category = "Email"
    description = "Email verification, and domain search for employee emails (requires Hunter key)."
    accepts = ("email", "domain")
    requires_key = "hunter"

    def run(self, ent, ctx):
        k = api_key("hunter")
        if ent.type == "email":
            d = get_json(f"https://api.hunter.io/v2/email-verifier?email={ent.value}&api_key={k}")
            if d and d.get("data"):
                ctx.update({"hunter_status": d["data"].get("status"), "hunter_score": d["data"].get("score")})
        else:
            d = get_json(f"https://api.hunter.io/v2/domain-search?domain={ent.value}&limit=50&api_key={k}")
            for em in ((d or {}).get("data") or {}).get("emails", []):
                nid = ctx.emit("email", em["value"], rel="employee email", data={
                    "first_name": em.get("first_name"), "last_name": em.get("last_name"),
                    "position": em.get("position"), "confidence": em.get("confidence")})
                full = " ".join(filter(None, [em.get("first_name"), em.get("last_name")]))
                if full:
                    ctx.emit("name", full, rel="owner", parent=nid)


class FreeBreaches(Module):
    name = "breaches_free"
    title = "Breach check (free)"
    category = "Email"
    description = ("Data breaches containing this email, no API key needed: XposedOrNot (breach name, date, "
                   "exposed data types) and LeakCheck public (leak sources + exposed field names).")
    accepts = ("email",)

    def run(self, ent, ctx):
        e = ent.value
        seen = set()
        d = get_json(f"https://api.xposedornot.com/v1/breach-analytics?email={e}", timeout=25)
        for b in (((d or {}).get("ExposedBreaches") or {}).get("breaches_details") or []):
            seen.add(b["breach"].lower())
            ctx.emit("breach", f"{b['breach']}:{e}", f"Breach: {b['breach']}", {
                "breach": b["breach"], "domain": b.get("domain"), "date": b.get("xposed_date"),
                "records": b.get("xposed_records"), "data_classes": (b.get("xposed_data") or "").split(";"),
                "password_risk": b.get("password_risk"), "verified": b.get("verified"),
                "description": b.get("details"), "source": "XposedOrNot"}, rel="in breach", pivot=False)
        d = get_json(f"https://leakcheck.io/api/public?check={e}", timeout=25)
        if d and d.get("success"):
            ctx.update({"leakcheck_found": d.get("found"), "leakcheck_fields": d.get("fields")})
            for s in d.get("sources") or []:
                nm = s.get("name") or "Unknown"
                if nm.lower().split(".")[0] in seen or nm.lower() in seen:
                    continue
                ctx.emit("breach", f"{nm}:{e}", f"Leak: {nm}", {"breach": nm, "date": s.get("date"),
                         "source": "LeakCheck"}, rel="in leak", pivot=False)
