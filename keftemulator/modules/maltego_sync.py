"""Maltego Two-Way Sync - Bidirectional Data Integration"""

import json
from datetime import datetime

class MaltegoSync:
    name = "Maltego Two-Way Sync"
    category = "Intelligence"
    accepts = ["domain", "ip_address", "email_address", "username", "name"]
    
    def investigate(self, target, ctx):
        """Sync data between Ebanatrium and Maltego"""
        try:
            ctx.emit("status", f"Syncing with Maltego: {target}")
            
            # Send to Maltego
            ctx.emit("link", "Send to Maltego", 
                    f"Push findings to Maltego for {target}",
                    {"action": "send", "target": target},
                    rel="maltego_sync_send")
            
            # Import from Maltego
            ctx.emit("link", "Import from Maltego",
                    f"Import Maltego findings for {target}",
                    {"action": "import", "target": target},
                    rel="maltego_sync_import")
            
            # Consolidated results
            ctx.emit("link", "Consolidated Intelligence",
                    "Combined findings from Ebanatrium + Maltego",
                    {"consolidated": True, "sources": ["Ebanatrium", "Maltego"]},
                    rel="maltego_consolidated")
                    
        except Exception as e:
            ctx.emit("link", "Sync Error", str(e)[:100],
                    {"error": str(e)}, rel="maltego_error")


MODULE = MaltegoSync()
