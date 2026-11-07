"""Google dork search - Advanced search queries to find ACTUAL data"""
import requests
from bs4 import BeautifulSoup
import urllib.parse
from ..core import Module

class GoogleDorkSearch(Module):
    name = "google_dork_search"
    title = "Google Advanced Search"
    category = "People Search"
    description = "Use Google dorks to find ACTUAL person names, documents, and info linked to phone/email"
    accepts = ("phone", "email", "domain", "name")

    def run(self, ent, ctx):
        query = ent.value.strip()
        query_encoded = urllib.parse.quote(query)
        
        ctx.log(f"Google dork search: {query}", "info")
        
        # Advanced search queries
        dorks = [
            f'"{query}" phone contact',
            f'"{query}" name address',
            f'"{query}" company OR business',
            f'"{query}" email OR contact',
            f'site:linkedin.com "{query}"',
            f'site:facebook.com "{query}"',
            f'site:business.ge "{query}"',
            f'filetype:pdf "{query}"',
            f'filetype:doc "{query}"',
            f'"{query}" registration OR documents',
        ]
        
        found_data = []
        
        for dork in dorks:
            try:
                # Search Google
                search_url = f"https://www.google.com/search?q={urllib.parse.quote(dork)}"
                
                ctx.log(f"Searching: {dork}", "info")
                
                resp = requests.get(
                    search_url,
                    timeout=10,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                        "Accept-Language": "en-US,en;q=0.9"
                    }
                )
                
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.content, 'html.parser')
                    
                    # Extract search results
                    results = soup.find_all('div', class_='g')[:3]
                    
                    for result in results:
                        title_tag = result.find('h3')
                        snippet_tag = result.find('span', class_='VwiC3b')
                        
                        if title_tag and snippet_tag:
                            title = title_tag.get_text(strip=True)
                            snippet = snippet_tag.get_text(strip=True)
                            
                            if title and snippet:
                                data = {
                                    "title": title,
                                    "snippet": snippet,
                                    "dork": dork,
                                    "source": "Google"
                                }
                                found_data.append(data)
                                ctx.emit("company", f"🔍 FOUND: {title}", query, data, rel="google_search")
                                ctx.log(f"Result: {title}", "info")
                                
            except Exception as e:
                pass  # Continue to next dork
        
        if not found_data:
            ctx.log(f"Google dork: No results found for {query}", "warn")

