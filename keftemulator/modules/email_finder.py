"""Email finder - Find emails associated with domains and people"""
import requests
import re
from ..core import Module

class EmailFinder(Module):
    name = "email_finder"
    title = "Email Finder"
    category = "People Search"
    description = "Find email addresses associated with domains, companies, and people"
    accepts = ("domain", "company", "name")

    def run(self, ent, ctx):
        query = ent.value.strip()

        ctx.log(f"searching for emails: {query}", "info")

        emails_found = set()
        sources = []

        # Hunter.io API (free tier)
        try:
            if '@' not in query and '.' in query:  # Domain
                resp = requests.get(
                    f"https://api.hunter.io/v2/domain-search?domain={query}&limit=100",
                    timeout=10
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if 'data' in data and 'emails' in data['data']:
                        for email_obj in data['data']['emails']:
                            emails_found.add(email_obj['value'])
                            sources.append(f"hunter.io: {email_obj.get('first_name', '')} {email_obj.get('last_name', '')}")
                            ctx.log(f"Found: {email_obj['value']}", "info")
        except:
            pass

        # Email-format.com API
        try:
            if '.' in query:  # Domain
                resp = requests.get(
                    f"https://api.email-format.com/v1/predict?domain={query}",
                    timeout=10
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if 'format' in data:
                        sources.append(f"email-format: {data['format']}")
                        ctx.log(f"Email format: {data['format']}", "info")
        except:
            pass

        # Search in public databases via Clearbit
        try:
            resp = requests.get(
                f"https://company.clearbit.com/v2/companies/suggest?query={query}",
                timeout=10
            )
            if resp.status_code == 200:
                companies = resp.json()
                for company in companies[:3]:
                    if 'domain' in company:
                        # Try to find emails for this company
                        try:
                            domain_resp = requests.get(
                                f"https://company.clearbit.com/v1/domains/find?name={company['name']}",
                                timeout=5
                            )
                        except:
                            pass
        except:
            pass

        # Manual regex from common patterns
        patterns = [
            f"{query.replace(' ', '.')}@*.com",
            f"contact@{query.lower()}.com",
            f"info@{query.lower()}.com",
            f"admin@{query.lower()}.com"
        ]

        result = {
            "query": query,
            "emails_found": list(emails_found),
            "sources": sources,
            "count": len(emails_found),
            "source": "email_finder"
        }

        if emails_found:
            email_list = list(emails_found)[:10]
            for email in email_list:  # Emit first 10
                ctx.emit("email_address", email, parent=ent.id, rel="associated_email")

            # SHOW ACTUAL EMAIL ADDRESSES, NOT JUST "FOUND"
            emails_display = ", ".join(email_list)
            ctx.log(f"Emails: {emails_display}", "info")
            ctx.emit("company", f"📧 FOUND {len(emails_found)} EMAIL(S): {emails_display}", query, result, rel="email_results")
        else:
            ctx.log("No emails found", "warn")
