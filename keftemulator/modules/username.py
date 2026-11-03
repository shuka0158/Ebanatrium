"""Username -> accounts. Native API-backed checks + Sherlock + Maigret wrappers."""
import json
import re
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ..core import Module
from ..util import get, get_json, find_tool, run_cmd, strip_ansi, api_key, RE_DOMAIN


def _clean_url(u):
    if not u:
        return None
    u = u.strip()
    if not u.startswith("http"):
        u = "https://" + u
    return u


class ProfileAPIs(Module):
    """Rich profile lookups via public JSON APIs (gives bio, name, location, links)."""
    name = "profiles"
    title = "Profile APIs (bio data)"
    category = "Username"
    description = ("GitHub, GitLab, Reddit, Keybase, HackerNews, Dev.to, Chess.com, Lichess, "
                   "Docker Hub, Gravatar, Codeberg, Bluesky, Mastodon search — extracts bio, real name, "
                   "location, websites, linked accounts, avatars.")
    accepts = ("username",)

    def run(self, ent, ctx):
        u = ent.value
        checks = [self.github, self.gitlab, self.reddit, self.keybase, self.hackernews, self.devto,
                  self.chess, self.lichess, self.dockerhub, self.gravatar, self.codeberg,
                  self.bluesky, self.mastodon]
        with ThreadPoolExecutor(6) as ex:
            for f in checks:
                ex.submit(self._safe, f, u, ctx)

    @staticmethod
    def _safe(f, u, ctx):
        try:
            f(u, ctx)
        except Exception as e:  # noqa: BLE001
            ctx.log(f"{f.__name__}: {e}", "warn")

    def _account(self, ctx, site, url, data, avatar=None):
        data = {k: v for k, v in data.items() if v not in (None, "", [], {})}
        data["site"] = site
        data["url"] = url
        if avatar:
            data["avatar"] = avatar
        return ctx.emit("account", url, f"{site}: {ctx.ent.value}", data, rel="has account")

    def _bio_pivots(self, ctx, parent, name=None, email=None, blog=None, location=None, twitter=None):
        if name and len(name) > 2:
            ctx.emit("name", name, rel="real name", parent=parent)
        if email:
            ctx.emit("email", email.lower(), rel="email", parent=parent)
        if blog:
            from urllib.parse import urlparse
            host = urlparse(_clean_url(blog)).hostname or ""
            host = host.removeprefix("www.")
            if RE_DOMAIN.match(host) and not any(s in host for s in ("github.", "twitter.", "x.com", "linkedin.", "facebook.", "instagram.")):
                ctx.emit("domain", host, rel="website", parent=parent)
            else:
                ctx.emit("link", _clean_url(blog), rel="website", parent=parent, pivot=False)
        if location:
            ctx.emit("location", location, rel="location", parent=parent, data={"query": location})
        if twitter:
            ctx.emit("username", twitter, rel="twitter handle", parent=parent)

    def github(self, u, ctx):
        hdr = {"Accept": "application/vnd.github+json"}
        if api_key("github_token"):
            hdr["Authorization"] = "Bearer " + api_key("github_token")
        d = get_json(f"https://api.github.com/users/{u}", headers=hdr)
        if not d or "login" not in d:
            return
        pid = self._account(ctx, "GitHub", d["html_url"], {
            "name": d.get("name"), "bio": d.get("bio"), "company": d.get("company"),
            "location": d.get("location"), "blog": d.get("blog"), "email": d.get("email"),
            "twitter": d.get("twitter_username"), "followers": d.get("followers"),
            "repos": d.get("public_repos"), "created": d.get("created_at"), "hireable": d.get("hireable"),
        }, d.get("avatar_url"))
        self._bio_pivots(ctx, pid, d.get("name"), d.get("email"), d.get("blog"), d.get("location"),
                         d.get("twitter_username"))
        # Commit emails leak via public events
        ev = get_json(f"https://api.github.com/users/{u}/events/public?per_page=100", headers=hdr) or []
        seen = set()
        for e in ev:
            for c in (e.get("payload") or {}).get("commits", []) or []:
                em = (c.get("author") or {}).get("email", "")
                if em and "noreply" not in em and em not in seen:
                    seen.add(em)
                    ctx.emit("email", em.lower(), rel="commit email", parent=pid,
                             data={"source": "GitHub public commit"})

    def gitlab(self, u, ctx):
        d = get_json(f"https://gitlab.com/api/v4/users?username={u}")
        if d:
            d = d[0]
            full = get_json(f"https://gitlab.com/api/v4/users/{d['id']}") or d
            pid = self._account(ctx, "GitLab", d["web_url"], {
                "name": full.get("name"), "bio": full.get("bio"), "location": full.get("location"),
                "website": full.get("website_url"), "organization": full.get("organization"),
                "job_title": full.get("job_title"), "created": full.get("created_at")}, d.get("avatar_url"))
            self._bio_pivots(ctx, pid, full.get("name"), full.get("public_email"), full.get("website_url"),
                             full.get("location"))

    def reddit(self, u, ctx):
        d = get_json(f"https://www.reddit.com/user/{u}/about.json")
        if d and d.get("data", {}).get("name"):
            x = d["data"]
            import datetime
            self._account(ctx, "Reddit", f"https://www.reddit.com/user/{x['name']}", {
                "karma": x.get("total_karma"), "bio": (x.get("subreddit") or {}).get("public_description"),
                "created": datetime.datetime.utcfromtimestamp(x.get("created_utc", 0)).isoformat(),
                "verified": x.get("verified")}, (x.get("icon_img") or "").split("?")[0])

    def keybase(self, u, ctx):
        d = get_json(f"https://keybase.io/_/api/1.0/user/lookup.json?usernames={u}")
        them = (d or {}).get("them") or []
        if not them or not them[0]:
            return
        t = them[0]
        prof = t.get("profile") or {}
        pid = self._account(ctx, "Keybase", f"https://keybase.io/{u}", {
            "name": prof.get("full_name"), "bio": prof.get("bio"), "location": prof.get("location")})
        self._bio_pivots(ctx, pid, prof.get("full_name"), location=prof.get("location"))
        for p in (t.get("proofs_summary") or {}).get("all", []):
            if p.get("proof_type") in ("dns", "generic_web_site"):
                ctx.emit("domain", p.get("nametag"), rel="keybase proof", parent=pid)
            else:
                ctx.emit("account", p.get("service_url") or p.get("nametag"),
                         f"{p.get('proof_type')}: {p.get('nametag')}",
                         {"site": p.get("proof_type"), "verified": "keybase proof"}, rel="proven account",
                         parent=pid, pivot=False)
                if p.get("nametag") and p.get("nametag").lower() != u.lower():
                    ctx.emit("username", p["nametag"], rel="alias", parent=pid)

    def hackernews(self, u, ctx):
        d = get_json(f"https://hacker-news.firebaseio.com/v0/user/{u}.json")
        if d:
            about = re.sub("<[^>]+>", " ", d.get("about") or "")
            self._account(ctx, "HackerNews", f"https://news.ycombinator.com/user?id={u}",
                          {"karma": d.get("karma"), "bio": about.strip()})

    def devto(self, u, ctx):
        d = get_json(f"https://dev.to/api/users/by_username?url={u}")
        if d and d.get("username"):
            pid = self._account(ctx, "Dev.to", f"https://dev.to/{u}", {
                "name": d.get("name"), "bio": d.get("summary"), "location": d.get("location"),
                "website": d.get("website_url"), "twitter": d.get("twitter_username"),
                "github": d.get("github_username"), "joined": d.get("joined_at")}, d.get("profile_image"))
            self._bio_pivots(ctx, pid, d.get("name"), blog=d.get("website_url"), location=d.get("location"))

    def chess(self, u, ctx):
        d = get_json(f"https://api.chess.com/pub/player/{u.lower()}")
        if d and d.get("username"):
            self._account(ctx, "Chess.com", d.get("url"), {
                "name": d.get("name"), "location": d.get("location"),
                "country": (d.get("country") or "").rsplit("/", 1)[-1]}, d.get("avatar"))

    def lichess(self, u, ctx):
        d = get_json(f"https://lichess.org/api/user/{u}")
        if d and d.get("id") and not d.get("disabled"):
            p = d.get("profile") or {}
            self._account(ctx, "Lichess", d.get("url"), {
                "name": " ".join(filter(None, [p.get("firstName"), p.get("lastName")])),
                "bio": p.get("bio"), "location": p.get("location"), "links": p.get("links")})

    def dockerhub(self, u, ctx):
        d = get_json(f"https://hub.docker.com/v2/users/{u}/")
        if d and d.get("username"):
            self._account(ctx, "Docker Hub", f"https://hub.docker.com/u/{u}", {
                "name": d.get("full_name"), "location": d.get("location"), "company": d.get("company"),
                "joined": d.get("date_joined")}, d.get("gravatar_url"))

    def gravatar(self, u, ctx):
        d = get_json(f"https://en.gravatar.com/{u}.json")
        if d and d.get("entry"):
            _gravatar_entry(ctx, d["entry"][0])

    def codeberg(self, u, ctx):
        d = get_json(f"https://codeberg.org/api/v1/users/{u}")
        if d and d.get("login"):
            pid = self._account(ctx, "Codeberg", f"https://codeberg.org/{u}", {
                "name": d.get("full_name"), "bio": d.get("description"), "location": d.get("location"),
                "website": d.get("website"), "created": d.get("created")}, d.get("avatar_url"))
            self._bio_pivots(ctx, pid, d.get("full_name"), blog=d.get("website"), location=d.get("location"))

    def bluesky(self, u, ctx):
        handle = u if "." in u else f"{u}.bsky.social"
        d = get_json(f"https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor={handle}")
        if d and d.get("did"):
            self._account(ctx, "Bluesky", f"https://bsky.app/profile/{d['handle']}", {
                "name": d.get("displayName"), "bio": d.get("description"),
                "followers": d.get("followersCount"), "posts": d.get("postsCount"),
                "created": d.get("createdAt")}, d.get("avatar"))

    def mastodon(self, u, ctx):
        d = get_json(f"https://mastodon.social/api/v2/search?q={u}&type=accounts&limit=10")
        for a in (d or {}).get("accounts", []):
            if a.get("username", "").lower() == u.lower():
                self._account(ctx, "Mastodon", a.get("url"), {
                    "name": a.get("display_name"), "bio": re.sub("<[^>]+>", " ", a.get("note") or "").strip(),
                    "acct": a.get("acct"), "followers": a.get("followers_count"),
                    "created": a.get("created_at")}, a.get("avatar"))


