"""Module loader for Keftemulator"""
import importlib
import pkgutil
from pathlib import Path

def load():
    """Load all module classes"""
    modules = {}
    module_dir = Path(__file__).parent
    
    for importer, modname, ispkg in pkgutil.iter_modules([str(module_dir)]):
        if modname.startswith('_'):
            continue
        try:
            mod = importlib.import_module(f'.{modname}', __name__)
            for attr in dir(mod):
                obj = getattr(mod, attr)
                # Check if it's a class with name attribute
                if isinstance(obj, type) and hasattr(obj, 'name') and hasattr(obj, 'run'):
                    # Instantiate the module
                    modules[obj.name] = obj()
        except Exception as e:
            print(f"Warning: Could not load module {modname}: {e}")
    
    return modules

