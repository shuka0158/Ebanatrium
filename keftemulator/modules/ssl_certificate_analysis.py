"""SSL Certificate Analysis - Certificate Intelligence"""

import requests
import json

class SSLCertificateAnalysis:
    name = "SSL Certificate Analysis"
    category = "Intelligence"
    accepts = ["domain"]
    
    def investigate(self, target, ctx):
        """Analyze SSL certificates for target domain"""
        try:
            ctx.emit("status", f"Analyzing SSL certificates: {target}")
            
            # crt.sh - certificate search
            url = f"https://crt.sh/?q={target}&output=json"
            
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                try:
                    certs = resp.json()
                    ctx.emit("link", "SSL Certificates Found", f"{len(certs) if isinstance(certs, list) else 1} certificate(s)",
                            {"domain": target, "count": len(certs) if isinstance(certs, list) else 1},
                            rel="ssl_cert")
                except:
                    pass
            
            ctx.emit("link", "Certificate Search (crt.sh)",
                    "View SSL/TLS certificates issued for domain",
                    {"domain": target, "source": "crt.sh"},
                    rel="benediction_feature")
                    
        except Exception as e:
            ctx.emit("link", "Certificate Error", str(e)[:100],
                    {"error": str(e)}, rel="benediction_error")


MODULE = SSLCertificateAnalysis()
