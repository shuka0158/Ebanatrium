"""Password login for the web GUI (required once the app is exposed publicly)."""
import json
import os
import secrets
import sys
import time
from datetime import timedelta

from flask import request, session, redirect, render_template, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from .util import DATA

AUTH_FILE = DATA / "auth.json"
SECRET_FILE = DATA / "secret.key"
MAX_FAILS, LOCK_SECONDS = 5, 15 * 60
_fails = {}  # ip -> [count, first_fail_ts]


def _write_private(path, text):
    path.write_text(text)
    os.chmod(path, 0o600)


def secret_key():
    if not SECRET_FILE.exists():
        _write_private(SECRET_FILE, secrets.token_hex(32))
    return SECRET_FILE.read_text().strip()


def set_password(pw):
    _write_private(AUTH_FILE, json.dumps({"hash": generate_password_hash(pw)}))
    # rotating the secret logs out every existing session
    _write_private(SECRET_FILE, secrets.token_hex(32))


def password_hash():
    if not AUTH_FILE.exists():
        return None
    return json.loads(AUTH_FILE.read_text()).get("hash")


def client_ip():
    # ngrok forwards the real visitor address; only trust it from the local tunnel
    if request.remote_addr in ("127.0.0.1", "::1"):
        fwd = request.headers.get("X-Forwarded-For", "")
        if fwd:
            return fwd.split(",")[0].strip()
    return request.remote_addr


def init(app):
    app.secret_key = secret_key()
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                      PERMANENT_SESSION_LIFETIME=timedelta(days=7))

    @app.before_request
    def guard():
        if request.endpoint in ("login", "static") or session.get("auth"):
            return None
        if request.path.startswith("/api/"):
            return jsonify(error="login required"), 401
        return redirect("/login")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        err = None
        if request.method == "POST":
            ip = client_ip()
            n, t0 = _fails.get(ip, [0, time.time()])
            if time.time() - t0 > LOCK_SECONDS:
                n, t0 = 0, time.time()
            if n >= MAX_FAILS:
                err = "Too many attempts. Try again in 15 minutes."
            else:
                h = password_hash()
                if h and check_password_hash(h, request.form.get("password", "")):
                    _fails.pop(ip, None)
                    session.clear()
                    session.permanent = True
                    session["auth"] = True
                    return redirect("/")
                _fails[ip] = [n + 1, t0]
                time.sleep(1)
                err = "Wrong password."
        return render_template("login.html", error=err,
                               configured=password_hash() is not None), (401 if err else 200)

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect("/login")


if __name__ == "__main__":
    # python -m keftemulator.auth set-password [PASSWORD]
    if len(sys.argv) >= 2 and sys.argv[1] == "set-password":
        pw = sys.argv[2] if len(sys.argv) > 2 else secrets.token_urlsafe(14)
        set_password(pw)
        print(pw)
    else:
        print("usage: python -m keftemulator.auth set-password [PASSWORD]")
