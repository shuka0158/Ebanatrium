"""Local Intelligence Synthesizer - Free AI-powered reports"""
import requests
from ..core import Module

class LocalIntelligenceSynthesizer(Module):
    name = "local_intelligence"
    title = "Local AI Intelligence Report"
    category = "Intelligence"
    description = "Generate free AI intelligence reports using Ollama"
    accepts = ("company", "domain", "ip_address", "url")

    OLLAMA_URL = "http://localhost:11434/api/generate"
    MODEL = "mistral"

    def run(self, ent, ctx):
        target = ent.value.strip()
        
        ctx.log(f"Generating intelligence report: {target}", "info")
        
        prompt = f"""Create a brief OSINT intelligence report for: {target}

Format:
📋 SUMMARY (2 sentences)
🎯 KEY POINTS (3-4 bullet points)
⚠️ RISK LEVEL (LOW/MEDIUM/HIGH)
✅ ACTIONS (2-3 recommended next steps)

Be professional and actionable."""
        
        try:
            resp = requests.post(
                self.OLLAMA_URL,
                json={
                    "model": self.MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.5
                },
                timeout=90
            )
            
            if resp.status_code == 200:
                result = resp.json()
                report = result.get('response', '')
                
                if report:
                    ctx.log("✅ Intelligence report generated", "info")
                    ctx.emit("company", f"📊 INTELLIGENCE REPORT: {target}", target, {
                        "report": report,
                        "model": self.MODEL,
                        "source": "local_ai",
                        "cost": "FREE - LOCAL"
                    }, rel="intelligence_report")
                    
        except requests.exceptions.ConnectionError:
            ctx.log("Ollama not running", "warn")
        except Exception as e:
            ctx.log(f"Report error: {str(e)[:50]}", "warn")

