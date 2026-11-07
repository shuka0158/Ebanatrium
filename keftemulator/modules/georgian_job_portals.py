"""Georgian Job Portal Intelligence - Professional Databases"""

import requests

class GeorgianJobPortals:
    name = "Georgian Job Portals"
    category = "People Search"
    accepts = ["name", "email_address"]
    
    def investigate(self, target, ctx):
        """Search Georgian job sites for professional info"""
        try:
            ctx.emit("status", f"Searching Georgian job portals: {target}")
            
            portals = [
                ("Brainok.ge", "https://brainok.ge", "CV database, job listings"),
                ("Jobs.ge", "https://jobs.ge", "Georgian job portal"),
                ("CV.ge", "https://cv.ge", "Professional profiles"),
                ("Recruit.ge", "https://recruit.ge", "Recruitment platform"),
            ]
            
            for name, url, desc in portals:
                ctx.emit("link", name,
                        desc,
                        {"url": url, "type": "job_portal", "search": target},
                        rel="georgian_jobs")
                        
        except Exception as e:
            ctx.emit("link", "Job Portal Error", str(e)[:100],
                    {"error": str(e)}, rel="georgian_error")


MODULE = GeorgianJobPortals()
