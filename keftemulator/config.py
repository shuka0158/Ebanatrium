"""Load configuration from environment variables or .env file"""

import os
from pathlib import Path

# Load .env file if it exists
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

# Maltego Configuration
MALTEGO_EMAIL = os.getenv('MALTEGO_EMAIL', '')
MALTEGO_PASSWORD = os.getenv('MALTEGO_PASSWORD', '')
MALTEGO_API_KEY = os.getenv('MALTEGO_API_KEY', '')

# GitHub Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')

# Other API Keys
SHODAN_API_KEY = os.getenv('SHODAN_API_KEY', '')
VIRUSTOTAL_API_KEY = os.getenv('VIRUSTOTAL_API_KEY', '')
