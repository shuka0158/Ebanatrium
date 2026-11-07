"""Deep AI Analysis - Comprehensive synthesis of all findings"""
import requests
import json
from ..core import Module

class DeepAnalysis(Module):
    name = "deep_analysis"
    title = "Deep AI Analysis"
    category = "Intelligence"
    description = "Comprehensive deep analysis synthesizing all findings"
    accepts = ("company", "domain", "ip_address", "url", "email_address", "phone")

    TUNNEL_URL = "http://localhost:7777/analyze"

    def run(self, ent, ctx):
        target = ent.value.strip()
        
        ctx.log(f"🧠 DEEP ANALYSIS: {target}", "info")
        
        # Build comprehensive analysis prompt
        prompt = f"""You are conducting a DEEP OSINT investigation of: {target}

Perform COMPREHENSIVE analysis:

1. 🎯 TARGET IDENTIFICATION
   - What exactly is this? (person/company/domain/IP/service)
   - Primary purpose or function
   - Key characteristics

2. 🔗 RELATIONSHIPS & CONNECTIONS
   - Related entities
   - Infrastructure connections
   - Owner/operator relationships
   - Historical connections

3. 🚨 RISK & THREAT ASSESSMENT
   - Risk level: LOW/MEDIUM/HIGH/CRITICAL
   - Specific threats identified
   - Security issues found
   - Vulnerability indicators

4. 📊 DATA & EVIDENCE
   - Key data points discovered
   - Evidence of activity
   - Temporal patterns
   - Geographic indicators

5. 🕵️ INVESTIGATION VECTOR ANALYSIS
   - Most promising investigation paths
   - Data sources that yielded results
   - Unexplored angles
   - Next logical steps

6. 📈 PATTERN ANALYSIS
   - Behavioral patterns
   - Connection patterns
   - Activity timelines
   - Anomalies detected

7. 💡 INTELLIGENCE SUMMARY
   - Key conclusions
   - High-confidence findings
   - Medium-confidence findings
   - Speculation vs evidence

8. ✅ ACTIONABLE RECOMMENDATIONS
   - Immediate actions
   - Medium-term investigation steps
   - Long-term monitoring
   - Risk mitigation

Be exhaustive. Extract MAXIMUM information. Organize clearly."""
        
        try:
            response = requests.post(
                self.TUNNEL_URL,
                json={
                    "target": target,
                    "type": "deep_analysis"
                },
                timeout=120  # Allow more time for deep analysis
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    analysis = result.get('analysis', '')
                    model = result.get('model', 'unknown')
                    
                    ctx.log(f"✅ Deep analysis complete ({model})", "info")
                    
                    # Emit the comprehensive analysis
                    ctx.emit("company", f"🧠 DEEP INTELLIGENCE: {target}", target, {
                        "deep_analysis": analysis,
                        "model": model,
                        "source": "deep_analysis_engine",
                        "type": "comprehensive_intelligence"
                    }, rel="deep_analysis")
                else:
                    ctx.log(f"Analysis failed: {result.get('error')}", "warn")
            else:
                ctx.log(f"Tunnel error: {response.status_code}", "warn")
                
        except requests.exceptions.Timeout:
            ctx.log("Deep analysis timed out - result too comprehensive", "warn")
        except requests.exceptions.ConnectionError:
            ctx.log("Tunnel not running", "warn")
        except Exception as e:
            ctx.log(f"Error: {str(e)[:50]}", "warn")

