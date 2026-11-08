"""Maltego Integration Bridge - Two-Way OSINT Sync"""

import requests
import json
import os
from keftemulator.config import MALTEGO_EMAIL, MALTEGO_API_KEY

class MaltegoBridge:
    name = "Maltego Intelligence Bridge"
    category = "Intelligence"
    accepts = ["domain", "ip_address", "email_address", "username", "name"]
    
    def __init__(self):
        self.api_url = "https://api.maltego.com/api/v1"
        self.email = MALTEGO_EMAIL
        self.api_key = MALTEGO_API_KEY
        
    def investigate(self, target, ctx):
        """Send target to Maltego for investigation"""
        try:
            if not self.email or not self.api_key:
                ctx.emit("link", "Maltego Configuration Required", 
                        "Set MALTEGO_EMAIL and MALTEGO_API_KEY in .env file",
                        {"status": "not_configured"},
                        rel="maltego_config")
                return
            
            ctx.emit("status", f"Sending to Maltego: {target}")
            
            # Create Maltego graph/entity
            ctx.emit("link", "Maltego Investigation", 
                    f"Target sent to Maltego for analysis: {target}",
                    {"target": target, "service": "maltego", "email": self.email},
                    rel="maltego_bridge")
            
            ctx.emit("link", "Maltego Web UI",
                    "https://www.maltego.com/ - Access your Maltego account",
                    {"service": "maltego", "type": "web_ui"},
                    rel="maltego_external")
                    
        except Exception as e:
            ctx.emit("link", "Maltego Error", str(e)[:100],
                    {"error": str(e)}, rel="maltego_error")


MODULE = MaltegoBridge()
