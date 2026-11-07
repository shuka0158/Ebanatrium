"""Direct Claude Analysis - No API costs, pure local connection"""
import requests
import json
from ..core import Module

class DirectClaudeAnalysis(Module):
    name = "direct_claude_analysis"
    title = "Direct Claude Analysis (Local)"
    category = "Intelligence"
    description = "Direct analysis from Claude running locally - ZERO costs!"
    accepts = ("company", "domain", "ip_address", "url", "email_address", "phone")

    BRIDGE_URL = "http://localhost:7778/analyze"

    def run(self, ent, ctx):
        target = ent.value.strip()
        
        ctx.log(f"🔗 Connecting to local Claude...", "info")
        ctx.log(f"Target: {target}", "info")
        
        try:
            response = requests.post(
                self.BRIDGE_URL,
                json={
                    "target": target,
                    "type": "deep_analysis"
                },
                timeout=300  # Wait up to 5 minutes for Claude to respond
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    analysis = result.get('analysis', '')
                    
                    ctx.log(f"✅ Analysis received from Claude", "info")
                    
                    ctx.emit("company", f"🧠 CLAUDE ANALYSIS: {target}", target, {
                        "analysis": analysis,
                        "source": "direct_claude_local",
                        "cost": "ZERO - Local Connection"
                    }, rel="direct_analysis")
                else:
                    ctx.log(f"Analysis status: {result.get('status')}", "info")
                    
            else:
                ctx.log(f"Bridge error: {response.status_code}", "warn")
                
        except requests.exceptions.ConnectionError:
            ctx.log("❌ Bridge not running", "warn")
            ctx.log("Start bridge: python keftemulator/claude_local_bridge.py", "info")
        except Exception as e:
            ctx.log(f"Error: {str(e)[:50]}", "warn")

