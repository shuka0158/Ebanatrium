"""Georgian Viber User Intelligence - Contact & Profile Lookup"""

import re

class GeorgianViberSearch:
    name = "Georgian Viber Search"
    category = "People Search"
    accepts = ["phone_number", "username"]
    
    def investigate(self, target, ctx):
        """Search Viber profiles with Georgian numbers"""
        try:
            ctx.emit("status", f"Searching Viber: {target}")
            
            # Clean phone if provided
            if target.replace('+', '').replace('-', '').isdigit():
                phone = re.sub(r'\D', '', target)
                if not phone.startswith('995'):
                    phone = '995' + phone[-9:] if len(phone) == 9 else phone
                
                ctx.emit("link", "Viber Profile by Phone",
                        f"+{phone}",
                        {"phone": phone, "type": "viber_phone"},
                        rel="georgian_viber_phone")
            
            # Username search
            ctx.emit("link", "Viber Username Search",
                    target,
                    {"username": target, "type": "viber_username"},
                    rel="georgian_viber_username")
            
            ctx.emit("link", "Viber Group Search",
                    f"Groups with: {target}",
                    {"search": target, "type": "viber_groups"},
                    rel="georgian_viber_groups")
                    
        except Exception as e:
            ctx.emit("link", "Viber Search Error", str(e)[:100],
                    {"error": str(e)}, rel="georgian_error")


MODULE = GeorgianViberSearch()
