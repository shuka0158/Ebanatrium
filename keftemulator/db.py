"""SQLite storage for scans, entities (nodes), relations (edges) and logs."""
import json
import sqlite3
import threading
import time

from .util import DATA

_lock = threading.RLock()
_conn = sqlite3.connect(DATA / "keftemulator.db", check_same_thread=False)
_conn.row_factory = sqlite3.Row
_conn.executescript("""
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS scans(
  id INTEGER PRIMARY KEY AUTOINCREMENT, target TEXT, ttype TEXT, status TEXT,
  created REAL, finished REAL, modules TEXT, depth INTEGER, notes TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS nodes(
  id INTEGER PRIMARY KEY AUTOINCREMENT, scan_id INTEGER, key TEXT, type TEXT,
  value TEXT, label TEXT, data TEXT, module TEXT, depth INTEGER, created REAL,
  UNIQUE(scan_id, key));
CREATE TABLE IF NOT EXISTS edges(
  scan_id INTEGER, src INTEGER, dst INTEGER, label TEXT,
  UNIQUE(scan_id, src, dst));
CREATE TABLE IF NOT EXISTS logs(
  id INTEGER PRIMARY KEY AUTOINCREMENT, scan_id INTEGER, ts REAL, level TEXT, msg TEXT);
CREATE INDEX IF NOT EXISTS ix_nodes_scan ON nodes(scan_id);
CREATE INDEX IF NOT EXISTS ix_logs_scan ON logs(scan_id);
""")


def q(sql, args=(), one=False):
    with _lock:
        cur = _conn.execute(sql, args)
        rows = cur.fetchall()
    return (rows[0] if rows else None) if one else rows


def x(sql, args=()):
    with _lock:
        cur = _conn.execute(sql, args)
        _conn.commit()
        return cur.lastrowid


def create_scan(target, ttype, modules, depth):
    return x("INSERT INTO scans(target,ttype,status,created,modules,depth) VALUES(?,?,?,?,?,?)",
             (target, ttype, "running", time.time(), json.dumps(modules), depth))


def finish_scan(scan_id, status="finished"):
    x("UPDATE scans SET status=?, finished=? WHERE id=?", (status, time.time(), scan_id))


def add_node(scan_id, etype, value, label, data, module, depth):
    """Insert node; returns (node_id, is_new). Merges data into existing nodes."""
    key = f"{etype}:{value.lower() if etype not in ('image',) else value}"
    with _lock:
        row = _conn.execute("SELECT id, data FROM nodes WHERE scan_id=? AND key=?",
                            (scan_id, key)).fetchone()
        if row:
            if data:
                old = json.loads(row["data"] or "{}")
                for k, v in data.items():
                    if v not in (None, "", [], {}) and k not in old:
                        old[k] = v
                _conn.execute("UPDATE nodes SET data=? WHERE id=?", (json.dumps(old, default=str), row["id"]))
                _conn.commit()
            return row["id"], False
        cur = _conn.execute(
            "INSERT INTO nodes(scan_id,key,type,value,label,data,module,depth,created) VALUES(?,?,?,?,?,?,?,?,?)",
            (scan_id, key, etype, value, label or value, json.dumps(data or {}, default=str),
             module, depth, time.time()))
        _conn.commit()
        return cur.lastrowid, True


def add_edge(scan_id, src, dst, label=""):
    if src is None or src == dst:
        return
    x("INSERT OR IGNORE INTO edges(scan_id,src,dst,label) VALUES(?,?,?,?)", (scan_id, src, dst, label))


def log(scan_id, msg, level="info"):
    x("INSERT INTO logs(scan_id,ts,level,msg) VALUES(?,?,?,?)", (scan_id, time.time(), level, msg))


def node_dict(r):
    d = dict(r)
    d["data"] = json.loads(d["data"] or "{}")
    d.pop("key", None)
    return d


def scan_dict(r):
    d = dict(r)
    d["modules"] = json.loads(d["modules"] or "[]")
    return d


def delete_scan(scan_id):
    for t in ("nodes", "edges", "logs"):
        x(f"DELETE FROM {t} WHERE scan_id=?", (scan_id,))
    x("DELETE FROM scans WHERE id=?", (scan_id,))


# ---------------------------------------------------------------- cases & monitors
_conn.executescript("""
CREATE TABLE IF NOT EXISTS cases(
  id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, notes TEXT DEFAULT '', created REAL);
CREATE TABLE IF NOT EXISTS monitors(
  id INTEGER PRIMARY KEY AUTOINCREMENT, target TEXT, ttype TEXT, modules TEXT, depth INTEGER,
  interval_hours REAL, enabled INTEGER DEFAULT 1, case_id INTEGER, created REAL,
  last_run REAL, last_scan_id INTEGER, last_new INTEGER DEFAULT 0, runs INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS monitor_events(
  id INTEGER PRIMARY KEY AUTOINCREMENT, monitor_id INTEGER, scan_id INTEGER, ts REAL,
  new_count INTEGER, items TEXT, seen INTEGER DEFAULT 0);
""")
if "case_id" not in [r[1] for r in _conn.execute("PRAGMA table_info(scans)")]:
    _conn.execute("ALTER TABLE scans ADD COLUMN case_id INTEGER")
    _conn.commit()


def node_keys(scan_id):
    return {r["key"]: r for r in q("SELECT key,type,value,label FROM nodes WHERE scan_id=?", (scan_id,))}
