"""Flask web GUI + JSON API."""
import csv
import html
import io
import json
import subprocess
import threading
import time
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, render_template, send_from_directory, send_file, Response, abort

from . import db, __version__, auth, service
from .core import Scan
from .modules import load
from .util import (load_config, save_config, detect_type, TARGET_TYPES, UPLOADS, ROOT, find_tool, DATA)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 40 * 1024 * 1024
auth.init(app)
MODULES = load()
# scans left "running" by a previous process can never finish
db.x("UPDATE scans SET status='interrupted' WHERE status='running'")


@app.route("/")
def index():
    # map tile key: sent to the browser by design (tile requests come from the viewer)
    return render_template("index.html", version=__version__,
                           carto_key=load_config()["api_keys"].get("carto", ""))


@app.route("/uploads/<path:name>")
def uploads(name):
    return send_from_directory(UPLOADS, name)


# ------------------------------------------------------------------ contact tree images
@app.get("/api/contact-tree/image/<path:filename>")
def contact_tree_image(filename):
    """Serve images from contact tree database"""
    from urllib.parse import unquote
    import sqlite3
    import os

    db_path = "/home/shuka/.local/share/keftemulator/contact_tree.db"
    if not os.path.exists(db_path):
        abort(404)

    try:
        # Decode URL-encoded filename
        filename = unquote(filename)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT file_path FROM documents WHERE filename = ? AND file_type = "image"', (filename,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({"error": f"Image not found: {filename}"}), 404

        filepath = row['file_path']
        if not os.path.exists(filepath):
            return jsonify({"error": f"File not found: {filepath}"}), 404

        # Serve the image file with correct MIME type
        import mimetypes
        mimetype = mimetypes.guess_type(filepath)[0] or 'image/png'
        return send_file(filepath, mimetype=mimetype)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------------------------------------------------------ modules
@app.get("/api/modules")
def api_modules():
    return jsonify(sorted((m.info() for m in MODULES.values()), key=lambda x: (x["category"], x["title"])))


@app.get("/api/types")
def api_types():
    return jsonify(TARGET_TYPES)


# ------------------------------------------------------------------ scans
@app.get("/api/scans")
def api_scans():
    rows = db.q("""SELECT s.*, (SELECT COUNT(*) FROM nodes n WHERE n.scan_id=s.id) AS n,
                   (SELECT name FROM cases c WHERE c.id=s.case_id) AS case_name
                   FROM scans s ORDER BY id DESC LIMIT 200""")
    return jsonify([db.scan_dict(r) for r in rows])


@app.post("/api/scans")
def api_new_scan():
    if request.files.get("image"):
        f = request.files["image"]
        ext = Path(f.filename or "x.jpg").suffix.lower()[:6] or ".jpg"
        path = UPLOADS / f"{uuid.uuid4().hex}{ext}"
        f.save(path)
        target, ttype = str(path), "image"
        form = request.form
        mods = json.loads(form.get("modules") or "[]")
        depth = int(form.get("depth", 1))
        case_id = int(form.get("case_id") or 0) or None
    else:
        body = request.get_json(force=True)
        target = (body.get("target") or "").strip()
        ttype = body.get("type") or "auto"
        mods = body.get("modules") or []
        depth = int(body.get("depth", 1))
        case_id = int(body.get("case_id") or 0) or None
        if not target:
            return jsonify(error="empty target"), 400
        if ttype == "auto":
            ttype = detect_type(target)
        if ttype == "email":
            target = target.lower()
        if ttype == "domain":
            target = target.lower().removeprefix("www.")
    depth = max(0, min(depth, 4))
    sid, _ = service.start_scan(target, ttype, mods, depth, case_id,
                                label_target=Path(target).name if ttype == "image" else None)
    return jsonify(id=sid, type=ttype)


