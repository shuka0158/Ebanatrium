"""Claude Pro Analyzer - Use your Claude Pro subscription"""
import requests
import json
from ..core import Module

class ClaudeProAnalyzer(Module):
    name = "claude_pro_analyzer"
    title = "Claude Pro AI Analysis"
    category = "Intelligence"
    description = "Intelligent analysis using your Claude Pro subscription"
    accepts = ("company", "url", "email_address", "phone", "ip_address", "domain")

    def run(self, ent, ctx):
        target = ent.value.strip()
        ent_type = ent.type
        
        ctx.log(f"Claude Pro analyzing: {target}", "info")
        
        # Build analysis prompt
        prompt = f"""You are an expert OSINT intelligence analyst. Analyze this target comprehensively:

TARGET: {target}
TYPE: {ent_type}

Provide in structured format:
1. ENTITY ASSESSMENT
   - What this represents
   - Significance level
   
2. RISK EVALUATION
   - Risk Level: LOW/MEDIUM/HIGH/CRITICAL
   - Threat indicators
   
3. INTELLIGENCE SUMMARY
   - Key findings
   - Patterns identified
   
4. RECOMMENDED ACTIONS
   - Next investigation vectors
   - Data sources to check
   - Timeline for research

Be precise and actionable. Only suggest legitimate OSINT techniques."""
        
        try:
            import os
            api_key = os.environ.get('CLAUDE_API_KEY')
            
            if not api_key:
                ctx.log("Claude API key not configured", "warn")
                ctx.log("Set: export CLAUDE_API_KEY='sk-ant-YOUR-KEY'", "info")
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
                    "max_tokens": 1500,
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
                analysis = result['content'][0]['text']
                
                ctx.log("✅ Claude Pro analysis complete", "info")
                ctx.emit("company", f"🧠 CLAUDE PRO ANALYSIS: {target}", target, {
                    "analysis": analysis,
                    "model": "claude-3-5-sonnet",
                    "source": "claude_pro",
                    "subscription": "Claude Pro"
                }, rel="ai_analysis")
                
            else:
                ctx.log(f"Claude API error: {response.status_code}", "warn")
                ctx.log(f"Response: {response.text[:100]}", "warn")
                
        except Exception as e:
            ctx.log(f"Analysis error: {str(e)[:50]}", "warn")

