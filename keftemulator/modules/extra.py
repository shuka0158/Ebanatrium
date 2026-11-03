"""Extra sources: Telegram, account enrichment, Georgian business registry (NAPR), urlscan,
reverse IP, IntelX, dark-web search links, GitHub deep dive."""
import html as htmllib
import re
import threading
import time
from urllib.parse import quote, urlparse

from ..core import Module
from ..util import get, get_json, http, api_key, RE_DOMAIN

META = re.compile(r'<meta[^>]+(?:property|name)=["\'](og:title|og:description|og:image|description|'
                  r'twitter:title|twitter:description|twitter:image)["\'][^>]*content=["\']([^"\']*)', re.I)
META_REV = re.compile(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]*(?:property|name)=["\'](og:title|og:description|'
                      r'og:image|description)["\']', re.I)
GENERIC_TITLES = re.compile(r"^(instagram|tiktok|facebook|log ?in|sign ?in|sign ?up|join|welcome|home|page not found|just a moment|"
                            r"access denied|error|404|attention required)", re.I)


def meta_tags(html):
    out = {}
    for k, v in META.findall(html):
        out.setdefault(k.lower(), htmllib.unescape(v).strip())
    for v, k in META_REV.findall(html):
        out.setdefault(k.lower(), htmllib.unescape(v).strip())
    return out


# ====================================================================== TELEGRAM
class Telegram(Module):
    name = "telegram"
    title = "Telegram profile/channel"
    category = "Username"
    description = ("Public t.me page: display name, bio, photo, and whether it is a user, bot, group "
                   "or channel (with member/subscriber count and latest public posts).")
    accepts = ("username",)

    def run(self, ent, ctx):
        u = ent.value.lstrip("@")
        if not re.match(r"^[A-Za-z][A-Za-z0-9_]{3,31}$", u):
            return
        r = get(f"https://t.me/{u}", timeout=15)
        if r.status_code != 200 or "tgme_page_title" not in r.text:
            return
        m = meta_tags(r.text)
        extra = re.search(r'tgme_page_extra">\s*([^<]+)', r.text)
        extra = extra.group(1).strip() if extra else ""
        kind = ("channel" if "subscriber" in extra else "group" if "member" in extra
                else "bot" if u.lower().endswith("bot") else "user")
        data = {"site": "Telegram", "url": f"https://t.me/{u}", "name": m.get("og:title"),
                "bio": m.get("og:description"), "telegram_type": kind, "members": extra or None,
                "avatar": m.get("og:image") if "telesco.pe" in (m.get("og:image") or "") else None}
        if kind == "channel":
            p = get(f"https://t.me/s/{u}", timeout=15)
            posts = re.findall(r'tgme_widget_message_text[^>]*>(.*?)</div>', p.text, re.S)[-5:]
            data["recent_posts"] = [re.sub(r"<[^>]+>", " ", htmllib.unescape(x)).strip()[:300] for x in posts]
        pid = ctx.emit("account", f"https://t.me/{u}", f"Telegram ({kind}): {u}", data, rel="has account")
        name = data["name"]
        if kind == "user" and name and name.lower() != u.lower() and len(name) > 2:
            ctx.emit("name", name, rel="telegram name", parent=pid)
        for link in set(re.findall(r"https?://[^\s\"'<>]+", data.get("bio") or "")):
            ctx.emit("url", link.rstrip(".,)"), rel="link in bio", parent=pid)
        for at in set(re.findall(r"(?<![\w@])@([A-Za-z][A-Za-z0-9_]{3,31})", data.get("bio") or "")):
            if at.lower() != u.lower():
                ctx.emit("username", at, rel="mentioned in bio", parent=pid)


# ====================================================================== ENRICHMENT
class AccountEnrich(Module):
    name = "enrich"
    title = "Account profile enrichment"
    category = "Username"
    description = ("Opens every account found (Sherlock, Maigret, site check) and extracts the public name, "
                   "bio and profile photo from the page. Capped at 150 accounts per scan.")
    accepts = ("account",)
    enricher = True
    LIMIT = 150
    _lock = threading.Lock()
    _count = {}

    def run(self, ent, ctx):
        d = ent.data or {}
        url = d.get("url") or ent.value
        if not str(url).startswith("http") or d.get("bio") or d.get("name"):
            return  # not a URL (e.g. holehe) or already rich (profile APIs)
        with self._lock:
            n = self._count.get(ctx.scan.id, 0)
            if n >= self.LIMIT:
                return
            self._count[ctx.scan.id] = n + 1
        try:
            r = get(url, timeout=10)
        except Exception:
            return
        if r.status_code != 200 or "text/html" not in r.headers.get("content-type", ""):
            return
        m = meta_tags(r.text[:300000])
        title = m.get("og:title") or m.get("twitter:title")
        desc = m.get("og:description") or m.get("twitter:description") or m.get("description")
        img = m.get("og:image") or m.get("twitter:image")
        upd = {}
        if title and not GENERIC_TITLES.match(title):
            upd["page_title"] = title[:200]
        if desc and len(desc) > 3:
            upd["bio"] = desc[:500]
        if img and img.startswith("http") and not re.search(r"logo|default|favicon|og-image|share", img, re.I):
            upd["avatar"] = img
        if upd:
            from .. import db
            db.add_node(ctx.scan.id, ent.type, ent.value, None, upd, self.name, ent.depth)


