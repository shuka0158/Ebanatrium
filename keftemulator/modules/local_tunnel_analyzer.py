"""Local Tunnel Analyzer - Uses local Claude tunnel (zero API costs)"""
import requests
import json
from ..core import Module

class LocalTunnelAnalyzer(Module):
    name = "local_tunnel_analyzer"
    title = "Local Tunnel AI (FREE)"
    category = "Intelligence"
    description = "Analyze using local Claude tunnel - NO API COSTS!"
    accepts = ("company", "url", "email_address", "phone", "ip_address", "domain")

    TUNNEL_URL = "http://localhost:7777/analyze"

    def run(self, ent, ctx):
        target = ent.value.strip()
        
        ctx.log(f"Local tunnel analyzing: {target}", "info")
        
        try:
            response = requests.post(
                self.TUNNEL_URL,
                json={
                    "target": target,
                    "type": ent.type
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    analysis = result.get('analysis', '')
                    model = result.get('model', 'unknown')
                    
                    ctx.log(f"✅ Analysis complete ({model})", "info")
                    ctx.emit("company", f"🚀 LOCAL TUNNEL: {target}", target, {
                        "analysis": analysis,
                        "model": model,
                        "source": "local_tunnel",
                        "cost": "FREE"
                    }, rel="ai_analysis")
                else:
                    ctx.log(f"Tunnel error: {result.get('error')}", "warn")
            else:
                ctx.log(f"Tunnel error: {response.status_code}", "warn")
                
        except requests.exceptions.ConnectionError:
            ctx.log("❌ Tunnel not running", "warn")
            ctx.log("Start tunnel: python keftemulator/claude_tunnel.py", "info")
        except Exception as e:
            ctx.log(f"Error: {str(e)[:50]}", "warn")

