#!/bin/bash
# Keftemulator Setup Script
# Installs dependencies, creates venv, and prompts for API keys

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          KEFTEMULATOR - OSINT PLATFORM SETUP              ║"
echo "║                  61 Modules • 40+ Sources                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install it first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
echo "✓ Python $PYTHON_VERSION detected"
echo ""

# Create venv
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

echo ""
echo "📥 Activating virtual environment..."
source .venv/bin/activate

echo "📚 Installing Python dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

echo ""
echo "🛠️  Installing external tools (this may take a few minutes)..."
bash install_tools.sh 2>/dev/null || echo "⚠️  Some tools may need manual installation"
echo "✓ Tools installation complete"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "🔑 API KEYS CONFIGURATION"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "You can add API keys now or later in the web UI (Settings tab)."
echo "Leave blank to skip any key."
echo ""

# Create config if it doesn't exist
if [ ! -f "data/config.json" ]; then
    mkdir -p data
    cat > data/config.json << 'CONFIGEOF'
{
  "api_keys": {},
  "max_depth": 3,
  "max_entities": 400,
  "threads": 8,
  "tool_timeout": 600
}
CONFIGEOF
fi

declare -A KEYS

# Shodan
read -p "📍 Shodan API key (get free at shodan.io): " KEYS[shodan]
[ -z "${KEYS[shodan]}" ] || echo "✓ Shodan key set"

# VirusTotal
read -p "🦠 VirusTotal API key (get free at virustotal.com): " KEYS[virustotal]
[ -z "${KEYS[virustotal]}" ] || echo "✓ VirusTotal key set"

# Hunter.io
read -p "📧 Hunter.io API key (get free at hunter.io): " KEYS[hunter]
[ -z "${KEYS[hunter]}" ] || echo "✓ Hunter key set"

# GitHub
read -p "🐙 GitHub Token (get at github.com/settings/tokens): " KEYS[github_token]
[ -z "${KEYS[github_token]}" ] || echo "✓ GitHub token set"

# AbuseIPDB
read -p "🔴 AbuseIPDB API key (get free at abuseipdb.com): " KEYS[abuseipdb]
[ -z "${KEYS[abuseipdb]}" ] || echo "✓ AbuseIPDB key set"

# NumVerify
read -p "📱 NumVerify API key (get free at numverify.com): " KEYS[numverify]
[ -z "${KEYS[numverify]}" ] || echo "✓ NumVerify key set"

# CARTO
read -p "🗺️  CARTO API key (get free at carto.com): " KEYS[carto]
[ -z "${KEYS[carto]}" ] || echo "✓ CARTO key set"

# IntelX
read -p "🕵️  IntelX API key (free.intelx.io): " KEYS[intelx]
[ -z "${KEYS[intelx]}" ] || echo "✓ IntelX key set"

# URLScan
read -p "🔗 URLScan API key (get free at urlscan.io): " KEYS[urlscan]
[ -z "${KEYS[urlscan]}" ] || echo "✓ URLScan key set"

# ntfy.sh topic
read -p "🔔 ntfy.sh topic for notifications (optional): " KEYS[ntfy_topic]
[ -z "${KEYS[ntfy_topic]}" ] || echo "✓ ntfy.sh topic set"

# Update config
echo ""
echo "💾 Saving configuration..."
python3 << PYEOF
import json
import sys

config_file = "data/config.json"
with open(config_file, 'r') as f:
    config = json.load(f)

keys_to_add = {
    'shodan': """${KEYS[shodan]}""",
    'virustotal': """${KEYS[virustotal]}""",
    'hunter': """${KEYS[hunter]}""",
    'github_token': """${KEYS[github_token]}""",
    'abuseipdb': """${KEYS[abuseipdb]}""",
    'numverify': """${KEYS[numverify]}""",
    'carto': """${KEYS[carto]}""",
    'intelx': """${KEYS[intelx]}""",
    'urlscan': """${KEYS[urlscan]}""",
    'ntfy_topic': """${KEYS[ntfy_topic]}"""
}

for key, value in keys_to_add.items():
    if value and value.strip():
        config['api_keys'][key] = value

with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)
PYEOF

echo "✓ Configuration saved"

# Set password
echo ""
echo "════════════════════════════════════════════════════════════"
echo "🔐 SET WEB UI PASSWORD"
echo "════════════════════════════════════════════════════════════"
read -sp "Enter password for web UI (default: keftemulator): " PASSWORD
PASSWORD=${PASSWORD:-keftemulator}

python3 -m keftemulator.auth set-password "$PASSWORD" 2>/dev/null || true
echo ""
echo "✓ Password set"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ SETUP COMPLETE!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "🚀 To start Keftemulator, run:"
echo ""
echo "   bash run.sh"
echo ""
echo "Then open: http://127.0.0.1:5050"
echo ""
echo "📖 For more info, see README.md"
echo ""