def _gravatar_entry(ctx, e, parent=None):
    url = e.get("profileUrl")
    nm = e.get("displayName") or (e.get("name") or {}).get("formatted")
    pid = ctx.emit("account", url, f"Gravatar: {e.get('preferredUsername')}", {
        "site": "Gravatar", "url": url, "name": nm, "bio": e.get("aboutMe"),
        "location": e.get("currentLocation"), "avatar": e.get("thumbnailUrl")},
        rel="has account", parent=parent)
    if nm:
        ctx.emit("name", nm, rel="real name", parent=pid)
    if e.get("currentLocation"):
        ctx.emit("location", e["currentLocation"], rel="location", parent=pid)
    for a in e.get("accounts", []) or []:
        ctx.emit("account", a.get("url"), f"{a.get('shortname')}: {a.get('username')}",
                 {"site": a.get("shortname"), "url": a.get("url")}, rel="linked account", parent=pid, pivot=False)
    for ur in e.get("urls", []) or []:
        ctx.emit("link", ur.get("value"), ur.get("title"), rel="website", parent=pid, pivot=False)
    return pid


# Sites checked by HTTP status / content. (name, url, mode, marker)
#   mode "status": 200 = exists, 404 = missing
#   mode "absent": exists unless marker text present
#   mode "present": exists only if marker text present
SITES = [
    ("Instagram", "https://www.instagram.com/{}/", "manual", None),
    ("TikTok", "https://www.tiktok.com/@{}", "present", '"uniqueId":"{}"'),
    ("Telegram", "https://t.me/{}", "present", "tgme_page_title"),
    ("X / Twitter", "https://x.com/{}", "manual", None),
    ("Facebook", "https://www.facebook.com/{}", "manual", None),
    ("LinkedIn", "https://www.linkedin.com/in/{}", "manual", None),
    ("YouTube", "https://www.youtube.com/@{}", "status", None),
    ("Twitch", "https://www.twitch.tv/{}", "present", 'content="twitch.tv/{}"'),
    ("Pinterest", "https://www.pinterest.com/{}/", "absent", "User not found"),
    ("SoundCloud", "https://soundcloud.com/{}", "status", None),
    ("Spotify", "https://open.spotify.com/user/{}", "manual", None),
    ("Steam", "https://steamcommunity.com/id/{}", "absent", "The specified profile could not be found"),
    ("Medium", "https://medium.com/@{}", "status", None),
    ("Patreon", "https://www.patreon.com/{}", "status", None),
    ("Vimeo", "https://vimeo.com/{}", "status", None),
    ("Flickr", "https://www.flickr.com/people/{}", "status", None),
    ("DeviantArt", "https://www.deviantart.com/{}", "status", None),
    ("Behance", "https://www.behance.net/{}", "status", None),
    ("Dribbble", "https://dribbble.com/{}", "status", None),
    ("About.me", "https://about.me/{}", "status", None),
    ("Linktree", "https://linktr.ee/{}", "status", None),
    ("Replit", "https://replit.com/@{}", "status", None),
    ("PyPI", "https://pypi.org/user/{}/", "manual", None),
    ("npm", "https://www.npmjs.com/~{}", "status", None),
    ("Kaggle", "https://www.kaggle.com/{}", "status", None),
    ("HackerOne", "https://hackerone.com/{}", "status", None),
    ("Bugcrowd", "https://bugcrowd.com/{}", "status", None),
    ("TryHackMe", "https://tryhackme.com/api/user/exist/{}", "present", '"success":true'),
    ("Wikipedia", "https://en.wikipedia.org/wiki/User:{}", "status", None),
    ("Imgur", "https://imgur.com/user/{}", "manual", None),
    ("Tumblr", "https://{}.tumblr.com", "status", None),
    ("WordPress", "https://{}.wordpress.com", "status", None),
    ("Blogger", "https://{}.blogspot.com", "status", None),
    ("Substack", "https://{}.substack.com", "status", None),
    ("Etsy", "https://www.etsy.com/shop/{}", "status", None),
    ("Roblox", "https://www.roblox.com/user.aspx?username={}", "absent", "Page cannot be found"),
    ("Xbox Gamertag", "https://xboxgamertag.com/search/{}", "status", None),
    ("Duolingo", "https://www.duolingo.com/2017-06-30/users?username={}", "present", '"username"'),
    ("Last.fm", "https://www.last.fm/user/{}", "manual", None),
    ("MyAnimeList", "https://myanimelist.net/profile/{}", "status", None),
    ("Quora", "https://www.quora.com/profile/{}", "manual", None),
    ("VK", "https://vk.com/{}", "manual", None),
    ("OK.ru", "https://ok.ru/{}", "manual", None),
    ("Snapchat", "https://www.snapchat.com/add/{}", "status", None),
    ("Threads", "https://www.threads.net/@{}", "manual", None),
    ("OnlyFans", "https://onlyfans.com/{}", "manual", None),
    ("Cash App", "https://cash.app/${}", "status", None),
    ("Venmo", "https://account.venmo.com/u/{}", "status", None),
    ("Discord (lookup)", "https://discord.com/users/{}", "manual", None),
]


