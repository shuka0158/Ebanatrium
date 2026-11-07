"""Public Records Deep Search - Free sources for addresses, names, family"""
import requests
import re
from ..core import Module

class PublicRecordsDeep(Module):
    name = "public_records_deep"
    title = "Public Records Deep Search"
    category = "Intelligence"
    description = "Search public records: addresses, family, legal names from free sources"
    accepts = ("name", "email_address", "phone")

    def run(self, ent, ctx):
        query = ent.value.strip()
        ctx.log(f"Deep public records search: {query}", "info")
        
        # Search multiple FREE public record sources
        sources = [
            ("FamilySearch", f"https://www.familysearch.org/search?query={query}"),
            ("Archive.org Person", f"https://archive.org/advancedsearch.php?q={query}"),
            ("PublicRecords.com", f"https://www.publicrecords.com/search?q={query}"),
            ("Ancestry (Free)", f"https://www.ancestry.com/search/collections/public/"),
            ("Vital Records", f"https://www.vitalchecker.com/{query}"),
            ("Court Records", f"https://www.courtlistener.com/search/?q={query}"),
        ]
        
        for source, url in sources:
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    ctx.emit("link",
                        f"Public Record: {source}",
                        url,
                        {"source": source, "type": "public_record"},
                        rel="public_record")
                    ctx.log(f"✅ {source} - accessible", "info")
            except:
                pass

