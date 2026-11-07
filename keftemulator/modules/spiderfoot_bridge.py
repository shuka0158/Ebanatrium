"""SpiderFoot Bridge - Direct integration of comprehensive OSINT"""
import sys
sys.path.insert(0, '/media/mount/OSINT_SOURCES/spiderfoot')

from ..core import Module

class SpiderFootBridge(Module):
    name = "spiderfoot_bridge"
    title = "SpiderFoot - Comprehensive OSINT"
    category = "Intelligence"
    description = "Full OSINT reconnaissance using SpiderFoot (200+ modules)"
    accepts = ("domain", "ip_address", "email_address", "username")

    def run(self, ent, ctx):
        target = ent.value.strip()
        
        ctx.log(f"Running SpiderFoot reconnaissance on: {target}", "info")
        
        try:
            from spiderfoot import SpiderFoot
            from spiderfoot.spiderfoot import SpiderFootRunner
            
            # Initialize SpiderFoot
            sf = SpiderFoot()
            sf.debug = False
            
            # Detect target type
            if "@" in target:
                target_type = "EMAIL"
            elif "." in target and "/" not in target:
                target_type = "DOMAIN"
            elif all(c.isdigit() or c == "." for c in target):
                target_type = "IP_ADDRESS"
            else:
                target_type = "USERNAME"
            
            ctx.log(f"Target type: {target_type}", "info")
            
            # Run SpiderFoot scan
            results = sf.startSpiderFootScan(target, target_type)
            
            # Process results
            for result_type, result_data in results.items():
                for data in result_data:
                    if data:
                        ctx.emit("link",
                            f"SpiderFoot: {result_type}",
                            str(data),
                            {"source": "SpiderFoot", "type": result_type},
                            rel="spiderfoot_result")
            
            ctx.log(f"✅ SpiderFoot scan complete", "info")
            
        except Exception as e:
            ctx.log(f"SpiderFoot error: {str(e)[:50]}", "warn")

