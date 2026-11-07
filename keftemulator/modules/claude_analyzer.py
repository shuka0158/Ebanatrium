"""Claude AI Analyzer - Intelligent investigation analysis"""
import requests
import json
from ..core import Module

class ClaudeAnalyzer(Module):
    name = "claude_analyzer"
    title = "Claude AI Analyzer"
    category = "Intelligence"
    description = "Use Claude AI to analyze findings and extract insights"
    accepts = ("company", "url", "email_address", "phone", "ip_address")

    # Set your Claude API key here
    CLAUDE_API_KEY = "sk-ant-"  # Will be set via environment
    CLAUDE_MODEL = "claude-3-5-sonnet-20241022"

    def run(self, ent, ctx):
        target = ent.value.strip()
        
        ctx.log(f"Claude AI analyzing: {target}", "info")
        
        # Build analysis prompt based on entity type
        analysis_prompt = f"""
You are an OSINT intelligence analyst. Analyze this target and provide insights:

TARGET: {target}
TYPE: {ent.type}

Provide:
1. What this likely represents (person/business/service/etc)
2. Risk level assessment (low/medium/high/critical)
3. Recommended investigation vectors
4. Potential connections to find
5. Data sources to check
6. Summary assessment

Be precise and factual. Only suggest legitimate OSINT techniques.
"""
        
        try:
            # Call Claude API
            import os
            api_key = os.environ.get('CLAUDE_API_KEY') or self.CLAUDE_API_KEY
            
            if not api_key or api_key == "sk-ant-":
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
                    "model": self.CLAUDE_MODEL,
                    "max_tokens": 1024,
                    "messages": [
                        {
                            "role": "user",
                            "content": analysis_prompt
                        }
                    ]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result['content'][0]['text']
                
                ctx.log("✅ Claude analysis complete", "info")
                ctx.emit("company", f"🤖 AI ANALYSIS: {target}", target, {
                    "analysis": analysis,
                    "model": self.CLAUDE_MODEL,
                    "source": "claude_ai"
                }, rel="ai_analysis")
                
            else:
                ctx.log(f"Claude API error: {response.status_code}", "warn")
                
        except Exception as e:
            ctx.log(f"Claude analysis error: {str(e)[:50]}", "warn")

