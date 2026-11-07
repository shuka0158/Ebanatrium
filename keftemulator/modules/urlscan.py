"""URLscan.io integration - Scan URLs and detect threats"""
import requests
import time
from ..core import Module

class URLscanIntegration(Module):
    name = "urlscan"
    title = "URLscan.io Scanner"
    category = "URL Intelligence"
    description = "Scan URLs with URLscan.io to detect threats, malware, phishing, and extract page data"
    accepts = ("url",)

    # URLscan API key
    API_KEY = "01a1b4e4-01e2-753b-98ce-83a4fd098eaf"
    API_URL = "https://urlscan.io/api/v1"

    def run(self, ent, ctx):
        url = ent.value.strip()

        if not url.startswith("http"):
            return

        ctx.log(f"scanning with urlscan.io: {url}", "info")

        try:
            # Submit URL for scanning
            headers = {"API-Key": self.API_KEY}
            payload = {
                "url": url,
                "visibility": "public"
            }

            resp = requests.post(
                f"{self.API_URL}/scan/",
                headers=headers,
                json=payload,
                timeout=10
            )

            if resp.status_code == 200:
                scan_data = resp.json()
                scan_uuid = scan_data.get("uuid")
                scan_url = scan_data.get("url")

                ctx.log(f"Scan submitted: {scan_uuid}", "info")

                # Wait for scan to complete
                time.sleep(5)

                # Get scan results
                result_resp = requests.get(
                    f"{self.API_URL}/result/{scan_uuid}/",
                    headers=headers,
                    timeout=15
                )

                if result_resp.status_code == 200:
                    results = result_resp.json()

                    result_data = {
                        "url": url,
                        "scan_uuid": scan_uuid,
                        "scan_url": f"https://urlscan.io/result/{scan_uuid}/",
                        "source": "urlscan"
                    }

                    # Extract threat info
                    if "stats" in results:
                        stats = results["stats"]
                        result_data["malicious"] = stats.get("malicious", 0)
                        result_data["suspicious"] = stats.get("suspicious", 0)
                        result_data["unrated"] = stats.get("unrated", 0)
                        result_data["total"] = stats.get("total", 0)

                    # Verdicts
                    if "verdicts" in results:
                        verdicts = results["verdicts"]
                        result_data["overall_verdict"] = verdicts.get("overall", {}).get("malicious", False)
                        result_data["phishing"] = verdicts.get("phishing", False)
                        result_data["malware"] = verdicts.get("malware", False)

                    # Page info
                    if "page" in results:
                        page = results["page"]
                        result_data["page_title"] = page.get("title", "Unknown")
                        result_data["page_domain"] = page.get("domain", "Unknown")
                        result_data["page_ip"] = page.get("ip", "Unknown")
                        result_data["page_asn"] = page.get("asn", "Unknown")

                    # Linked URLs
                    if "lists" in results and "urls" in results["lists"]:
                        result_data["linked_urls_count"] = len(results["lists"]["urls"])

                    # Check threat indicators
                    if result_data.get("overall_verdict"):
                        ctx.log("⚠️ MALICIOUS URL DETECTED!", "warn")
                        ctx.emit("company", f"🚨 URLscan Alert - MALICIOUS", url, result_data, rel="threat")
                    elif result_data.get("malicious", 0) > 0:
                        ctx.log(f"⚠️ Detected {result_data['malicious']} malicious indicators", "warn")
                        ctx.emit("company", f"⚠️ URLscan - Threats Detected", url, result_data, rel="threat")
                    else:
                        ctx.log("✅ URL appears clean", "info")
                        ctx.emit("company", f"✅ URLscan - Clean", url, result_data, rel="scan")

                elif result_resp.status_code == 404:
                    ctx.log("Scan still processing, check back later", "info")
                    result_data = {
                        "url": url,
                        "scan_uuid": scan_uuid,
                        "status": "processing",
                        "scan_url": f"https://urlscan.io/result/{scan_uuid}/"
                    }
                    ctx.emit("company", f"📡 URLscan - Scanning", url, result_data, rel="scan")

            elif resp.status_code == 429:
                ctx.log("URLscan rate limit exceeded", "warn")

            else:
                ctx.log(f"URLscan error: {resp.status_code}", "warn")

        except Exception as e:
            ctx.log(f"urlscan error: {str(e)[:50]}", "warn")
