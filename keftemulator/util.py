"""Shared helpers: HTTP session, subprocess runner, config, target detection."""
import json
import os
import re
import shutil
import subprocess
import threading
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TOOLS = ROOT / "tools"
UPLOADS = DATA / "uploads"
CONFIG_FILE = DATA / "config.json"
for _d in (DATA, UPLOADS):
    _d.mkdir(parents=True, exist_ok=True)

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")

_local = threading.local()


def http() -> requests.Session:
    """Thread-local requests session with a browser UA."""
    s = getattr(_local, "s", None)
    if s is None:
        s = requests.Session()
        s.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
        _local.s = s
    return s


def get(url, **kw):
    kw.setdefault("timeout", 15)
    return http().get(url, **kw)


def get_json(url, **kw):
    r = get(url, **kw)
    if r.status_code == 429:  # one polite retry
        import time
        try:
            wait = min(float(r.headers.get("Retry-After", 3)), 8)
        except ValueError:
            wait = 3
        time.sleep(wait)
        r = get(url, **kw)
    if r.status_code != 200:
        return None
    try:
        return r.json()
    except ValueError:
        return None


# ---------------------------------------------------------------- config
DEFAULT_CONFIG = {
    "api_keys": {
        "shodan": "", "hibp": "", "hunter": "", "virustotal": "",
        "abuseipdb": "", "numverify": "", "github_token": "", "carto": "",
        "intelx": "", "urlscan": "", "ntfy_topic": "",
    },
    "max_depth": 2,
    "max_entities": 400,
    "threads": 8,
    "tool_timeout": 600,
}
_cfg_lock = threading.Lock()


def load_config():
    with _cfg_lock:
        cfg = json.loads(json.dumps(DEFAULT_CONFIG))
        if CONFIG_FILE.exists():
            try:
                saved = json.loads(CONFIG_FILE.read_text())
                for k, v in saved.items():
                    if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                        cfg[k].update(v)
                    else:
                        cfg[k] = v
            except ValueError:
                pass
        return cfg


def save_config(cfg):
    with _cfg_lock:
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
        os.chmod(CONFIG_FILE, 0o600)


def api_key(name):
    return (load_config()["api_keys"].get(name) or "").strip()


# ---------------------------------------------------------------- tools
def find_tool(name):
    """Locate an external binary: PATH, pipx bin dir, or ./tools/bin."""
    for cand in (TOOLS / "bin" / name, Path.home() / ".local" / "bin" / name):
        if cand.exists() and os.access(cand, os.X_OK):
            return str(cand)
    return shutil.which(name)


def run_cmd(args, timeout=None, cwd=None, env=None):
    """Run a command, return (returncode, stdout+stderr)."""
    timeout = timeout or load_config().get("tool_timeout", 600)
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                           cwd=cwd, env=env, errors="replace")
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        return -1, out + "\n[timeout]"
    except FileNotFoundError:
        return -2, f"not found: {args[0]}"


ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def strip_ansi(s):
    return ANSI.sub("", s)


# ---------------------------------------------------------------- detection
RE_EMAIL = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
RE_IPV4 = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
RE_DOMAIN = re.compile(r"^(?=.{1,253}$)([a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$", re.I)
RE_PHONE = re.compile(r"^\+?[\d\s\-().]{7,20}$")
RE_VIN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$", re.I)
RE_BTC = re.compile(r"^(bc1[a-z0-9]{25,59}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})$")
RE_ETH = re.compile(r"^0x[a-fA-F0-9]{40}$")
RE_URL = re.compile(r"^https?://", re.I)
RE_IMG_URL = re.compile(r"^https?://\S+\.(jpe?g|png|gif|webp|bmp|tiff?)(\?\S*)?$", re.I)

TARGET_TYPES = ["auto", "username", "email", "domain", "ip", "phone", "name", "company",
                "image", "image_url", "vin", "plate", "btc", "eth", "url"]


def detect_type(value: str) -> str:
    v = value.strip()
    if RE_EMAIL.match(v):
        return "email"
    if RE_IPV4.match(v) or (":" in v and re.match(r"^[0-9a-fA-F:]+$", v)):
        return "ip"
    if RE_IMG_URL.match(v):
        return "image_url"
    if RE_URL.match(v):
        return "url"
    if RE_ETH.match(v):
        return "eth"
    if RE_BTC.match(v):
        return "btc"
    if re.match(r"^[A-Za-z]{2}-\d{3}-[A-Za-z]{2}$", v):
        return "plate"
    if RE_VIN.match(v) and re.search(r"\d", v) and re.search(r"[A-Za-z]", v):
        return "vin"
    # Phone: has + prefix or formatting chars (spaces, dashes, parens)
    if RE_PHONE.match(v) and (v.startswith("+") or any(c in v for c in " -()")) and sum(c.isdigit() for c in v) >= 7:
        return "phone"
    # Georgian ID: exactly 11 pure digits (no formatting) → search as "name" to trigger all modules
    if v.isdigit() and len(v) == 11:
        return "name"
    # Plain phone: 7+ digits without Georgian ID pattern
    if RE_PHONE.match(v) and sum(c.isdigit() for c in v) >= 7:
        return "phone"
    if RE_DOMAIN.match(v):
        return "domain"
    if " " in v:
        return "name"
    return "username"
