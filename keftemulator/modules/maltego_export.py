"""Maltego Graph Export - Export OSINT Results to Maltego Format"""

import json
from datetime import datetime

class MaltegoExport:
    name = "Maltego Graph Export"
    category = "Intelligence"
    accepts = ["domain", "ip_address", "email_address", "username"]
    
    def investigate(self, target, ctx):
        """Export findings to Maltego graph format"""
        try:
            ctx.emit("status", f"Preparing Maltego export for: {target}")
            
            # Create Maltego entity data
            maltego_entity = {
                "entity_type": "maltego.Entity",
                "value": target,
                "properties": {
                    "investigated_by": "Ebanatrium-OSINT",
                    "timestamp": datetime.now().isoformat(),
                    "source": "Ebanatrium"
                }
            }
            
            ctx.emit("link", "Export Graph", 
                    f"Graph exported for: {target}",
                    {"format": "maltego", "data": json.dumps(maltego_entity)},
                    rel="maltego_export")
            
            ctx.emit("link", "Maltego Format Ready",
                    "Results can be imported into Maltego graph",
                    {"exportable": True, "format": "json"},
                    rel="maltego_export")
                    
        except Exception as e:
            ctx.emit("link", "Export Error", str(e)[:100],
                    {"error": str(e)}, rel="maltego_error")


MODULE = MaltegoExport()
