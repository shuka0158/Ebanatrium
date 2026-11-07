"""URL Validator - Only emit URLs that actually work"""
import requests
from ..core import Module

class URLValidator(Module):
    name = "url_validator"
    title = "URL Validator"
    category = "Threat Detection"
    description = "Validate URLs and only emit if they actually work"
    accepts = ("url", "domain")

    def run(self, ent, ctx):
        url = ent.value.strip()
        
        if not url.startswith('http'):
            url = 'https://' + url
        
        ctx.log(f"Validating URL: {url}", "info")
        
        try:
            resp = requests.head(url, timeout=5, allow_redirects=True)
            
            if resp.status_code == 200:
                ctx.log(f"✅ URL VALID (200 OK)", "info")
                ctx.emit("url", url, url, {
                    "status": 200,
                    "valid": True,
                    "headers": dict(resp.headers)
                }, rel="valid_url")
            elif resp.status_code in [301, 302, 303, 307, 308]:
                ctx.log(f"✅ URL REDIRECTS (valid)", "info")
                ctx.emit("url", url, url, {
                    "status": resp.status_code,
                    "valid": True,
                    "redirects_to": resp.url
                }, rel="valid_url")
            else:
                ctx.log(f"❌ INVALID URL (HTTP {resp.status_code})", "warn")
                
        except requests.exceptions.ConnectionError:
            ctx.log(f"❌ CANNOT REACH - Invalid URL or domain down", "warn")
        except Exception as e:
            ctx.log(f"❌ URL ERROR: {str(e)[:50]}", "warn")