@app.get("/api/scans/<int:sid>")
def api_scan(sid):
    s = db.q("SELECT * FROM scans WHERE id=?", (sid,), one=True)
    if not s:
        abort(404)
    since_n = int(request.args.get("since_node", 0))
    since_l = int(request.args.get("since_log", 0))
    nodes = [db.node_dict(r) for r in db.q("SELECT * FROM nodes WHERE scan_id=? AND id>? ORDER BY id",
                                           (sid, since_n))]
    # nodes whose data got enriched after first fetch
    updated = []
    if since_n:
        updated = [db.node_dict(r) for r in db.q(
            "SELECT * FROM nodes WHERE scan_id=? AND id<=? AND depth<=1", (sid, since_n))]
    edges = [dict(r) for r in db.q("SELECT src,dst,label FROM edges WHERE scan_id=?", (sid,))]
    logs = [dict(r) for r in db.q("SELECT * FROM logs WHERE scan_id=? AND id>? ORDER BY id", (sid, since_l))]
    return jsonify(scan=db.scan_dict(s), nodes=nodes, updated=updated, edges=edges, logs=logs)


@app.post("/api/scans/<int:sid>/stop")
def api_stop(sid):
    sc = Scan.running.get(sid)
    if sc:
        sc.stop()
    else:
        db.finish_scan(sid, "stopped")
    return jsonify(ok=True)


@app.delete("/api/scans/<int:sid>")
def api_delete(sid):
    sc = Scan.running.get(sid)
    if sc:
        sc.stop()
    db.delete_scan(sid)
    return jsonify(ok=True)


@app.post("/api/scans/<int:sid>/notes")
def api_notes(sid):
    db.x("UPDATE scans SET notes=? WHERE id=?", (request.get_json(force=True).get("notes", ""), sid))
    return jsonify(ok=True)


