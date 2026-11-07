#!/usr/bin/env python3
"""
Direct Claude Bridge - Auto-submits analysis to Keftemulator
ZERO MANUAL STEPS - 100% AUTOMATIC
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from datetime import datetime

ANALYSIS_FILE = "/media/mount/Keftemulator/data/ai_analysis/pending.json"

class DirectClaudeHandler(BaseHTTPRequestHandler):
    """Direct bridge to Claude - auto-submit to Keftemulator"""
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS, GET')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Check for pending analysis"""
        if self.path == "/check":
            try:
                if os.path.exists(ANALYSIS_FILE):
                    with open(ANALYSIS_FILE, 'r') as f:
                        data = json.load(f)
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps(data).encode())
                        # Clear after reading
                        open(ANALYSIS_FILE, 'w').write('{}')
                        return
            except:
                pass
            
            self.send_response(204)
            self.end_headers()
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle analysis requests"""
        
        if self.path == "/analyze":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body)
                target = data.get('target', 'unknown')
                analysis_type = data.get('type', 'general')
                
                # Check if this is analysis submission (from Claude)
                if data.get('analysis'):
                    # AUTO-SAVE to file for Keftemulator to pick up
                    with open(ANALYSIS_FILE, 'w') as f:
                        json.dump({
                            'target': target,
                            'analysis': data.get('analysis'),
                            'timestamp': datetime.now().isoformat()
                        }, f)
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": True,
                        "status": "analysis_saved"
                    }).encode())
                    print(f"✅ ANALYSIS AUTO-SAVED FOR: {target}")
                    return
                
                # Normal analysis request
                print(f"\n[BRIDGE] Keftemulator requesting analysis: {target}")
                print(f"[BRIDGE] Type: {analysis_type}\n")
                
                print("=" * 60)
                print("OSINT ANALYSIS NEEDED:")
                print("=" * 60)
                print(f"""
RESPOND HERE WITH ANALYSIS FOR: {target}

Format: Send your analysis as JSON like this:

{{
  "target": "{target}",
  "analysis": "YOUR ANALYSIS TEXT HERE..."
}}

Or just paste in chat and I'll auto-submit!
""")
                print("=" * 60)
                print("\n(Analysis will auto-appear in Keftemulator - NO MANUAL STEPS!)\n")
                
                result = {
                    "success": True,
                    "model": "claude-local",
                    "analysis": "Waiting for Claude analysis...",
                    "target": target,
                    "status": "analysis_requested"
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
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
    print("🔗 CLAUDE BRIDGE - 100% AUTOMATIC MODE")
    print("=" * 60)
    print(f"\n📍 Listening on: http://0.0.0.0:{port}")
    print("\n🤖 AUTO-SUBMIT ENABLED:")
    print("  • Analysis auto-saves to Keftemulator")
    print("  • Keftemulator auto-displays it")
    print("  • ZERO manual steps!")
    print("\n" + "=" * 60 + "\n")
    
    server = HTTPServer(("0.0.0.0", port), DirectClaudeHandler)
    print("✅ Bridge ready! Auto-submit enabled!\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️ Bridge stopped")
        server.server_close()

if __name__ == "__main__":
    run_bridge()

