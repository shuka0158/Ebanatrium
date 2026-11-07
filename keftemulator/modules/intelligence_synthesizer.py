"""Intelligence Synthesizer - Combine all data into actionable intelligence"""
import requests
import json
from ..core import Module

class IntelligenceSynthesizer(Module):
    name = "intelligence_synthesizer"
    title = "Intelligence Synthesizer"
    category = "Intelligence"
    description = "Use AI to synthesize all findings into actionable intelligence"
    accepts = ("company", "domain", "ip_address")

    def run(self, ent, ctx):
        target = ent.value.strip()
        
        ctx.log(f"Synthesizing intelligence report for: {target}", "info")
        
        synthesis_prompt = f"""
You are creating an executive intelligence summary for target: {target}

This is from an automated OSINT investigation.

Create a brief intelligence report with:
1. EXECUTIVE SUMMARY (2-3 sentences)
2. KEY FINDINGS (bullet points)
3. RISK ASSESSMENT
4. RECOMMENDED ACTIONS
5. CONFIDENCE LEVEL

Keep it professional and actionable.
"""
        
        try:
            import os
            api_key = os.environ.get('CLAUDE_API_KEY')
            
            if not api_key:
                ctx.log("Claude API key not set", "warn")
                return
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 2048,
                    "messages": [
                        {
                            "role": "user",
                            "content": synthesis_prompt
                        }
                    ]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                report = result['content'][0]['text']
                
                ctx.log("✅ Intelligence report generated", "info")
                ctx.emit("company", f"📊 INTELLIGENCE REPORT: {target}", target, {
                    "report": report,
                    "generated_by": "claude_ai",
                    "source": "intelligence_synthesizer"
                }, rel="intelligence_report")
                
        except Exception as e:
            ctx.log(f"Synthesis error: {str(e)[:50]}", "warn")

