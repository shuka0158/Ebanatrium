#!/usr/bin/env python3
"""
Direct Claude Bridge - Auto-submits analysis to Eba[Na]trium
100% AUTOMATIC - NO MANUAL STEPS
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from datetime import datetime

ANALYSIS_FILE = "/media/mount/Keftemulator/data/ai_analysis/pending.json"

class DirectClaudeHandler(BaseHTTPRequestHandler):
    """Direct bridge - auto-submit to Eba[Na]trium"""
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS, GET')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Return pending analysis"""
        if self.path == "/check":
            try:
                if os.path.exists(ANALYSIS_FILE):
                    with open(ANALYSIS_FILE, 'r') as f:
                        content = f.read()
                        data = json.loads(content) if content and content != '{}' else {}
                        
                        if data and data.get('analysis'):
                            # Found analysis - return it
                            self.send_response(200)
                            self.send_header('Content-Type', 'application/json')
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            self.wfile.write(json.dumps(data).encode())
                            # KEEP the file so multiple reads work
                            return
            except:
                pass
            
            # No analysis or error
            self.send_response(204)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle analysis requests and submissions"""
        
        if self.path == "/analyze":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body)
                target = data.get('target', 'unknown')
                analysis = data.get('analysis')
                analysis_type = data.get('type', 'general')
                
                # Check if this is analysis submission
                if analysis:
                    # SAVE to file for Keftemulator to pick up
                    os.makedirs(os.path.dirname(ANALYSIS_FILE), exist_ok=True)
                    with open(ANALYSIS_FILE, 'w') as f:
                        json.dump({
                            'target': target,
                            'analysis': analysis,
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
                    print(f"\n✅ ANALYSIS AUTO-SAVED FOR: {target}\n")
                    return
                
                # Normal analysis request
                print(f"\n[BRIDGE] Analyzing: {target}")
                print("=" * 60)
                print("RESPOND WITH ANALYSIS!")
                print("=" * 60)
                print(f"\nTarget: {target}")
                print(f"Type: {analysis_type}\n")
                
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
        """Suppress logging"""
        pass

def run_bridge(port=7778):
    """Start bridge"""
    
    print("\n" + "=" * 60)
    print("🔗 CLAUDE BRIDGE - AUTO-SUBMIT ACTIVE")
    print("=" * 60)
    print(f"\n✅ Listening on: http://0.0.0.0:{port}")
    print("✅ Auto-polling: http://localhost:7778/check")
    print("✅ Analysis auto-displays in Eba[Na]trium\n")
    
    server = HTTPServer(("0.0.0.0", port), DirectClaudeHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️ Stopped")
        server.server_close()

if __name__ == "__main__":
    run_bridge()