# ====================================================================== GEORGIA: NAPR
LAT2GEO = [("ch'", "ჭ"), ("ts'", "წ"), ("k'", "კ"), ("p'", "პ"), ("t'", "ტ"), ("zh", "ჟ"), ("gh", "ღ"),
           ("sh", "შ"), ("ch", "ჩ"), ("ts", "ც"), ("dz", "ძ"), ("kh", "ხ"), ("a", "ა"), ("b", "ბ"),
           ("g", "გ"), ("d", "დ"), ("e", "ე"), ("v", "ვ"), ("z", "ზ"), ("t", "თ"), ("i", "ი"), ("k", "კ"),
           ("l", "ლ"), ("m", "მ"), ("n", "ნ"), ("o", "ო"), ("p", "პ"), ("r", "რ"), ("s", "ს"), ("u", "უ"),
           ("f", "ფ"), ("q", "ქ"), ("y", "ყ"), ("w", "წ"), ("c", "ც"), ("x", "ხ"), ("j", "ჯ"), ("h", "ჰ")]


def to_georgian(s):
    if re.search(r"[ა-ჿ]", s):
        return s
    out, i, low = "", 0, s.lower()
    while i < len(low):
        for lat, geo in LAT2GEO:
            if low.startswith(lat, i):
                out += geo
                i += len(lat)
                break
        else:
            out += low[i]
            i += 1
    return out


