#!/usr/bin/env bash
# Installs the external OSINT tools Keftemulator wraps. No sudo needed.
#   ./install_tools.sh all | sherlock | maigret | holehe | theharvester |
#                      phoneinfoga | exiftool | opencv | spiderfoot | reconng
set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
TOOLS="$ROOT/tools"; BIN="$TOOLS/bin"
mkdir -p "$BIN"
PY="$ROOT/.venv/bin/python"

need_pipx() {
  command -v pipx >/dev/null || { python3 -m pip install --user pipx || return 1; }
}
pipx_i() { need_pipx && pipx install --force "$@"; }

i_sherlock()     { pipx_i sherlock-project; }
i_maigret()      { pipx_i maigret; }
i_holehe()       { pipx_i holehe; }
i_theharvester() {
  # latest needs Python 3.14; 4.9.2 is the newest release that runs on 3.12
  local py; py=$(python3 -c 'import sys;print(sys.version_info[1])')
  if [ "$py" -ge 14 ]; then pipx_i "git+https://github.com/laramies/theHarvester.git"
  else pipx_i "git+https://github.com/laramies/theHarvester.git@4.9.2"; fi
}
i_opencv()       { "$PY" -m pip install "opencv-python-headless<5"; }

i_phoneinfoga() {
  local arch; arch=$(uname -m); [ "$arch" = "aarch64" ] && arch=arm64
  local url="https://github.com/sundowndev/phoneinfoga/releases/latest/download/phoneinfoga_Linux_${arch}.tar.gz"
  echo "downloading $url"
  curl -fsSL "$url" | tar -xz -C "$BIN" phoneinfoga && chmod +x "$BIN/phoneinfoga" && "$BIN/phoneinfoga" version
}

i_exiftool() {
  command -v perl >/dev/null || { echo "perl is required for exiftool"; return 1; }
  local ver; ver=$(curl -fsSL https://exiftool.org/ver.txt)
  echo "ExifTool $ver"
  rm -rf "$TOOLS/exiftool"; mkdir -p "$TOOLS/exiftool"
  curl -fsSL "https://github.com/exiftool/exiftool/archive/refs/tags/${ver}.tar.gz" | tar -xz -C "$TOOLS/exiftool" --strip-components=1
  ln -sf "$TOOLS/exiftool/exiftool" "$BIN/exiftool" && "$BIN/exiftool" -ver
}

i_spiderfoot() {
  local d="$TOOLS/spiderfoot"
  [ -d "$d/.git" ] && git -C "$d" pull --ff-only || git clone --depth 1 https://github.com/smicallef/spiderfoot.git "$d"
  python3 -m venv "$d/venv"
  "$d/venv/bin/pip" install -q --upgrade pip setuptools wheel
  # upstream pins are old; install with relaxed pins for modern Python
  sed -E 's/[<>=~!].*$//' "$d/requirements.txt" | grep -v '^\s*$' > "$d/req-relaxed.txt"
  "$d/venv/bin/pip" install -r "$d/req-relaxed.txt"
  cat > "$BIN/spiderfoot" <<EOF
#!/usr/bin/env bash
cd "$d" && exec "$d/venv/bin/python" "$d/sf.py" "\$@"
EOF
  chmod +x "$BIN/spiderfoot"
  cat > "$BIN/spiderfoot-web" <<EOF
#!/usr/bin/env bash
cd "$d" && exec "$d/venv/bin/python" "$d/sf.py" -l 127.0.0.1:5001
EOF
  chmod +x "$BIN/spiderfoot-web"
  "$BIN/spiderfoot" -M 2>/dev/null | head -3 || true
}

i_reconng() {
  local d="$TOOLS/recon-ng"
  [ -d "$d/.git" ] && git -C "$d" pull --ff-only || git clone --depth 1 https://github.com/lanmaster53/recon-ng.git "$d"
  python3 -m venv "$d/venv"
  "$d/venv/bin/pip" install -q --upgrade pip setuptools wheel
  "$d/venv/bin/pip" install -r "$d/REQUIREMENTS"
  for f in recon-ng recon-cli; do
    cat > "$BIN/$f" <<EOF
#!/usr/bin/env bash
cd "$d" && exec "$d/venv/bin/python" "$d/$f" "\$@"
EOF
    chmod +x "$BIN/$f"
  done
  "$BIN/recon-cli" -C "marketplace refresh" >/dev/null 2>&1
  for m in recon/domains-hosts/hackertarget recon/domains-hosts/certificate_transparency; do
    "$BIN/recon-cli" -C "marketplace install $m"
  done
}

run() { echo; echo "=== $1 ==="; "i_$1" && echo "✔ $1 installed" || echo "✘ $1 failed"; }

case "${1:-all}" in
  all) for t in sherlock maigret holehe theharvester phoneinfoga exiftool opencv spiderfoot reconng; do run "$t"; done ;;
  *) run "$1" ;;
esac
