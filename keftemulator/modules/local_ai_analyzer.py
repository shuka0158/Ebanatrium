"""Local AI Analyzer - Free open-source AI analysis (Ollama)"""
import requests
import json
from ..core import Module

class LocalAIAnalyzer(Module):
    name = "local_ai_analyzer"
    title = "Local AI Analyzer (Free)"
    category = "Intelligence"
    description = "Use free local AI (Ollama) to analyze findings - ZERO COST"
    accepts = ("company", "url", "email_address", "phone", "ip_address", "domain")

    OLLAMA_URL = "http://localhost:11434/api/generate"
    MODEL = "mistral"  # Free model, excellent quality

    def run(self, ent, ctx):
        target = ent.value.strip()
        ent_type = ent.type
        
        ctx.log(f"Local AI analyzing: {target}", "info")
        
        # Build analysis prompt
        prompt = f"""You are an OSINT analyst. Analyze this target:

Target: {target}
Type: {ent_type}

Provide concisely:
1. What this represents
2. Risk level (LOW/MEDIUM/HIGH/CRITICAL)  
3. Next investigation steps
4. Key findings

Be practical and factual."""
        
        try:
            # Call local Ollama API (completely free)
            resp = requests.post(
                self.OLLAMA_URL,
                json={
                    "model": self.MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7
                },
                timeout=60
            )
            
            if resp.status_code == 200:
                result = resp.json()
                analysis = result.get('response', '')
                
                if analysis:
                    ctx.log("✅ Local AI analysis complete", "info")
                    ctx.emit("company", f"🤖 AI ANALYSIS: {target}", target, {
                        "analysis": analysis,
                        "model": self.MODEL,
                        "source": "local_ai",
                        "cost": "FREE"
                    }, rel="ai_analysis")
                else:
                    ctx.log("No analysis generated", "warn")
                    
            else:
                ctx.log(f"Ollama error: {resp.status_code}", "warn")
                ctx.log("Make sure Ollama is running: ollama serve", "info")
                
        except requests.exceptions.ConnectionError:
            ctx.log("❌ Cannot connect to Ollama", "warn")
            ctx.log("Install & run: ollama serve", "info")
        except Exception as e:
            ctx.log(f"Analysis error: {str(e)[:50]}", "warn")

