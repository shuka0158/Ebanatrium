# Ebanatrium OSINT Intelligence Platform

**Eba[Na]trium** - Advanced Open Source Intelligence (OSINT) platform for deep intelligence gathering.

## 🤝 Contributing

Hey guys, I really wanna make this OSINT powerful and max it out, so if anyone has recommendations about what to add/change, or if you want to contribute, please feel free to open an issue, pull request, or message me on Discord: **@shuka0158**

## Features

- 🔍 **7 Active OSINT Modules** with real data extraction
- 🧬 **GitHub Intelligence** - Real profile data, repositories, followers
- 🔐 **Breach Detection** - Check HaveIBeenPwned database
- 🌐 **Username Finder** - Verify accounts across 100+ platforms
- 📧 **Email & Domain** - theHarvester integration
- 🕷️ **Web Crawler** - Photon web scraping
- 🧪 **Periodic Table Branding** - Na (Sodium) element styling

## Architecture

```
Eba[Na]trium (port 5052)
├── GitHub Real Data Module
├── Breach Database Module
├── Username Finder (Sherlock)
├── theHarvester Bridge
├── Photon Web Crawler
├── VIN Decoder
└── Vehicle Intelligence
```

## Installation

```bash
cd /media/mount/Keftemulator
systemctl --user start ebanatrium.service
```

## Access

- **Web UI**: http://localhost:5052
- **Login**: kefteme

## Technology

- Flask (Python)
- SQLite Database
- Real API Integration (GitHub, HaveIBeenPwned)
- Dark theme UI

## OSINT Capabilities

### Working Modules (Real Data)
✅ GitHub profiles with repos and followers
✅ Breach database searches
✅ Username verification on 100+ platforms
✅ Email and domain discovery
✅ Web crawling
✅ VIN vehicle intelligence
✅ Activity timeline analysis

### Limitations
- ❌ Personal address data (requires paid services)
- ❌ Phone numbers (restricted access)
- ❌ Government databases (requires authorization)

## Responsible Use

This tool is for **authorized security research, ethical pentesting, and educational purposes only**.

- ✅ Use on targets you have permission to test
- ✅ Respect privacy and data protection laws (GDPR, etc.)
- ❌ Do not use for stalking, harassment, or unauthorized access

## License

MIT License

---

**Eba[Na]trium** - Intelligence Through Open Sources
