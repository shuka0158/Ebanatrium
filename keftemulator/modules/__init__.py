"""Module registry: every Module subclass in this package is auto-registered."""
import importlib
import pkgutil

from ..core import Module

REGISTRY = {}


def load():
    if REGISTRY:
        return REGISTRY
    for m in pkgutil.iter_modules(__path__):
        importlib.import_module(f"{__name__}.{m.name}")

    def walk(cls):
        for sub in cls.__subclasses__():
            if sub.name:
                REGISTRY[sub.name] = sub()
            walk(sub)
    walk(Module)
    return REGISTRY