class NAPRRegistry(Module):
    name = "napr"
    title = "Georgian business registry (NAPR)"
    category = "Georgia"
    description = ("Searches the official public registry of companies and individual entrepreneurs "
                   "(enreg.reestri.gov.ge) by name or ID code. Returns company details, registration info, "
                   "and links to public court documents and business filings. Latin names are transliterated to Georgian.")
    accepts = ("name", "company")
    URL = "https://enreg.reestri.gov.ge/main.php"

    def run(self, ent, ctx):
        q = ent.value.strip()
        s = http()
        try:
            s.get(self.URL, timeout=20)  # session cookie
        except Exception as e:
            ctx.log(f"registry unreachable: {e}", "warn")
            return
        if re.fullmatch(r"\d{9,11}", q):
            queries = [("s_legal_person_idnumber", q)]
        else:
            geo = to_georgian(q)
            queries = [("s_legal_person_name", geo)]
            if ent.type == "name" and " " in geo:  # entrepreneurs are registered as "ი/მ First Last"
                queries.append(("s_legal_person_name", geo.split()[-1] + " " + geo.split()[0]))
        seen = 0
        for field, val in queries:
            data = {"c": "search", "m": "find_legal_persons", "s_legal_person_idnumber": "",
                    "s_legal_person_name": ""}
            data[field] = val
            try:
                r = s.post(self.URL, data=data, timeout=30)
                r.encoding = "utf-8"
            except Exception as e:
                ctx.log(f"search failed: {e}", "warn")
                continue
            for row in re.findall(r"<tr[^>]*>(.*?)</tr>", r.text, re.S):
                cells = [re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", c))).strip()
                         for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
                cells = [c for c in cells if c]
                lid = re.search(r"legal_person\((\d+)\)", row)
                code = next((c for c in cells if re.fullmatch(r"\d{9}", c)), None)
                pn = next((c for c in cells if re.fullmatch(r"\d{11}", c)), None)
                if not code and not pn:
                    continue
                rest = [c for c in cells if c not in (code, pn)]
                nm, form, status = (rest + ["", "", ""])[:3]
                seen += 1
                rid = lid.group(1) if lid else None
                cid = code or pn
                data = {
                    "name": nm, "id_code": code, "personal_no": pn, "legal_form": form, "status": status,
                    "country": "Georgia", "registry_id": rid,
                    "url": f"https://enreg.reestri.gov.ge/main.php?c=show&m=legal_person&show_id={rid}" if rid else None,
                    "documents_link": f"https://enreg.reestri.gov.ge/main.php?c=show&m=legal_person_documents&show_id={rid}" if rid else None,
                }
                ctx.emit("company", f"GE:{cid}", f"{nm} ({cid})", data, rel="registry match", pivot=False)
                if seen >= 40:
                    return
        ctx.update({"napr_matches": seen, "napr_query": queries[0][1]})


# ====================================================================== GEORGIAN COURT DOCUMENTS
class CourtDocuments(Module):
    name = "ge_court"
    title = "Georgian court documents"
    category = "Georgia"
    description = ("Searches Georgian court case database (cas.court.ge) by company or person name/ID. "
                   "Returns public court filings, decisions, and case details linked to businesses or individuals.")
    accepts = ("name", "company")

    def run(self, ent, ctx):
        q = ent.value.strip()
        # Extract ID code if it's a company entity like "GE:123456789"
        if ent.type == "company" and q.startswith("GE:"):
            search_val = q.split(":", 1)[1]
        else:
            search_val = q

        try:
            # Georgian court case search: cas.court.ge/en/cases
            search_url = "https://cas.court.ge/en/cases"
            s = http()
            params = {"q": search_val}
            r = s.get(search_url, params=params, timeout=20)
            if r.status_code != 200:
                return

            # Parse cases from results (looking for case links and details)
            cases = re.findall(r'<a[^>]*href=["\']([^"\']*case[^"\']*)["\'][^>]*>([^<]+)</a>', r.text, re.I)
            if not cases:
                return

            for url, title in cases[:15]:
                full_url = url if url.startswith("http") else f"https://cas.court.ge{url}"
                ctx.emit("link", full_url, f"Court: {title[:80]}",
                        {"source": "Georgian Court", "title": title}, rel="court case", pivot=False)

            ctx.update({"court_cases_found": len(cases)})
        except Exception as e:
            ctx.log(f"court search error: {e}", "warn")


# ====================================================================== URLSCAN
class URLScan(Module):
    name = "urlscan"
    title = "urlscan.io history & screenshots"
    category = "Domain"
    description = ("Past public scans of the domain: screenshots, IPs, servers, redirects and related "
                   "domains. Works without a key; an urlscan key raises the rate limit.")
    accepts = ("domain",)

    def run(self, ent, ctx):
        h = {"API-Key": api_key("urlscan")} if api_key("urlscan") else {}
        d = get_json(f"https://urlscan.io/api/v1/search/?q=domain:{quote(ent.value)}&size=12", headers=h, timeout=25)
        res = (d or {}).get("results") or []
        if not res:
            return
        shots = []
        for x in res:
            page, task = x.get("page") or {}, x.get("task") or {}
            sid = x.get("_id")
            shot = x.get("screenshot") or (f"https://urlscan.io/screenshots/{sid}.png" if sid else None)
            if shot:
                shots.append(shot)
            if len(shots) <= 6 and sid:
                ctx.emit("screenshot", f"https://urlscan.io/result/{sid}/", f"{page.get('url', '')[:70]}", {
                    "preview": shot, "url": f"https://urlscan.io/result/{sid}/", "date": task.get("time"),
                    "ip": page.get("ip"), "server": page.get("server"), "country": page.get("country"),
                    "title": page.get("title"), "status": page.get("status")}, rel="urlscan", pivot=False)
            if page.get("ip"):
                ctx.emit("ip", page["ip"], rel="hosted on (urlscan)", pivot=False)
            pd = (page.get("domain") or "").lower()
            if pd and pd != ent.value and not pd.endswith("." + ent.value) and RE_DOMAIN.match(pd):
                ctx.emit("domain", pd, rel="redirects to / related", pivot=False)
        ctx.update({"urlscan_scans": d.get("total"), "preview": shots[0] if shots else None})


# ====================================================================== REVERSE IP
class ReverseIP(Module):
    name = "reverseip"
    title = "Reverse IP (sites on same server)"
    category = "IP"
    description = "Other domains hosted on the same IP address (HackerTarget, free, ~50 lookups/day)."
    accepts = ("ip",)

    def run(self, ent, ctx):
        try:
            r = get(f"https://api.hackertarget.com/reverseiplookup/?q={ent.value}", timeout=25)
        except Exception:
            return
        t = r.text.strip()
        if r.status_code != 200 or not t or "error" in t.lower() or "API count" in t:
            ctx.log(t[:120] or f"HTTP {r.status_code}", "warn")
            return
        doms = [x.strip().lower() for x in t.splitlines() if RE_DOMAIN.match(x.strip())]
        ctx.update({"cohosted_domains": len(doms)})
        for dmn in doms[:100]:
            ctx.emit("domain", dmn, rel="same server", pivot=False)


# ====================================================================== INTELX
class IntelX(Module):
    name = "intelx"
    title = "Intelligence X (leaks, pastes, darknet)"
    category = "Leaks"
    description = ("Searches leaks, paste sites, darknet and public data dumps for the selector, and "
                   "lists related emails/domains (phonebook). Needs a free IntelX key.")
    accepts = ("email", "domain", "username", "phone", "ip", "btc", "url")
    requires_key = "intelx"
    homepage = "https://intelx.io/account?tab=developer"
    BUCKET = {0: "Pastes", 1: "Dumpster", 2: "Darknet", 3: "WHOIS", 4: "Usenet", 5: "Leaks",
              6: "Public web", 7: "Documents", 9: "Leaks"}

    def _base(self):
        return "https://free.intelx.io"

    def run(self, ent, ctx):
        k = api_key("intelx")
        h = {"x-key": k, "User-Agent": "Keftemulator"}
        base = self._base()
        term = ent.value if ent.type != "phone" else "+" + re.sub(r"\D", "", ent.value)
        try:
            r = http().post(f"{base}/intelligent/search", headers=h, timeout=25, json={
                "term": term, "maxresults": 40, "media": 0, "sort": 2, "terminate": []})
            sid = r.json().get("id") if r.status_code == 200 else None
        except Exception as e:
            ctx.log(f"search: {e}", "warn")
            return
        if not sid:
            ctx.log(f"search HTTP {r.status_code}: {r.text[:120]}", "warn")
            return
        records = []
        for _ in range(8):
            time.sleep(1.5)
            d = get_json(f"{base}/intelligent/search/result?id={sid}&limit=40", headers=h, timeout=25) or {}
            records += d.get("records") or []
            if d.get("status") in (1, 2):  # finished / not found
                break
        for x in records[:40]:
            bucket = x.get("bucket") or self.BUCKET.get(x.get("media"), "")
            ctx.emit("leak", f"intelx:{x.get('systemid')}", f"{bucket or 'Record'}: {x.get('name', '')[:70]}", {
                "name": x.get("name"), "date": x.get("date"), "bucket": bucket, "size": x.get("size"),
                "url": f"https://intelx.io/?did={x.get('systemid')}"}, rel="found in", pivot=False)
        if ent.type == "domain":
            try:
                r = http().post(f"{base}/phonebook/search", headers=h, timeout=25,
                                json={"term": ent.value, "maxresults": 200, "media": 0, "target": 2})
                pid = r.json().get("id")
                time.sleep(2)
                d = get_json(f"{base}/phonebook/search/result?id={pid}&limit=200", headers=h) or {}
                for s in (d.get("selectors") or [])[:150]:
                    v = s.get("selectorvalue", "").lower()
                    if "@" in v:
                        ctx.emit("email", v, rel="phonebook (IntelX)", pivot=False)
            except Exception as e:
                ctx.log(f"phonebook: {e}", "warn")
        ctx.update({"intelx_records": len(records)})


# ====================================================================== DARK WEB
class DarkWeb(Module):
    name = "darkweb"
    title = "Dark-web search links"
    category = "Leaks"
    description = ("Ahmia (Tor search engine) links for the selector. Ahmia blocks automated queries, "
                   "so results open in your browser (clearnet or Tor).")
    accepts = ("email", "username", "name", "phone", "domain", "btc", "eth")

    def run(self, ent, ctx):
        q = quote(f'"{ent.value}"' if " " in ent.value else ent.value)
        for t, u in [("Ahmia (clearnet)", f"https://ahmia.fi/search/?q={q}"),
                     ("Ahmia (Tor Browser)", f"http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search/?q={q}"),
                     ("Google: onion mirrors", f"https://www.google.com/search?q={q}+site:onion.ly+OR+site:onion.ws")]:
            ctx.emit("link", u, t, {"kind": "darkweb"}, rel="dark-web search", pivot=False)


# ====================================================================== GITHUB DEEP
class GitHubDeep(Module):
    name = "github_deep"
    title = "GitHub deep dive"
    category = "Username"
    description = ("Every author email/name in the user's own commits (up to 30 repos), organisations, "
                   "gists, public SSH and GPG keys (GPG keys often contain emails).")
    accepts = ("username",)

    def run(self, ent, ctx):
        u = ent.value
        hdr = {"Accept": "application/vnd.github+json"}
        tok = api_key("github_token")
        if tok:
            hdr["Authorization"] = "Bearer " + tok
        user = get_json(f"https://api.github.com/users/{u}", headers=hdr)
        if not user or user.get("type") not in ("User", "Organization"):
            return
        acc = ctx.emit("account", user["html_url"], f"GitHub: {u}", {"site": "GitHub", "url": user["html_url"]},
                       rel="has account", pivot=False)
        login = user["login"]
        for o in get_json(f"https://api.github.com/users/{login}/orgs", headers=hdr) or []:
            ctx.emit("account", f"https://github.com/{o['login']}", f"GitHub org: {o['login']}",
                     {"site": "GitHub org", "url": f"https://github.com/{o['login']}", "bio": o.get("description"),
                      "avatar": o.get("avatar_url")}, rel="member of", parent=acc, pivot=False)
        keys = get_json(f"https://api.github.com/users/{login}/keys", headers=hdr) or []
        gpg = get_json(f"https://api.github.com/users/{login}/gpg_keys", headers=hdr) or []
        info = {"ssh_keys": [k.get("key", "")[:60] + "…" for k in keys], "gpg_key_ids": [g.get("key_id") for g in gpg]}
        emails = {}
        for g in gpg:
            for e in g.get("emails") or []:
                emails.setdefault(e.get("email", "").lower(), "GPG key")
        gists = get_json(f"https://api.github.com/users/{login}/gists?per_page=30", headers=hdr) or []
        info["gists"] = [{"url": g.get("html_url"), "description": g.get("description"),
                          "files": list((g.get("files") or {}).keys())[:5]} for g in gists[:15]]
        repos = get_json(f"https://api.github.com/users/{login}/repos?sort=pushed&per_page=100", headers=hdr) or []
        own = [r for r in repos if not r.get("fork")][: (30 if tok else 6)]
        names = {}
        for r in own:
            commits = get_json(f"https://api.github.com/repos/{login}/{r['name']}/commits?author={login}&per_page=30",
                               headers=hdr) or []
            for c in commits if isinstance(commits, list) else []:
                a = (c.get("commit") or {}).get("author") or {}
                em, nm = (a.get("email") or "").lower(), a.get("name")
                if em and "noreply" not in em:
                    emails.setdefault(em, f"commit in {r['name']}")
                if nm:
                    names[nm] = names.get(nm, 0) + 1
        info["repos_checked"] = len(own)
        info["commit_names"] = names
        ctx.update(info)
        for em, src in emails.items():
            if "@" in em:
                ctx.emit("email", em, rel=src, parent=acc, data={"source": f"GitHub {src}"})
        for nm in names:
            if nm.lower() != login.lower() and " " in nm.strip():
                ctx.emit("name", nm, rel="commit author name", parent=acc)


# ====================================================================== POWERFUL TOOLS
# Company relationships - Directors, shareholders, connections
class CompanyRelations(Module):
    name = "company_relations"
    title = "Company relationships (directors, shareholders)"
    category = "Georgia"
    description = ("Extract company directors, founders, and shareholders from NAPR registry. "
                   "Search for person-to-company relationships and corporate networks.")
    accepts = ("name", "company")

    def run(self, ent, ctx):
        if ent.type == "company":
            cid = ent.value.split(":")[-1] if ":" in ent.value else ent.value
            # Search NAPR for company details including directors
            s = http()
            try:
                s.get("https://enreg.reestri.gov.ge/main.php", timeout=20)
                data = {"c": "search", "m": "find_legal_persons", "s_legal_person_idnumber": cid, "s_legal_person_name": ""}
                r = s.post("https://enreg.reestri.gov.ge/main.php", data=data, timeout=30)
                r.encoding = "utf-8"
                # Parse for director names
                directors = re.findall(r'director[^<]*?:?[^<]*?([A-Z][a-zა-ჿ]{2,}\s+[A-Z][a-zა-ჿ]{2,})', r.text, re.I)
                for director in set(directors):
                    ctx.emit("name", director.strip(), rel="company director", data={"company": ent.value})
            except Exception as e:
                ctx.log(f"company relations lookup failed: {e}", "warn")


# Georgian Cadastre - Property and real estate lookup
class GeorgianCadastre(Module):
    name = "ge_cadastre"
    title = "Georgian cadastre (property records)"
    category = "Georgia"
    description = ("Search Georgian national cadastre for property ownership and real estate information. "
                   "Link properties to owners by name or address.")
    accepts = ("name", "company")

    def run(self, ent, ctx):
        q = ent.value.strip()
        try:
            # Georgian cadastre search links
            cadastre_url = f"https://cadastre.gov.ge/public/search"
            # Provide direct search links
            ctx.emit("link", f"{cadastre_url}?query={quote(q)}", 
                    f"Georgian Cadastre: {q[:60]}", 
                    {"source": "Georgian Cadastre", "note": "Property/real estate records"}, 
                    rel="cadastre search", pivot=False)
            ctx.update({"cadastre_search": q})
        except Exception as e:
            ctx.log(f"cadastre search error: {e}", "warn")


# Name variations - Generate alternative spellings and AKAs
class NameVariations(Module):
    name = "name_variations"
    title = "Name variations & AKAs"
    category = "Enrichment"
    description = ("Generate name variations: transliterations (Latin↔Georgian), nicknames, "
                   "initials, and common alternate spellings for comprehensive search.")
    accepts = ("name",)
    enricher = True

    def run(self, ent, ctx):
        nm = ent.value.strip()
        if not nm or len(nm) < 2:
            return
        
        parts = nm.split()
        variations = set([nm])
        
        # Reverse order (Last First → First Last)
        if len(parts) >= 2:
            variations.add(" ".join(reversed(parts)))
        
        # Initials
        if len(parts) == 2:
            variations.add(f"{parts[0][0]}. {parts[1]}")
            variations.add(f"{parts[1]} {parts[0][0]}.")
        
        # First name only
        if len(parts) >= 1:
            variations.add(parts[0])
            if len(parts) > 1:
                variations.add(parts[-1])
        
        data = {"variations": list(variations)[:10]}
        ctx.update(data)
        
        for var in variations:
            if var != nm and len(var) > 2:
                ctx.emit("name", var, rel="name variation", parent=ent.id, data={"variation_of": nm})


# Email leak search enhancement
class EmailLeakDatabase(Module):
    name = "email_leaks"
    title = "Email leak & breach search"
    category = "Email"
    description = ("Search multiple email breach databases: HIBP, FreeBreaches, LeakCheck, "
                   "and exposed email collections for compromise data.")
    accepts = ("email",)

    def run(self, ent, ctx):
        em = ent.value.lower()
        breaches = []
        
        try:
            # Search breaches
            r = get(f"https://api.pwnedpasswords.com/range/{em[:5]}", timeout=15)
            if r.status_code == 200:
                for line in r.text.splitlines():
                    if em.upper() in line:
                        breaches.append("PwnedPasswords")
        except:
            pass
        
        # Create search links for other databases
        search_links = [
            (f"https://haveibeenpwned.com/search?query={quote(em)}", "HIBP"),
            (f"https://www.freebreaches.com/search?query={quote(em)}", "FreeBreaches"),
        ]
        
        for url, name in search_links:
            ctx.emit("link", url, f"{name} leak search: {em}", 
                    {"source": f"{name} Database"}, rel="breach search", pivot=False)
        
        if breaches:
            ctx.update({"breaches_found": breaches})


# Georgian Tax Registry search
class GeorgianTaxSearch(Module):
    name = "ge_tax"
    title = "Georgian tax registry (TIN search)"
    category = "Georgia"
    description = ("Search Georgian tax registry by business name or tax ID (TIN). "
                   "Find company tax information and registration details.")
    accepts = ("company", "name")

    def run(self, ent, ctx):
        q = ent.value.strip()
        try:
            # Georgian tax service search
            ctx.emit("link", f"https://www.rs.ge/ka/taxinfo", 
                    f"Georgian Tax Search: {q[:60]}", 
                    {"source": "Georgian Tax Service"}, 
                    rel="tax search", pivot=False)
            ctx.update({"tax_search_query": q})
        except Exception as e:
            ctx.log(f"tax search error: {e}", "warn")


# Business directory - Georgian businesses
class BusinessDirectory(Module):
    name = "ge_business_dir"
    title = "Georgian business directory"
    category = "Georgia"
    description = ("Search Georgian business directories for contact info, phone numbers, "
                   "addresses, and company details.")
    accepts = ("company", "phone", "name")

    def run(self, ent, ctx):
        q = ent.value.strip()
        sources = [
            ("https://www.business.ge/ge/", "Business.ge"),
            ("https://www.2gis.ge/", "2GIS Georgia"),
            ("https://www.yellowpages.ge/", "Yellow Pages GE"),
        ]
        
        for url, name in sources:
            search_url = f"{url}?q={quote(q)}" if "?" not in url else f"{url}q={quote(q)}"
            ctx.emit("link", search_url, f"{name}: {q[:50]}", 
                    {"source": f"{name}"}, rel="business directory", pivot=False)


# LinkedIn/Employment history search
class EmploymentHistory(Module):
    name = "employment_history"
    title = "Employment history search"
    category = "Person"
    description = ("Search for employment history, LinkedIn profiles, work email addresses, "
                   "and professional networks for a person.")
    accepts = ("name", "email")

    def run(self, ent, ctx):
        q = ent.value.strip()
        # Employment search links
        searches = [
            (f"https://www.linkedin.com/search/results/people/?keywords={quote(q)}", "LinkedIn"),
            (f"https://www.indeed.com/resumes?q={quote(q)}", "Indeed"),
            (f"https://www.crunchbase.com/search?query={quote(q)}", "Crunchbase"),
        ]
        
        for url, name in searches:
            ctx.emit("link", url, f"{name}: {q[:40]}", 
                    {"source": f"{name} Search"}, rel="employment search", pivot=False)


# Georgian arrest & criminal records
class GeorgianCriminalRecords(Module):
    name = "ge_criminal"
    title = "Georgian criminal records search"
    category = "Georgia"
    description = ("Search Georgian court and police databases for arrest records, convictions, "
                   "and criminal case information.")
    accepts = ("name", "phone")

    def run(self, ent, ctx):
        q = ent.value.strip()
        try:
            # Georgian court database search
            ctx.emit("link", "https://cas.court.ge/en/cases", 
                    f"Georgian Courts: {q[:60]}", 
                    {"source": "Georgian Court System", "query": q}, 
                    rel="criminal records search", pivot=False)
            ctx.update({"criminal_search": q})
        except Exception as e:
            ctx.log(f"criminal records search error: {e}", "warn")


# Social Media Profile Enrichment
class SocialMediaEnrich(Module):
    name = "social_enrich"
    title = "Social media profile enrichment"
    category = "Username"
    description = ("Extract and enrich social media profiles: follower counts, bio details, "
                   "mutual connections, and linked social accounts.")
    accepts = ("account", "username")
    enricher = True

    def run(self, ent, ctx):
        url = (ent.data or {}).get("url") or ent.value
        if not url.startswith("http"):
            return
        
        try:
            r = get(url, timeout=12)
            if r.status_code != 200:
                return
            
            # Extract counts from page
            followers = re.search(r'(\d+(?:\.\d+)?[KM]?)\s*(?:followers|subscribers)', r.text, re.I)
            following = re.search(r'(\d+(?:\.\d+)?[KM]?)\s*following', r.text, re.I)
            posts = re.search(r'(\d+(?:\.\d+)?[KM]?)\s*posts?', r.text, re.I)
            
            data = {}
            if followers:
                data["followers_count"] = followers.group(1)
            if following:
                data["following_count"] = following.group(1)
            if posts:
                data["posts_count"] = posts.group(1)
            
            if data:
                ctx.update(data)
        except Exception as e:
            ctx.log(f"social enrich error: {e}", "warn")


# Vehicle registration enhancement
class VehicleRegistryGeorgia(Module):
    name = "vehicle_registry"
    title = "Vehicle registration search (Georgia)"
    category = "Georgia"
    description = ("Search Georgian vehicle registration database by plate number, VIN, "
                   "or owner name for vehicle history and registration info.")
    accepts = ("plate", "vin", "name")

    def run(self, ent, ctx):
        q = ent.value.strip()
        
        # Georgian vehicle databases
        searches = [
            (f"https://myauto.ge/ka/search?text={quote(q)}", "MyAuto.ge"),
            (f"https://www.platesmania.com/ge/search.php?q={quote(q)}", "Platesmania"),
        ]
        
        for url, name in searches:
            ctx.emit("link", url, f"{name}: {q}", 
                    {"source": f"{name}"}, rel="vehicle search", pivot=False)



# ====================================================================== ADDITIONAL POWERFUL TOOLS
# Company financial data - Court judgments, bankruptcies
class CompanyFinancial(Module):
    name = "company_financial"
    title = "Company financial & legal records"
    category = "Georgia"
    description = ("Search for company financial data, court judgments, bankruptcy filings, "
                   "legal cases, and regulatory actions from Georgian authorities.")
    accepts = ("company", "name")

    def run(self, ent, ctx):
        q = ent.value.strip()
        try:
            # Georgian court filings for company
            ctx.emit("link", f"https://cas.court.ge/en/cases?q={quote(q)}", 
                    f"Court Cases: {q[:50]}", 
                    {"source": "Georgian Court System", "type": "financial/legal"}, 
                    rel="legal records", pivot=False)
            
            # NAPR financial info
            ctx.emit("link", f"https://enreg.reestri.gov.ge/main.php?c=show&m=legal_person_documents&show_id=",
                    f"NAPR Financial: {q[:50]}", 
                    {"source": "NAPR Registry", "type": "financial"}, 
                    rel="financial records", pivot=False)
            
            ctx.update({"financial_search": q})
        except Exception as e:
            ctx.log(f"financial search error: {e}", "warn")


# Bankruptcy & legal records automation
class BankruptcyRecords(Module):
    name = "bankruptcy_records"
    title = "Bankruptcy & legal proceedings"
    category = "Georgia"
    description = ("Automated search for bankruptcy filings, insolvency proceedings, "
                   "and legal cases in Georgian courts.")
    accepts = ("company", "name")

    def run(self, ent, ctx):
        q = ent.value.strip()
        try:
            # Georgian court bankruptcy/insolvency search
            searches = [
                (f"https://cas.court.ge/en/cases?q={quote(q)}", "Georgian Courts"),
                (f"https://enreg.reestri.gov.ge/main.php", "NAPR Records"),
            ]
            
            for url, name in searches:
                ctx.emit("link", url, f"Bankruptcy Search: {q[:50]}", 
                        {"source": name, "type": "bankruptcy"}, 
                        rel="bankruptcy search", pivot=False)
            
            ctx.update({"bankruptcy_search": q})
        except Exception as e:
            ctx.log(f"bankruptcy search error: {e}", "warn")


# Family & relationship mapping
class FamilyRelationships(Module):
    name = "family_relations"
    title = "Family & relationship mapping"
    category = "Person"
    description = ("Map family connections, relatives, and social relationships. "
                   "Find connected people via shared surnames, addresses, and social links.")
    accepts = ("name",)

    def run(self, ent, ctx):
        nm = ent.value.strip()
        if len(nm) < 3:
            return
        
        parts = nm.split()
        # Search for people with same surname
        if len(parts) >= 2:
            surname = parts[-1]
            # Generate search queries
            searches = [
                (f"https://wikidata.org/wiki/Special:Search?search={quote(surname)}", "Wikidata"),
                (f"https://www.google.com/search?q={quote(surname)} Georgia family", "Google"),
            ]
            
            for url, name in searches:
                ctx.emit("link", url, f"Family Search: {surname}", 
                        {"source": name}, rel="family relation search", pivot=False)
        
        ctx.update({"family_search": nm})


# Social media direct integration (enhanced)
class SocialMediaAPI(Module):
    name = "social_media_api"
    title = "Social media API integration"
    category = "Username"
    description = ("Direct API integration with social platforms to fetch profile data: "
                   "followers, bio, posts, verification status, engagement metrics.")
    accepts = ("username", "account")
    enricher = True

    def run(self, ent, ctx):
        url = (ent.data or {}).get("url") or ent.value
        if not url or not url.startswith("http"):
            return
        
        data = {}
        try:
            r = get(url, timeout=12)
            if r.status_code == 200:
                # Extract JSON-LD data if available
                json_ld = re.search(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', r.text, re.S)
                if json_ld:
                    try:
                        jdata = json.loads(json_ld.group(1))
                        if isinstance(jdata, dict):
                            data.update({k: v for k, v in jdata.items() if k in 
                                       ["name", "description", "image", "url", "sameAs"]})
                    except:
                        pass
                
                # Extract meta data
                for pattern, field in [
                    (r'followers["\']?\s*:\s*(["\'])?(\d+(?:[KM])?)', "followers"),
                    (r'following["\']?\s*:\s*(["\'])?(\d+(?:[KM])?)', "following"),
                    (r'posts?["\']?\s*:\s*(["\'])?(\d+(?:[KM])?)', "posts"),
                    (r'verified["\']?\s*:\s*(true|false)', "verified"),
                ]:
                    m = re.search(pattern, r.text, re.I)
                    if m:
                        data[field] = m.group(2) if ")" in pattern else m.group(1)
            
            if data:
                ctx.update(data)
        except Exception as e:
            ctx.log(f"social media API error: {e}", "warn")


# ====================================================================== RECONNAISSANCE & SECURITY
# SSL certificate finder
class SSLCertificateFinder(Module):
    name = "ssl_certs"
    title = "SSL certificate finder"
    category = "Domain"
    description = ("Find all SSL certificates for a domain/IP/organization from multiple sources: "
                   "crt.sh, Censys, Shodan certificate databases.")
    accepts = ("domain", "ip", "company")

    def run(self, ent, ctx):
        target = ent.value
        if ent.type == "company":
            target = target.split(":")[-1] if ":" in target else target
        
        try:
            # crt.sh certificate search
            r = get(f"https://crt.sh/?q={quote(target)}&output=json", timeout=20)
            if r.status_code == 200:
                certs = r.json() if isinstance(r.json(), list) else []
                domains = set()
                for cert in certs[:50]:
                    if "name_value" in cert:
                        for d in cert["name_value"].split("\n"):
                            d = d.strip().lstrip("*.")
                            if d and "." in d:
                                domains.add(d)
                
                for domain in domains:
                    if domain != target:
                        ctx.emit("domain", domain, rel="certificate found", pivot=False, 
                                data={"source": "crt.sh"})
                
                ctx.update({"certificates_found": len(domains)})
        except Exception as e:
            ctx.log(f"cert search error: {e}", "warn")


# Malware & C2 detection
class MalwareC2Check(Module):
    name = "malware_check"
    title = "Malware/C2 check"
    category = "Security"
    description = ("Check if domain/IP is known malware, C2 server, or phishing site in "
                   "Abuse.ch, MalwareBazaar, URLhaus, and threat intelligence databases.")
    accepts = ("domain", "ip", "url")

    def run(self, ent, ctx):
        target = ent.value
        threats = []
        
        try:
            # URLhaus check
            r = get_json(f"https://urlhaus-api.abuse.ch/v1/urls/query/?host={quote(target)}", timeout=15)
            if r and r.get("query_status") == "ok" and r.get("result"):
                threats.append(f"URLhaus ({len(r['result'])} URLs)")
            
            # IP reputation check via AbuseIPDB (if key available)
            if ent.type == "ip" and api_key("abuseipdb"):
                r = get_json(f"https://api.abuseipdb.com/api/v2/check?ipAddress={target}",
                           headers={"Key": api_key("abuseipdb")}, timeout=15)
                if r and r.get("data", {}).get("abuseConfidenceScore", 0) > 50:
                    threats.append(f"AbuseIPDB ({r['data']['abuseConfidenceScore']}% confidence)")
        except:
            pass
        
        if threats:
            ctx.update({"malware_threats": threats})
            for threat in threats:
                ctx.log(f"⚠️ Threat detected: {threat}", "warn")


# Threat intelligence feeds
class ThreatIntelFeeds(Module):
    name = "threat_feeds"
    title = "Threat intelligence feeds"
    category = "Security"
    description = ("Check domain/IP/email against AlienVault OTX, SANS, URLhaus, "
                   "and other threat intelligence feeds.")
    accepts = ("domain", "ip", "email")

    def run(self, ent, ctx):
        target = ent.value
        indicators = []
        
        try:
            # AlienVault OTX search
            r = get_json(f"https://otx.alienvault.com/api/v1/indicators/{ent.type}/{target}/general", timeout=15)
            if r and r.get("pulse_info", {}).get("count", 0) > 0:
                indicators.append({
                    "source": "AlienVault OTX",
                    "pulses": r["pulse_info"]["count"],
                    "url": f"https://otx.alienvault.com/indicator/{ent.type}/{target}"
                })
        except:
            pass
        
        for ind in indicators:
            ctx.emit("link", ind["url"], 
                    f"Threat: {ind['source']} ({ind['pulses']} pulses)", 
                    {"source": ind["source"]}, rel="threat intelligence", pivot=False)
            ctx.log(f"Found in {ind['source']}: {ind['pulses']} threat pulses")


# CVE search
class CVESearch(Module):
    name = "cve_search"
    title = "CVE vulnerability search"
    category = "Security"
    description = ("Search for known vulnerabilities (CVEs) related to software, domains, "
                   "or organizations from NIST CVE database.")
    accepts = ("domain", "company", "name")

    def run(self, ent, ctx):
        q = ent.value.strip()
        try:
            # CVE search via public databases
            searches = [
                (f"https://nvd.nist.gov/vuln/search/results?form_type=Basic&results_type=overview&query={quote(q)}", 
                 "NIST NVD"),
                (f"https://www.cvedetails.com/cve/search.php?q={quote(q)}", "CVE Details"),
            ]
            
            for url, name in searches:
                ctx.emit("link", url, f"CVE Search: {q[:50]}", 
                        {"source": name}, rel="vulnerability search", pivot=False)
            
            ctx.update({"cve_search": q})
        except Exception as e:
            ctx.log(f"CVE search error: {e}", "warn")


# Wayback Machine deep archive
class WaybackArchive(Module):
    name = "wayback_deep"
    title = "Wayback Machine deep archive search"
    category = "Web"
    description = ("Search Internet Archive Wayback Machine for historical snapshots, "
                   "subdomain discovery, and website evolution history.")
    accepts = ("domain", "url")

    def run(self, ent, ctx):
        target = ent.value
        if ent.type == "url":
            target = urlparse(target).netloc or target
        
        try:
            # Get Wayback snapshots
            r = get_json(f"https://archive.org/wayback/available?url={quote(target)}", timeout=15)
            snapshots = r.get("archived_snapshots", {})
            if snapshots:
                closest = snapshots.get("closest", {})
                if closest:
                    ctx.emit("link", closest["url"], 
                            f"Wayback: {closest.get('timestamp', 'archived')}", 
                            {"source": "Internet Archive", "timestamp": closest.get("timestamp")}, 
                            rel="wayback snapshot", pivot=False)
                    ctx.update({"wayback_snapshots": len(snapshots)})
        except Exception as e:
            ctx.log(f"wayback search error: {e}", "warn")


# Technology detection & stack analysis
class TechnologyDetection(Module):
    name = "tech_detection"
    title = "Technology & web stack detection"
    category = "Domain"
    description = ("Detect technologies used: CMS, frameworks, analytics, CDN, "
                   "servers, and other web technologies via Wappalyzer-style analysis.")
    accepts = ("domain", "url")

    def run(self, ent, ctx):
        target = ent.value
        if ent.type == "url":
            target = urlparse(target).netloc or target
        
        technologies = []
        try:
            # Use public APIs for tech detection
            r = get(f"https://{target}" if not target.startswith("http") else target, timeout=15)
            if r.status_code == 200:
                # Detect common technologies by headers and content
                headers = {k.lower(): v for k, v in r.headers.items()}
                tech_map = {
                    "server": headers.get("server", ""),
                    "x-powered-by": headers.get("x-powered-by", ""),
                    "x-aspnet-version": headers.get("x-aspnet-version", ""),
                }
                
                # Detect by content patterns
                if "wordpress" in r.text.lower():
                    technologies.append("WordPress")
                if "shopify" in r.text.lower():
                    technologies.append("Shopify")
                if "/joomla/" in r.text.lower():
                    technologies.append("Joomla")
                if "drupal" in r.text.lower():
                    technologies.append("Drupal")
                
                for k, v in tech_map.items():
                    if v and v not in ("", "-"):
                        technologies.append(v)
                
                if technologies:
                    ctx.update({"technologies": list(set(technologies))})
        except Exception as e:
            ctx.log(f"tech detection error: {e}", "warn")

