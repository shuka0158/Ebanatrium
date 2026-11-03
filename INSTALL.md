# Keftemulator Installation Guide

## Quick Start

### Prerequisites
- Python 3.10+
- Linux/Mac (WSL on Windows)
- 2GB+ disk space

### Installation

**1. Clone the repository:**
```bash
git clone https://github.com/shuka0158/Keftemulator.git
cd Keftemulator
```

**2. Run the setup script:**
```bash
bash setup.sh
```

The setup script will:
- Create a Python virtual environment
- Install all dependencies
- Install external tools (Sherlock, PhoneInfoga, ExifTool, etc.)
- Prompt you for API keys
- Set your web UI password

**3. Start Keftemulator:**
```bash
bash run.sh
```

**4. Open in browser:**
```
http://127.0.0.1:5050
```

---

## API Keys (Optional but Recommended)

You can skip during setup and add keys later in the **Settings** tab.

| Service | Free Tier | Where to Get |
|---------|-----------|-------------|
| **Shodan** | Yes (limited) | https://www.shodan.io/ |
| **VirusTotal** | Yes (limited) | https://www.virustotal.com/gui/home/upload |
| **Hunter.io** | Yes (60 credits/month) | https://hunter.io/ |
| **GitHub** | Yes | https://github.com/settings/tokens (Personal access token) |
| **AbuseIPDB** | Yes | https://www.abuseipdb.com/register |
| **NumVerify** | Yes | https://numverify.com/ |
| **CARTO** | Yes | https://carto.com/signup/ |
| **IntelX** | Yes (limited) | https://free.intelx.io/ |
| **URLScan** | Yes | https://urlscan.io/ |
| **HIBP** | Subscription | https://haveibeenpwned.com/API/ |

---

## Manual API Key Configuration

Edit `data/config.json`:
```json
{
  "api_keys": {
    "shodan": "your_key_here",
    "virustotal": "your_key_here",
    "hunter": "your_key_here",
    "github_token": "your_token_here",
    "abuseipdb": "your_key_here",
    "numverify": "your_key_here",
    "carto": "your_key_here",
    "intelx": "your_key_here",
    "urlscan": "your_key_here",
    "ntfy_topic": "your_topic_here"
  },
  "max_depth": 3,
  "max_entities": 400,
  "threads": 8,
  "tool_timeout": 600
}
```

Then restart the app.

---

## External Tools

The setup script installs:
- **Sherlock** - Username search (50+ sites)
- **Maigret** - Username search (200+ sites)
- **holehe** - Email validation
- **theHarvester** - Email/subdomain enumeration
- **PhoneInfoga** - Phone number OSINT
- **ExifTool** - Image metadata extraction
- **SpiderFoot** - Full OSINT framework
- **Recon-ng** - Network reconnaissance

Check installation status: **Settings → Tools**

---

## Configuration

### Change Settings

Edit `data/config.json`:

```json
{
  "max_depth": 3,           // 0-5 recursion levels
  "max_entities": 400,      // Stop scan after N entities
  "threads": 8,             // Parallel module workers
  "tool_timeout": 600       // Max seconds per tool
}
```

### Change Password

```bash
python3 -m keftemulator.auth set-password "newpassword"
```

---

## Usage

### Running a Scan

1. Enter a **target** (username, email, domain, IP, phone, name, company, VIN, license plate)
2. Set **pivot depth** (0-5, default 3)
3. Select **modules** (or use presets: Fast, Default, All)
4. Click **Run Investigation**

### Target Types

| Type | Example | Found |
|------|---------|-------|
| **Username** | john_doe | Social profiles, emails, accounts |
| **Email** | user@example.com | Breaches, accounts, domains |
| **Domain** | example.com | DNS, IPs, certificates, history |
| **IP** | 8.8.8.8 | Geolocation, hosting, services |
| **Phone** | +995 555 123456 | Carrier, location, Georgian lookups |
| **Name** | John Doe | NAPR, Wikidata, social media |
| **Company** | OOO Acme | NAPR registry, court, directors |
| **VIN** | WBADT43452G297186 | Vehicle details, recalls |
| **Plate** | AB-123-CD | Georgian plates, photos |
| **Image** | photo.jpg | EXIF, GPS, reverse search |

### Georgian-Specific Features

- 🇬🇪 **NAPR Registry** - Company search by name or ID code
- 🇬🇪 **Cadastre** - Property and real estate records
- 🇬🇪 **Tax Registry** - TIN (Tax ID) lookup
- 🇬🇪 **Criminal Records** - Georgian court filings
- 🇬🇪 **Business Directory** - Phone, address, contact info
- 🇬🇪 **Vehicle Registry** - Plate and VIN lookup

---

## Cases & Monitors

### Create a Case
Group multiple scans together for complex investigations.

1. Run a scan
2. Click **Add to Case**
3. Choose existing or create new case
4. Scans are merged and deduplicated

### Create a Monitor
Run scans on a schedule and get notified of changes.

1. **Monitors** tab → **New Monitor**
2. Enter target, interval (hours), modules
3. Set ntfy.sh topic in Settings for notifications

---

## Command Line

```bash
# Start the web app
bash run.sh

# Check status
keft status

# View logs
keft logs

# Reset password
python3 -m keftemulator.auth set-password "newpass"

# Access locally
curl http://127.0.0.1:5050
```

---

## Troubleshooting

### Modules show as unavailable
→ Run: `bash setup.sh` again or check **Settings → Tools → Install All Missing**

### Scans finding very little
→ Check API keys in Settings, increase depth, or check tool status

### High memory usage
→ Lower `max_entities` or `threads` in config.json

### Slow scans
→ Reduce `threads` or use `max_depth: 1` for quick checks

---

## Legal & Ethical

- ✅ Only search **public data** you have authorization to investigate
- ✅ Respect **robots.txt** and rate limits
- ✅ Comply with **local data protection laws**
- ❌ No face recognition search
- ❌ No credential theft or unauthorized access
- ❌ No mass targeting or DoS

---

## Features

**61 Active Modules:**
- 10 Georgian-specific tools
- 10 Company & financial intelligence
- 9 Security & threat feeds
- 8 Email & breach databases
- 6 Social media & people search
- 5+ Network reconnaissance
- 5+ Framework integrations

**UI Features:**
- 📊 Interactive graph visualization
- 🗺️ Map view with geolocation
- 📁 Case management
- ⏱️ Scheduled monitors
- 🔔 Push notifications
- 📱 Mobile responsive
- 🌙 Dark theme

---

## Support & Issues

- 📖 **Guide** - Click **?** button in the app
- 🐛 **Bug Reports** - GitHub Issues
- 💡 **Feature Requests** - GitHub Discussions

---

## License

Open source - use for authorized OSINT research only.

---

**Happy investigating! 🔍**