class SiteCheck(Module):
    name = "sitecheck"
    title = "Quick site check (50 sites)"
    category = "Username"
    description = "Fast built-in presence check on ~50 major social/dev/gaming platforms. 'manual' sites produce links only."
    accepts = ("username",)

    def run(self, ent, ctx):
        u = ent.value
        if not re.match(r"^[A-Za-z0-9._\-]{2,40}$", u):
            return
        with ThreadPoolExecutor(12) as ex:
            for s in SITES:
                ex.submit(self.check, u, s, ctx)

    def check(self, u, site, ctx):
        name, url, mode, marker = site
        url = url.format(u)
        if mode == "manual":
            ctx.emit("link", url, f"{name} (verify manually)", {"site": name, "url": url,
                     "note": "Site blocks automated checks"}, rel="possible", pivot=False)
            return
        try:
            r = get(url, timeout=12, allow_redirects=True)
        except Exception:
            return
        body = r.text
        low = body[:20000].lower()
        if any(m in low for m in ("client challenge", "just a moment", "captcha", "cf-chl")):
            ctx.emit("link", url, f"{name} (blocked by bot check, verify manually)", {"site": name, "url": url},
                     rel="possible", pivot=False)
            return
        from urllib.parse import urlparse
        h1, h2 = (urlparse(x).hostname.removeprefix("www.") for x in (url, r.url))
        if h1 != h2 or u.lower() not in r.url.lower():  # redirected away (signup / home page)
            return
        found = False
        if mode == "status":
            found = r.status_code == 200
        elif mode == "absent":
            found = r.status_code == 200 and marker not in body
        elif mode == "present":
            found = r.status_code == 200 and marker.format(u) in body
        if found:
            ctx.emit("account", url, f"{name}: {u}", {"site": name, "url": url, "confidence": "medium"},
                     rel="has account", pivot=False)


