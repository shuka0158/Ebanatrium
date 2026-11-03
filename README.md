# Keftemulator — unified OSINT platform

🔍 **One web GUI that combines 61 OSINT modules** with the best open-source tools.

Give it one identifier (username, email, domain, IP, phone, name, company, plate, VIN, image).
It runs every matching module, then **pivots** (SpiderFoot-style) on each new email, username, domain, IP, phone or name it finds. 
Results show up as a **list**, an interactive **link-analysis graph** (Maltego-style), and a **map**.

## Quick Start (< 5 minutes)

```bash
git clone https://github.com/shuka0158/Keftemulator.git
cd Keftemulator
bash setup.sh           # Interactive setup with API key prompts
bash run.sh             # Start the app at http://127.0.0.1:5050
```

**See [INSTALL.md](INSTALL.md) for detailed setup instructions.**

## Features

✅ **61 active modules** across 40+ intelligence sources  
✅ **Georgian-focused**: NAPR registry, cadastre, tax, courts, business directory  
✅ **Recursive pivoting**: Discover connected entities automatically  
✅ **Interactive graph**: Visualize relationships (Cytoscape)  
✅ **Map view**: Geolocate entities  
✅ **Cases**: Group and merge multiple scans  
✅ **Monitors**: Schedule scans with change alerts  
✅ **Dark UI**: Mobile-responsive design  
✅ **No rate limits**: Run locally, speed depends on your machine  
✅ **All free API keys**: Optional integrations with free tiers

## What it covers
| Target | Native modules | Wrapped tools |
|---|---|---|
| Username | 13 profile APIs with bio data (GitHub incl. commit emails, GitLab, Reddit, Keybase proofs, HN, Dev.to, Chess.com, Lichess, Docker Hub, Gravatar, Codeberg, Bluesky, Mastodon) + 50-site quick check | **Sherlock** (400+ sites), **Maigret** (3000+ sites) |
| Email | MX/deliverability, free/disposable, Gravatar profile, breaches (XposedOrNot + LeakCheck, free), search links, HIBP*, Hunter* | **holehe** (120+ site registrations) |
| Domain | DNS/SPF/DMARC, WHOIS/RDAP contacts, subdomains (crt.sh, CertSpotter, HackerTarget), Wayback, homepage scrape (emails, phones, socials, tech), VirusTotal* | **theHarvester**, **Recon-ng**, **SpiderFoot** |
| IP | Geolocation/ASN/PTR, Shodan InternetDB (ports, CVEs), Shodan*, AbuseIPDB* | **SpiderFoot** |
| Phone | libphonenumber: carrier, region, line type, time zones; WhatsApp/Telegram/Truecaller links; NumVerify* | **PhoneInfoga** |
| Person name | Wikidata/Wikipedia bio (public figures), username permutations, social & document search | **SpiderFoot** |
| Image / photo | EXIF (camera, author, timestamps, GPS → map), hashes, face detection with crops, reverse search (Google Lens, Yandex, Bing, TinEye) | **ExifTool** |
| Vehicle | VIN decode + safety recalls (NHTSA); plate country/format detection and search links | — |
| Crypto | BTC balance & counterparties, ETH balance + ENS | — |

| Georgia | Business registry (NAPR): companies & individual entrepreneurs by name/ID; Georgian phone and plate sources | — |
| Leaks / dark web | IntelX* (leaks, pastes, darknet, phonebook), Ahmia search links | — |

Also: Telegram profiles/channels, account enrichment (name/bio/photo of every account found),
GitHub deep dive (commit emails, GPG keys, orgs, gists), urlscan.io screenshots, reverse IP.

**Cases** group several scans into one merged graph/report. **Monitors** re-run a scan on a schedule
and record what's new; set an `ntfy_topic` in Settings for phone push alerts (install the ntfy app
and subscribe to the same topic name).

`*` = needs a free/paid API key (Settings tab).

## Layout
```
keftemulator/core.py        scan engine (threaded, recursive pivoting, entity limit)
keftemulator/modules/*.py   modules — subclass core.Module, set `accepts`, implement run()
keftemulator/web.py         Flask API + GUI   (templates/, static/)
data/                       SQLite DB, uploads, config.json (API keys, chmod 600)
tools/                      SpiderFoot, Recon-ng, ExifTool, PhoneInfoga (installed locally)
```
Adding a source is one class: `accepts = ("email",)`, then `ctx.emit("account", url, data={...})`.

## Limits, by design
- **License plates:** registered-owner records sit in government registries and are protected
  by law. The plate module identifies the format and finds public sightings. It does not look up owners.
- **Faces:** it detects and crops faces and gives you general reverse-image search. It does not use
  face-recognition people-search engines.
- Only collect public data, for lawful purposes (journalism, security research, due diligence,
  finding your own exposure). Respect GDPR and platform terms.

## Public hosting (Tailscale Funnel) and on/off control
The app runs as two systemd **user** services: `keftemulator` (the web app on 127.0.0.1:5050)
and `keftemulator-tunnel` (Tailscale Funnel, which publishes it at the machine's permanent
`https://<machine>.<tailnet>.ts.net` URL). Every page and API call requires the login password.

One-time setup:
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up                       # opens a login link
sudo tailscale set --operator=$USER     # lets keft run funnel without sudo
tailscale funnel 5050                   # first time only: prints a link to enable Funnel; Ctrl+C after
```

Control:
```
keft on            # start app + public URL, prints the URL
keft off           # stop both; the URL goes offline
keft status | url | logs | restart
keft password [PW] # set/rotate the login password (logs everyone out)
keft boot on|off   # start automatically at boot
```
