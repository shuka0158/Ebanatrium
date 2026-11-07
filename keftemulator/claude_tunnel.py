#!/usr/bin/env python3
"""
Local Claude Tunnel - Connect Keftemulator to Claude directly
No API costs - Uses your existing Claude subscription
Smart fallback: Opus → Sonnet → Haiku
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess
import sys
import os

class ClaudeTunnelHandler(BaseHTTPRequestHandler):
    """Handle OSINT analysis requests through local Claude"""
    
    MODELS = [
        "claude-opus-4-1-20250805",      # Most powerful, try first
        "claude-3-5-sonnet-20241022",    # Good balance
        "claude-3-5-haiku-20241022",     # Fast, still capable
    ]
    
    def do_POST(self):
        """Handle POST requests from Keftemulator"""
        
        if self.path == "/analyze":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body)
                target = data.get('target', 'unknown')
                analysis_type = data.get('type', 'general')
                
                print(f"\n[TUNNEL] Analyzing: {target} ({analysis_type})")
                
                result = self.analyze_with_fallback(target, analysis_type)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                
            except Exception as e:
                self.send_error(400, str(e))
        else:
            self.send_error(404)
    
    def analyze_with_fallback(self, target, analysis_type):
        """Try models in order: Opus → Sonnet → Haiku"""
        
        prompt = f"""Analyze this OSINT target: {target}

Provide:
1. Assessment
2. Risk Level (LOW/MEDIUM/HIGH/CRITICAL)
3. Key Findings
4. Recommended Actions

Be concise and actionable."""
        
        for model in self.MODELS:
            try:
                print(f"[TUNNEL] Trying {model}...")
                
                result = subprocess.run(
                    [
                        sys.executable, "-c",
                        f"""
import anthropic

client = anthropic.Anthropic()
msg = client.messages.create(
    model="{model}",
    max_tokens=1024,
    messages=[{{"role": "user", "content": {repr(prompt)}}}]
)
print(msg.content[0].text)
"""
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    print(f"[TUNNEL] ✅ Success with {model}")
                    return {
                        "success": True,
                        "model": model,
                        "analysis": result.stdout.strip(),
                        "target": target
                    }
                else:
                    print(f"[TUNNEL] {model} failed: {result.stderr[:100]}")
                    continue
                    
            except Exception as e:
                print(f"[TUNNEL] {model} error: {str(e)[:50]}")
                continue
        
        return {
            "success": False,
            "error": "All models failed - check API key",
            "target": target
        }
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def run_tunnel(port=7777):
    """Start the local Claude tunnel"""
    
    print("=" * 50)
    print("🚀 CLAUDE LOCAL TUNNEL STARTING")
    print("=" * 50)
    print(f"\n📍 Listening on: http://localhost:{port}")
    print("\nFallback order:")
    print("  1️⃣ Claude Opus (most powerful)")
    print("  2️⃣ Claude Sonnet (good balance)")
    print("  3️⃣ Claude Haiku (fast)")
    print("\nKeftemulator will POST to: /analyze")
    print("\nEndpoint: http://localhost:{port}/analyze")
    print("\n" + "=" * 50 + "\n")
    
    server = HTTPServer(("0.0.0.0", port), ClaudeTunnelHandler)
    print("✅ Ready! Listening for requests...\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  Tunnel stopped")
        server.server_close()

if __name__ == "__main__":
    run_tunnel()

