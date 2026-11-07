"""Georgian News Archive - Historical Records & Mentions"""

import requests

class GeorgianNewsArchive:
    name = "Georgian News Archive"
    category = "Intelligence"
    accepts = ["name", "company"]
    
    def investigate(self, target, ctx):
        """Search Georgian news archives for mentions"""
        try:
            ctx.emit("status", f"Searching Georgian news archives: {target}")
            
            news_sources = [
                ("Formula.ge", "https://formula.ge", "Georgian news"),
                ("Civil.ge", "https://civil.ge", "Civil rights news"),
                ("Interpressnews.ge", "https://interpressnews.ge", "News agency"),
                ("Netgazeti.ge", "https://netgazeti.ge", "Georgian news"),
                ("Tabula.ge", "https://tabula.ge", "News portal"),
            ]
            
            for name, url, desc in news_sources:
                ctx.emit("link", name,
                        f"{desc} - Search: {target}",
                        {"url": url, "source": name, "search": target},
                        rel="georgian_news")
                        
        except Exception as e:
            ctx.emit("link", "News Archive Error", str(e)[:100],
                    {"error": str(e)}, rel="georgian_error")


MODULE = GeorgianNewsArchive()