@app.get("/api/scans/<int:sid>/export")
def api_export(sid):
    fmt = request.args.get("fmt", "json")
    s = db.scan_dict(db.q("SELECT * FROM scans WHERE id=?", (sid,), one=True))
    nodes = [db.node_dict(r) for r in db.q("SELECT * FROM nodes WHERE scan_id=? ORDER BY id", (sid,))]
    edges = [dict(r) for r in db.q("SELECT src,dst,label FROM edges WHERE scan_id=?", (sid,))]
    fname = f"keftemulator_scan{sid}"
    if fmt == "csv":
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["id", "type", "value", "label", "module", "depth", "data"])
        for n in nodes:
            w.writerow([n["id"], n["type"], n["value"], n["label"], n["module"], n["depth"], json.dumps(n["data"])])
        return Response(buf.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": f"attachment; filename={fname}.csv"})
    if fmt == "html":
        return Response(_html_report(s, nodes, edges), mimetype="text/html",
                        headers={"Content-Disposition": f"attachment; filename={fname}.html"})
    return Response(json.dumps({"scan": s, "nodes": nodes, "edges": edges}, indent=2, default=str),
                    mimetype="application/json",
                    headers={"Content-Disposition": f"attachment; filename={fname}.json"})


def _html_report(s, nodes, edges):
    e = html.escape
    by_type = {}
    for n in nodes:
        by_type.setdefault(n["type"], []).append(n)
    parts = [f"""<!doctype html><meta charset=utf-8><title>Keftemulator report #{s['id']}</title>
<style>body{{font:14px system-ui;margin:2rem auto;max-width:1100px;padding:0 1rem;color:#1b1f24}}
h1{{margin:0}}table{{border-collapse:collapse;width:100%;margin:.5rem 0 1.5rem}}
td,th{{border:1px solid #d0d7de;padding:6px 8px;vertical-align:top;text-align:left}}
th{{background:#f3f4f6}}code{{font-size:12px;white-space:pre-wrap;word-break:break-all}}
.meta{{color:#57606a}}</style>
<h1>Keftemulator OSINT report</h1>
<p class=meta>Target: <b>{e(s['target'])}</b> ({e(s['ttype'])}) · Scan #{s['id']} ·
{time.strftime('%Y-%m-%d %H:%M', time.localtime(s['created']))} · {len(nodes)} entities · {len(edges)} relations</p>"""]
    if s.get("notes"):
        parts.append(f"<h2>Analyst notes</h2><p style='white-space:pre-wrap'>{e(s['notes'])}</p>")
    for t in sorted(by_type):
        parts.append(f"<h2>{e(t)} ({len(by_type[t])})</h2><table><tr><th>Value</th><th>Module</th><th>Details</th></tr>")
        for n in by_type[t]:
            val = e(n["label"] or n["value"])
            if str(n["value"]).startswith("http"):
                val = f"<a href='{e(n['value'])}'>{val}</a>"
            d = json.dumps(n["data"], indent=1, default=str) if n["data"] else ""
            parts.append(f"<tr><td>{val}</td><td>{e(n['module'] or '')}</td><td><code>{e(d)}</code></td></tr>")
        parts.append("</table>")
    return "".join(parts)


# ------------------------------------------------------------------ cases
@app.get("/api/cases")
def api_cases():
    rows = db.q("""SELECT c.*, (SELECT COUNT(*) FROM scans s WHERE s.case_id=c.id) AS scans
                   FROM cases c ORDER BY id DESC""")
    return jsonify([dict(r) for r in rows])


@app.post("/api/cases")
def api_new_case():
    name = (request.get_json(force=True).get("name") or "").strip()[:120]
    if not name:
        return jsonify(error="name required"), 400
    return jsonify(id=db.x("INSERT INTO cases(name,created) VALUES(?,?)", (name, time.time())))


@app.delete("/api/cases/<int:cid>")
def api_delete_case(cid):
    db.x("UPDATE scans SET case_id=NULL WHERE case_id=?", (cid,))
    db.x("UPDATE monitors SET case_id=NULL WHERE case_id=?", (cid,))
    db.x("DELETE FROM cases WHERE id=?", (cid,))
    return jsonify(ok=True)


@app.post("/api/cases/<int:cid>/notes")
def api_case_notes(cid):
    db.x("UPDATE cases SET notes=? WHERE id=?", (request.get_json(force=True).get("notes", ""), cid))
    return jsonify(ok=True)


@app.post("/api/scans/<int:sid>/case")
def api_scan_case(sid):
    cid = request.get_json(force=True).get("case_id") or None
    db.x("UPDATE scans SET case_id=? WHERE id=?", (cid, sid))
    return jsonify(ok=True)


@app.get("/api/cases/<int:cid>")
def api_case(cid):
    c = db.q("SELECT * FROM cases WHERE id=?", (cid,), one=True)
    if not c:
        abort(404)
    scans, nodes, edges = service.case_graph(cid)
    running = any(s["status"] == "running" for s in scans)
    scan_like = {"id": f"case{cid}", "target": c["name"], "ttype": "case", "status": "running" if running else "finished",
                 "created": min([s["created"] for s in scans], default=c["created"]),
                 "finished": max([s["finished"] or 0 for s in scans], default=None) or None,
                 "depth": max([s["depth"] for s in scans], default=0),
                 "modules": sorted({m for s in scans for m in s["modules"]}), "notes": c["notes"]}
    return jsonify(scan=scan_like, case=dict(c), scans=scans, nodes=nodes, updated=[], edges=edges,
                   logs=[], full=True)


@app.get("/api/cases/<int:cid>/export")
def api_case_export(cid):
    c = db.q("SELECT * FROM cases WHERE id=?", (cid,), one=True)
    scans, nodes, edges = service.case_graph(cid)
    s = {"id": f"case {cid}", "target": c["name"] + " — " + ", ".join(x["target"] for x in scans),
         "ttype": "case", "created": c["created"], "notes": c["notes"]}
    return Response(_html_report(s, nodes, edges), mimetype="text/html",
                    headers={"Content-Disposition": f"attachment; filename=keftemulator_case{cid}.html"})


# ------------------------------------------------------------------ monitors
@app.get("/api/monitors")
def api_monitors():
    rows = db.q("""SELECT m.*, (SELECT name FROM cases c WHERE c.id=m.case_id) AS case_name,
                   (SELECT COUNT(*) FROM monitor_events e WHERE e.monitor_id=m.id AND e.seen=0 AND e.new_count>0) AS unseen
                   FROM monitors m ORDER BY id DESC""")
    out = []
    for r in rows:
        d = dict(r)
        d["modules"] = json.loads(d["modules"] or "[]")
        d["running"] = service.is_running(r["id"])
        d["next_run"] = (r["last_run"] or 0) + r["interval_hours"] * 3600 if r["enabled"] else None
        out.append(d)
    return jsonify(out)


@app.post("/api/monitors")
def api_new_monitor():
    b = request.get_json(force=True)
    sid = b.get("scan_id")
    if sid:
        s = db.q("SELECT * FROM scans WHERE id=?", (sid,), one=True)
        if not s or s["ttype"] == "image":
            return jsonify(error="this scan cannot be monitored"), 400
        target, ttype, mods, depth, case_id = s["target"], s["ttype"], s["modules"], s["depth"], s["case_id"]
    else:
        target, ttype = (b.get("target") or "").strip(), b.get("type") or "auto"
        if not target:
            return jsonify(error="empty target"), 400
        if ttype == "auto":
            ttype = detect_type(target)
        mods, depth, case_id = json.dumps(b.get("modules") or []), int(b.get("depth", 1)), b.get("case_id")
    hours = max(1.0, float(b.get("interval_hours", 24)))
    mid = db.x("""INSERT INTO monitors(target,ttype,modules,depth,interval_hours,case_id,created,last_scan_id,last_run)
                  VALUES(?,?,?,?,?,?,?,?,?)""",
               (target, ttype, mods, depth, hours, case_id, time.time(), sid, time.time() if sid else None))
    return jsonify(id=mid)


@app.patch("/api/monitors/<int:mid>")
def api_edit_monitor(mid):
    b = request.get_json(force=True)
    if "enabled" in b:
        db.x("UPDATE monitors SET enabled=? WHERE id=?", (1 if b["enabled"] else 0, mid))
    if "interval_hours" in b:
        db.x("UPDATE monitors SET interval_hours=? WHERE id=?", (max(1.0, float(b["interval_hours"])), mid))
    return jsonify(ok=True)


@app.delete("/api/monitors/<int:mid>")
def api_delete_monitor(mid):
    db.x("DELETE FROM monitor_events WHERE monitor_id=?", (mid,))
    db.x("DELETE FROM monitors WHERE id=?", (mid,))
    return jsonify(ok=True)


@app.post("/api/monitors/<int:mid>/run")
def api_run_monitor(mid):
    return jsonify(ok=service.run_now(mid))


@app.get("/api/monitors/<int:mid>/events")
def api_monitor_events(mid):
    rows = db.q("SELECT * FROM monitor_events WHERE monitor_id=? ORDER BY id DESC LIMIT 30", (mid,))
    db.x("UPDATE monitor_events SET seen=1 WHERE monitor_id=?", (mid,))
    return jsonify([{**dict(r), "items": json.loads(r["items"] or "[]")} for r in rows])


@app.post("/api/notify/test")
def api_notify_test():
    ok = service.notify("Keftemulator test", "Notifications are working.")
    return jsonify(ok=ok) if ok else (jsonify(error="set an ntfy topic in Settings first"), 400)


# ------------------------------------------------------------------ config
@app.get("/api/config")
def api_get_config():
    cfg = load_config()
    cfg["api_keys"] = {k: ("•" * 8 if v else "") for k, v in cfg["api_keys"].items()}
    return jsonify(cfg)


@app.post("/api/config")
def api_set_config():
    body = request.get_json(force=True)
    cfg = load_config()
    for k, v in (body.get("api_keys") or {}).items():
        if v is not None and not set(str(v)) <= {"•"}:
            cfg["api_keys"][k] = v.strip()
    for k in ("max_depth", "max_entities", "threads", "tool_timeout"):
        if k in body:
            cfg[k] = int(body[k])
    save_config(cfg)
    return jsonify(ok=True)


# ------------------------------------------------------------------ external tools
TOOLS = [
    ("sherlock", "sherlock", "Sherlock — username across 400+ sites"),
    ("maigret", "maigret", "Maigret — username dossier, 3000+ sites"),
    ("holehe", "holehe", "holehe — email → registered sites"),
    ("theharvester", "theHarvester", "theHarvester — emails/hosts for a domain"),
    ("phoneinfoga", "phoneinfoga", "PhoneInfoga — phone number scanner"),
    ("exiftool", "exiftool", "ExifTool — full metadata extraction"),
    ("opencv", None, "OpenCV — face detection in images"),
    ("spiderfoot", "spiderfoot", "SpiderFoot — 200+ module automation framework"),
    ("reconng", "recon-cli", "Recon-ng — modular recon framework"),
]
_install = {"running": None, "log": ""}


def _tool_installed(name, binary):
    if name == "opencv":
        try:
            import cv2  # noqa: F401
            return True
        except Exception:
            return False
    return bool(find_tool(binary))


@app.get("/api/tools")
def api_tools():
    return jsonify(tools=[{"name": n, "binary": b, "title": t, "installed": _tool_installed(n, b)}
                          for n, b, t in TOOLS],
                   running=_install["running"], log=_install["log"][-20000:])


@app.post("/api/tools/<name>/install")
def api_install(name):
    if name not in {t[0] for t in TOOLS} | {"all"}:
        abort(404)
    if _install["running"]:
        return jsonify(error="installer busy"), 409

    def run_one(tool):
        _install["log"] += f"\n$ install_tools.sh {tool}\n"
        p = subprocess.Popen(["bash", str(ROOT / "install_tools.sh"), tool], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, cwd=ROOT, errors="replace")
        for line in p.stdout:
            _install["log"] += line
        p.wait()
        return p.returncode

    def work():
        _install["running"] = name
        try:
            if name != "all":
                _install["log"] = ""
                code = run_one(name)
                _install["log"] += f"\n[exit {code}]\n"
                return
            _install["log"] = "Checking installed tools…\n\n"
            missing = []
            for n, b, t in TOOLS:
                ok = _tool_installed(n, b)
                _install["log"] += f"  {'✔ installed' if ok else '✘ missing  '}  {t}\n"
                if not ok:
                    missing.append((n, t))
            if not missing:
                _install["log"] += f"\nEverything is already installed ({len(TOOLS)}/{len(TOOLS)}). Nothing to do.\n"
                return
            _install["log"] += f"\nInstalling {len(missing)} missing tool(s): {', '.join(n for n, _ in missing)}\n"
            for n, _ in missing:
                run_one(n)
            _install["log"] += "\nSummary:\n"
            for n, b, t in TOOLS:
                if any(n == m for m, _ in missing):
                    ok = _tool_installed(n, b)
                    _install["log"] += f"  {'✔ now installed' if ok else '✘ still missing'}  {t}\n"
            _install["log"] += f"\n{sum(_tool_installed(n, b) for n, b, _ in TOOLS)}/{len(TOOLS)} tools installed.\n"
        finally:
            _install["running"] = None
    threading.Thread(target=work, daemon=True).start()
    return jsonify(ok=True)


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Keftemulator OSINT")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5050)
    a = ap.parse_args()
    print(f"\n  Keftemulator v{__version__}  →  http://{a.host}:{a.port}\n  data: {DATA}\n", flush=True)
    if auth.password_hash() is None:
        print("  WARNING: no password set — run `keft password`\n", flush=True)
    service.start_scheduler()
    from waitress import serve
    serve(app, host=a.host, port=a.port, threads=16, trusted_proxy="127.0.0.1",
          trusted_proxy_headers={"x-forwarded-proto"}, clear_untrusted_proxy_headers=False)


if __name__ == "__main__":
    main()
