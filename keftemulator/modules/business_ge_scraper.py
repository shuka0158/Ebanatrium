"""Business.ge scraper - Extract ACTUAL company data from Georgian business registry"""
import requests
from bs4 import BeautifulSoup
import re
from ..core import Module

class BusinessGEScraper(Module):
    name = "business_ge_scraper"
    title = "Business.ge Data Extractor"
    category = "People Search"
    description = "Scrape and extract ACTUAL company names, addresses, owner info from Business.ge"
    accepts = ("phone", "email", "company", "name")

    def run(self, ent, ctx):
        query = ent.value.strip()
        
        ctx.log(f"Scraping Business.ge for: {query}", "info")
        
        try:
            # Search Business.ge
            resp = requests.get(
                f"https://www.business.ge/en/search?q={query}",
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, 'html.parser')
                
                # Extract company listings
                companies = soup.find_all('div', class_=['company-item', 'result-item', 'search-result'])
                
                results = []
                for company in companies[:10]:
                    # Extract company name
                    name_tag = company.find(['h2', 'h3', 'a', 'strong'])
                    if name_tag:
                        company_name = name_tag.get_text(strip=True)
                        
                        # Extract address
                        address_tag = company.find(['p', 'span'], class_=['address', 'location'])
                        address = address_tag.get_text(strip=True) if address_tag else "N/A"
                        
                        # Extract phone (if available)
                        phone_match = re.search(r'\+995[\d\s]{9,}|[\d\s]{9,}', str(company))
                        phone = phone_match.group(0) if phone_match else "N/A"
                        
                        result = {
                            "company": company_name,
                            "address": address,
                            "phone": phone,
                            "source": "Business.ge"
                        }
                        
                        results.append(result)
                        ctx.log(f"Found: {company_name} at {address}", "info")
                        ctx.emit("company", f"🏢 {company_name}", company_name, result, rel="business_registered")
                
                if not results:
                    ctx.log("No results found on Business.ge", "warn")
                    
        except Exception as e:
            ctx.log(f"Business.ge scrape error: {str(e)[:50]}", "warn")

