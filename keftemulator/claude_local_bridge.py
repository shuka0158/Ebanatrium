#!/usr/bin/env python3
"""
Direct Claude Bridge - Connects Keftemulator to Claude Code locally
NO API costs - uses local stdin/stdout to Claude context
Uses port 7778 (tunnel uses 7777)
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess
import sys

class DirectClaudeHandler(BaseHTTPRequestHandler):
    """Direct bridge to Claude running in this terminal"""
    
    def do_POST(self):
        """Handle analysis requests directly from Keftemulator"""
        
        if self.path == "/analyze":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body)
                target = data.get('target', 'unknown')
                analysis_type = data.get('type', 'general')
                
                print(f"\n[BRIDGE] Keftemulator requesting analysis: {target}")
                print(f"[BRIDGE] Type: {analysis_type}")
                print(f"[BRIDGE] Waiting for Claude to process...\n")
                
                # Send request to Claude Code context
                request_prompt = f"""
KEFTEMULATOR ANALYSIS REQUEST:
Target: {target}
Type: {analysis_type}

Provide deep OSINT analysis for this target.
Include: identification, relationships, risks, findings, vectors, patterns, summary, recommendations.
"""
                
                print("=" * 60)
                print("OSINT ANALYSIS NEEDED:")
                print("=" * 60)
                print(request_prompt)
                print("=" * 60)
                print("\n(Claude will provide analysis via terminal - please respond)\n")
                
                # For now, return a placeholder that Keftemulator expects
                result = {
                    "success": True,
                    "model": "claude-local",
                    "analysis": "Waiting for Claude analysis...",
                    "target": target,
                    "status": "analysis_requested"
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                
            except Exception as e:
                self.send_error(400, str(e))
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def run_bridge(port=7778):
    """Start the direct Claude bridge"""
    
    print("\n" + "=" * 60)
    print("🔗 DIRECT CLAUDE BRIDGE - STARTING")
    print("=" * 60)
    print(f"\n📍 Local connection: http://localhost:{port}")
    print("\n💬 How this works:")
    print("  1. Keftemulator sends analysis request to localhost:7778")
    print("  2. Bridge prints request in your terminal")
    print("  3. YOU provide analysis as Claude")
    print("  4. Results sent back to Keftemulator")
    print("\n🎯 Cost: ZERO (local connection only)")
    print("\n" + "=" * 60 + "\n")
    
    server = HTTPServer(("localhost", port), DirectClaudeHandler)
    print("✅ Bridge ready! Listening for Keftemulator requests...\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️ Bridge stopped")
        server.server_close()

if __name__ == "__main__":
    run_bridge()

