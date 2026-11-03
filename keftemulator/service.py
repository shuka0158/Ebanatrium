"""Starting scans, scheduled monitors and change notifications."""
import json
import threading
import time

from . import db
from .core import Scan
from .modules import load
from .util import load_config, http

MODULES = load()


def start_scan(target, ttype, module_names, depth, case_id=None, label_target=None):
    chosen = [MODULES[m] for m in module_names if m in MODULES and MODULES[m].status()[0]]
    if not chosen:
        chosen = [m for m in MODULES.values() if m.default and m.status()[0]]
    sid = db.create_scan(label_target or target, ttype, [m.name for m in chosen], depth)
    if case_id:
        db.x("UPDATE scans SET case_id=? WHERE id=?", (case_id, sid))
    sc = Scan(sid, target, ttype, chosen, depth)
    sc.start()
    return sid, sc


# ------------------------------------------------------------------ notifications
def notify(title, message, click=None):
    """Push to ntfy.sh (free, no account) when a topic is configured in Settings."""
    topic = (load_config()["api_keys"].get("ntfy_topic") or "").strip()
    if not topic:
        return False
    url = topic if topic.startswith("http") else f"https://ntfy.sh/{topic}"
    headers = {"Title": title.encode("utf-8"), "Tags": "mag"}
    if click:
        headers["Click"] = click
    try:
        http().post(url, data=message.encode("utf-8"), headers=headers, timeout=15)
        return True
    except Exception:
        return False


# ------------------------------------------------------------------ monitors
IGNORE_TYPES = {"link"}  # search links are regenerated every run; not real changes


def run_monitor(mid):
    m = db.q("SELECT * FROM monitors WHERE id=?", (mid,), one=True)
    if not m:
        return
    db.x("UPDATE monitors SET last_run=? WHERE id=?", (time.time(), mid))
    sid, sc = start_scan(m["target"], m["ttype"], json.loads(m["modules"] or "[]"), m["depth"], m["case_id"])
    sc.join(timeout=3 * 3600)
    new = []
    prev = m["last_scan_id"]
    if prev and db.q("SELECT id FROM scans WHERE id=?", (prev,), one=True):
        old = db.node_keys(prev)
        for k, r in db.node_keys(sid).items():
            if k not in old and r["type"] not in IGNORE_TYPES:
                new.append({"type": r["type"], "value": r["value"], "label": r["label"]})
    first = prev is None
    db.x("UPDATE monitors SET last_scan_id=?, last_new=?, runs=runs+1 WHERE id=?",
         (sid, len(new), mid))
    if True:  # record every run, so the history shows "no changes" too
        db.x("INSERT INTO monitor_events(monitor_id,scan_id,ts,new_count,items) VALUES(?,?,?,?,?)",
             (mid, sid, time.time(), len(new), json.dumps(new[:300])))
    if new:
        lines = "\n".join(f"• {n['type']}: {n['label'][:80]}" for n in new[:15])
        more = f"\n…and {len(new) - 15} more" if len(new) > 15 else ""
        notify(f"Keftemulator: {len(new)} new for {m['target']}", lines + more)


_running = set()


def scheduler():
    while True:
        try:
            now = time.time()
            for m in db.q("SELECT * FROM monitors WHERE enabled=1"):
                due = (m["last_run"] or 0) + float(m["interval_hours"]) * 3600
                if now >= due and m["id"] not in _running:
                    _running.add(m["id"])

                    def go(mid=m["id"]):
                        try:
                            run_monitor(mid)
                        finally:
                            _running.discard(mid)
                    threading.Thread(target=go, daemon=True).start()
        except Exception as e:  # noqa: BLE001
            print("scheduler:", e, flush=True)
        time.sleep(60)


def start_scheduler():
    threading.Thread(target=scheduler, daemon=True, name="monitor-scheduler").start()


def run_now(mid):
    if mid in _running:
        return False
    _running.add(mid)

    def go():
        try:
            run_monitor(mid)
        finally:
            _running.discard(mid)
    threading.Thread(target=go, daemon=True).start()
    return True


def is_running(mid):
    return mid in _running


# ------------------------------------------------------------------ cases
def case_graph(case_id):
    """Merge every scan in a case; identical entities from different scans become one node."""
    scans = [db.scan_dict(r) for r in db.q("SELECT * FROM scans WHERE case_id=? ORDER BY id", (case_id,))]
    ids = [s["id"] for s in scans]
    if not ids:
        return scans, [], []
    ph = ",".join("?" * len(ids))
    canon, nodes = {}, {}
    for r in db.q(f"SELECT * FROM nodes WHERE scan_id IN ({ph}) ORDER BY id", ids):
        k = r["key"]
        if k in canon:
            nid = canon[k]
            nodes[nid]["data"].update({kk: vv for kk, vv in json.loads(r["data"] or "{}").items()
                                       if kk not in nodes[nid]["data"]})
            nodes[nid]["depth"] = min(nodes[nid]["depth"], r["depth"])
            canon[r["id"]] = nid
            continue
        canon[k] = r["id"]
        canon[r["id"]] = r["id"]
        nodes[r["id"]] = db.node_dict(r)
    edges, seen = [], set()
    for e in db.q(f"SELECT src,dst,label FROM edges WHERE scan_id IN ({ph})", ids):
        s, d = canon.get(e["src"]), canon.get(e["dst"])
        if s and d and s != d and (s, d) not in seen:
            seen.add((s, d))
            edges.append({"src": s, "dst": d, "label": e["label"]})
    return scans, list(nodes.values()), edges
