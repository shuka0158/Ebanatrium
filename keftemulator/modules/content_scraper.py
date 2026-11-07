"""Content Scraper - Extract ACTUAL data from pages"""
import requests
from bs4 import BeautifulSoup
import re
from ..core import Module

class ContentScraper(Module):
    name = "content_scraper"
    title = "Real Content Extractor"
    category = "Threat Detection"
    description = "Scrape and extract ACTUAL content from valid URLs"
    accepts = ("url", "domain")

    def run(self, ent, ctx):
        url = ent.value.strip()
        
        if not url.startswith('http'):
            return
        
        ctx.log(f"Scraping content: {url}", "info")
        
        try:
            resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            
            if resp.status_code != 200:
                ctx.log(f"Cannot fetch (HTTP {resp.status_code})", "warn")
                return
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Extract ACTUAL data
            title = soup.find('title')
            meta_desc = soup.find('meta', {'name': 'description'})
            
            # Find phone numbers
            phones = re.findall(r'\+?[\d\s\-\(\)]{10,}', resp.text)
            
            # Find emails
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', resp.text)
            
            # Find names (basic)
            text = soup.get_text()
            
            found_data = {
                "title": title.get_text() if title else None,
                "description": meta_desc.get('content') if meta_desc else None,
                "phones": list(set(phones)) if phones else None,
                "emails": list(set(emails)) if emails else None,
                "url": url
            }
            
            # Only emit if we actually found something
            if any([phones, emails, title]):
                ctx.log(f"✅ FOUND REAL DATA", "info")
                ctx.emit("company", f"📄 PAGE DATA: {found_data.get('title', 'Unknown')}", url, found_data, rel="page_data")
                
                # Emit individual findings
                for phone in phones[:5]:
                    ctx.log(f"Phone found: {phone}", "info")
                    ctx.emit("phone", phone, phone, {"source": url}, rel="found_on_page")
                
                for email in emails[:5]:
                    ctx.log(f"Email found: {email}", "info")
                    ctx.emit("email_address", email, email, {"source": url}, rel="found_on_page")
            else:
                ctx.log(f"No useful data found on page", "warn")
                
        except Exception as e:
            ctx.log(f"Scrape error: {str(e)[:50]}", "warn")

