"""Claude Pro Intelligence Reports"""
import requests
import json
from ..core import Module

class ClaudeProReports(Module):
    name = "claude_pro_reports"
    title = "Claude Pro Intelligence Reports"
    category = "Intelligence"
    description = "Generate professional intelligence reports with Claude Pro"
    accepts = ("company", "domain", "ip_address", "url")

    def run(self, ent, ctx):
        target = ent.value.strip()
        
        ctx.log(f"Generating Claude Pro report: {target}", "info")
        
        prompt = f"""Create a professional intelligence executive briefing for OSINT investigation of: {target}

Format as executive intelligence report:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTELLIGENCE BRIEFING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 EXECUTIVE SUMMARY
[2-3 sentences on target and key findings]

🎯 KEY INTELLIGENCE
[3-5 main findings with significance]

⚠️ RISK ASSESSMENT
Level: LOW / MEDIUM / HIGH / CRITICAL
[Brief threat evaluation]

✅ RECOMMENDED ACTIONS
[3-4 priority investigation steps]

📊 CONFIDENCE LEVEL
[HIGH / MEDIUM / LOW - based on evidence]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        
        try:
            import os
            api_key = os.environ.get('CLAUDE_API_KEY')
            
            if not api_key:
                ctx.log("Claude API key not configured", "warn")
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
                    "max_tokens": 2000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                report = result['content'][0]['text']
                
                ctx.log("✅ Intelligence report generated", "info")
                ctx.emit("company", f"📊 INTELLIGENCE REPORT: {target}", target, {
                    "report": report,
                    "model": "claude-3-5-sonnet",
                    "source": "claude_pro",
                    "subscription": "Claude Pro"
                }, rel="intelligence_report")
                
        except Exception as e:
            ctx.log(f"Report error: {str(e)[:50]}", "warn")

