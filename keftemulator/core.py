"""Scan engine: SpiderFoot-style event-driven recursion over pluggable modules."""
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor

from . import db
from .util import load_config, find_tool, api_key

# Entity types that trigger further modules when discovered.
PIVOT_TYPES = {"username", "email", "domain", "ip", "phone", "name", "vin",
               "btc", "eth", "image_url", "image", "url", "plate", "company"}


class Module:
    name = ""            # unique id
    title = ""           # display
    category = "misc"
    description = ""
    accepts = ()         # entity types handled
    requires_tool = None  # external binary (str)
    requires_key = None   # api key name in config
    default = True        # enabled by default
    external = False      # wraps a third-party tool
    enricher = False      # runs on every new entity of its types, even non-pivot ones (adds detail only)
    homepage = ""

    def status(self):
        if self.requires_tool and not find_tool(self.requires_tool):
            return False, f"'{self.requires_tool}' not installed"
        if self.requires_key and not api_key(self.requires_key):
            return False, f"API key '{self.requires_key}' not set"
        return True, "ready"

    def run(self, ent, ctx):
        raise NotImplementedError

    def info(self):
        ok, why = self.status()
        return {"name": self.name, "title": self.title or self.name, "category": self.category,
                "description": self.description, "accepts": list(self.accepts),
                "available": ok, "status": why, "default": self.default,
                "external": self.external, "homepage": self.homepage,
                "requires_tool": self.requires_tool, "requires_key": self.requires_key}


class Entity:
    __slots__ = ("id", "type", "value", "depth", "data")

    def __init__(self, nid, etype, value, depth, data=None):
        self.id, self.type, self.value, self.depth, self.data = nid, etype, value, depth, data or {}


class Ctx:
    """Handed to a module while it processes one entity."""

    def __init__(self, scan, ent, module):
        self.scan, self.ent, self.module = scan, ent, module

    @property
    def stopped(self):
        return self.scan.stop_flag.is_set()

    def log(self, msg, level="info"):
        db.log(self.scan.id, f"[{self.module.name}] {msg}", level)

    def emit(self, etype, value, label=None, data=None, rel="", pivot=True, parent=None):
        """Record a finding linked to the current entity. Returns node id."""
        if value is None or str(value).strip() == "":
            return None
        return self.scan.add_entity(etype, str(value).strip(), label, data, self.module.name,
                                    self.ent.depth + 1, parent if parent is not None else self.ent.id,
                                    rel, pivot)

    def update(self, data):
        """Merge data into the entity currently being processed."""
        db.add_node(self.scan.id, self.ent.type, self.ent.value, None, data, self.module.name, self.ent.depth)


class Scan(threading.Thread):
    running = {}

    def __init__(self, scan_id, target, ttype, modules, depth):
        super().__init__(daemon=True)
        cfg = load_config()
        self.id, self.target, self.ttype = scan_id, target, ttype
        self.modules = modules
        self.max_depth = depth
        self.max_entities = int(cfg.get("max_entities", 400))
        self.pool = ThreadPoolExecutor(max_workers=int(cfg.get("threads", 8)))
        self.stop_flag = threading.Event()
        self.cond = threading.Condition()
        self.pending = 0
        self.count = 0
        Scan.running[scan_id] = self

    # ------------------------------------------------------------------
    def add_entity(self, etype, value, label, data, module, depth, parent, rel, pivot):
        if self.stop_flag.is_set():
            return None
        nid, new = db.add_node(self.id, etype, value, label, data, module, depth)
        db.add_edge(self.id, parent, nid, rel)
        if new:
            self.count += 1
            if (pivot and etype in PIVOT_TYPES and depth <= self.max_depth
                    and self.count < self.max_entities):
                self.dispatch(Entity(nid, etype, value, depth, data))
            elif self.count < self.max_entities:
                self.dispatch(Entity(nid, etype, value, depth, data), enrich_only=True)
            if self.count == self.max_entities:
                db.log(self.id, f"Entity limit ({self.max_entities}) reached; no further pivoting", "warn")
        return nid

    def dispatch(self, ent, enrich_only=False):
        for m in self.modules:
            if ent.type in m.accepts and (m.enricher or not enrich_only):
                with self.cond:
                    self.pending += 1
                self.pool.submit(self._job, m, ent)

    def _job(self, m, ent):
        try:
            if not self.stop_flag.is_set():
                m.run(ent, Ctx(self, ent, m))
        except Exception as e:  # noqa: BLE001 - module errors must not kill a scan
            db.log(self.id, f"[{m.name}] error on {ent.value}: {e}", "error")
            traceback.print_exc()
        finally:
            with self.cond:
                self.pending -= 1
                self.cond.notify_all()

    def run(self):
        db.log(self.id, f"Scan started: {self.target} ({self.ttype}), "
                        f"{len(self.modules)} modules, depth {self.max_depth}")
        nid, _ = db.add_node(self.id, self.ttype, self.target, self.target, {"root": True}, "input", 0)
        self.count = 1
        self.dispatch(Entity(nid, self.ttype, self.target, 0))
        with self.cond:
            while self.pending > 0 and not self.stop_flag.is_set():
                self.cond.wait(1)
        self.pool.shutdown(wait=False, cancel_futures=True)
        status = "stopped" if self.stop_flag.is_set() else "finished"
        db.finish_scan(self.id, status)
        db.log(self.id, f"Scan {status}. {self.count} entities.")
        Scan.running.pop(self.id, None)

    def stop(self):
        self.stop_flag.set()
        with self.cond:
            self.cond.notify_all()
