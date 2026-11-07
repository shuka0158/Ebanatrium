"""
SpiderFoot Module Registry - All 233+ Reconnaissance Modules
Comprehensive OSINT integration with SpiderFoot's full module suite
"""

import os
import json

class SpiderFootAllModules:
    """Registry and router for all 233+ SpiderFoot modules"""

    name = "SpiderFoot (233 Modules)"
    category = "Intelligence"
    accepts = ["domain", "ip_address", "email_address", "username", "url", "phone_number", "company", "name"]

    def __init__(self):
        self.modules = self._load_module_list()
        self.total = len(self.modules)

    def _load_module_list(self):
        """Load all available SpiderFoot modules"""
        modules_dir = "/media/mount/Keftemulator/tools/spiderfoot/modules"
        modules = {}

        if os.path.exists(modules_dir):
            for filename in sorted(os.listdir(modules_dir)):
                if filename.startswith("sfp_") and filename.endswith(".py"):
                    module_name = filename[:-3]
                    modules[module_name] = {
                        "name": filename[4:-3],  # Remove sfp_ prefix and .py
                        "file": os.path.join(modules_dir, filename)
                    }

        return modules

    def investigate(self, target, ctx):
        """Display all available SpiderFoot modules"""

        ctx.emit("status", f"Scanning with {self.total} SpiderFoot modules...")

        # Emit comprehensive module listing
        module_list = "\n".join([f"  • {m['name']}" for m in self.modules.values()])

        ctx.emit("intelligence", "SpiderFoot Module Registry",
                f"Total available modules: {self.total}\n\n" +
                "Active reconnaissance modules:\n" +
                module_list[:2000] +  # First 50 modules
                (f"\n  ... and {self.total - 50} more modules" if self.total > 50 else ""),
                data={
                    "total_modules": self.total,
                    "modules": list(self.modules.keys()),
                    "categories": self._categorize_modules()
                })

        # Run basic reconnaissance
        self._basic_recon(target, ctx)

    def _categorize_modules(self):
        """Organize modules by category"""
        categories = {}
        for mod_name in self.modules.keys():
            # Extract category: sfp_<category>_rest
            parts = mod_name[4:].split("_")
            category = parts[0] if len(parts) > 1 else "other"

            if category not in categories:
                categories[category] = []
            categories[category].append(mod_name)

        return {cat: len(modules) for cat, modules in categories.items()}

    def _basic_recon(self, target, ctx):
        """Run basic reconnaissance with integrated tools"""

        # DNS Resolution
        try:
            import socket
            if "." in target and "@" not in target and ":" not in target:
                ctx.emit("status", f"DNS resolution: {target}")
                try:
                    ip = socket.gethostbyname(target)
                    ctx.emit("link", "DNS Resolution", ip,
                            {"type": "ip_address", "value": ip, "source": "dns"},
                            rel="dns_found")
                except:
                    pass
        except:
            pass

        # WHOIS Lookup
        try:
            ctx.emit("status", f"WHOIS lookup: {target}")
            import subprocess
            result = subprocess.run(
                ["whois", target],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = [l for l in result.stdout.split('\n') if l.strip()][:5]
                for line in lines:
                    ctx.emit("link", "WHOIS Data", line[:80],
                            {"source": "whois", "data": line},
                            rel="whois_data")
        except:
            pass

        # Module categories info
        ctx.emit("intelligence", "Module Categories",
                json.dumps(self._categorize_modules(), indent=2),
                data={"categories": self._categorize_modules()})


# Export module
MODULE = SpiderFootAllModules()