class Sherlock(Module):
    name = "sherlock"
    title = "Sherlock"
    category = "Username"
    description = "Hunts a username across 400+ social networks (sherlock-project)."
    accepts = ("username",)
    requires_tool = "sherlock"
    external = True
    homepage = "https://github.com/sherlock-project/sherlock"

    def run(self, ent, ctx):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out.txt"
            code, text = run_cmd([find_tool("sherlock"), ent.value, "--print-found", "--no-color",
                                  "--timeout", "15", "--output", str(out)])
            n = 0
            for line in strip_ansi(text).splitlines():
                m = re.match(r"\[\+\]\s*([^:]+):\s*(https?://\S+)", line.strip())
                if m:
                    n += 1
                    ctx.emit("account", m.group(2), f"{m.group(1).strip()}: {ent.value}",
                             {"site": m.group(1).strip(), "url": m.group(2), "source": "sherlock"},
                             rel="has account", pivot=False)
            ctx.log(f"{n} accounts for {ent.value}")


class Maigret(Module):
    name = "maigret"
    title = "Maigret"
    category = "Username"
    description = "Collects a dossier from 3000+ sites with profile parsing (soxoj/maigret). Slow but thorough."
    accepts = ("username",)
    requires_tool = "maigret"
    external = True
    homepage = "https://github.com/soxoj/maigret"

    def run(self, ent, ctx):
        with tempfile.TemporaryDirectory() as td:
            code, text = run_cmd([find_tool("maigret"), ent.value, "-J", "simple", "--folderoutput", td,
                                  "--timeout", "15", "--no-progressbar", "--no-color"])
            files = list(Path(td).glob("*.json"))
            if not files:
                ctx.log(f"no JSON output ({text[-300:]})", "warn")
                return
            data = json.loads(files[0].read_text())
            for site, info in data.items():
                st = (info.get("status") or {})
                if st.get("status") != "Claimed":
                    continue
                url = info.get("url_user") or st.get("url")
                ids = st.get("ids") or {}
                pid = ctx.emit("account", url, f"{site}: {ent.value}",
                               {"site": site, "url": url, "source": "maigret", "tags": st.get("tags"), **ids},
                               rel="has account", pivot=False)
                for k, v in ids.items():
                    if k in ("fullname", "name") and v:
                        ctx.emit("name", v, rel="real name", parent=pid)
                    elif k in ("email",) and v:
                        ctx.emit("email", v, rel="email", parent=pid)
                    elif k in ("location", "country", "city") and v:
                        ctx.emit("location", v, rel="location", parent=pid)
                    elif k.endswith("_username") or k == "username":
                        if v and v.lower() != ent.value.lower():
                            ctx.emit("username", v, rel="alias", parent=pid)
