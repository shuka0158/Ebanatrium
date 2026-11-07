"""Georgian Phone Number Intelligence - Carrier & Viber Lookup"""

import re

class GeorgianPhoneLookup:
    name = "Georgian Phone Lookup"
    category = "People Search"
    accepts = ["phone_number"]
    
    def investigate(self, target, ctx):
        """Analyze Georgian phone numbers"""
        try:
            # Clean phone number
            phone = re.sub(r'\D', '', target)
            
            if not phone.startswith('995'):
                phone = '995' + phone if len(phone) == 9 else phone
            
            ctx.emit("status", f"Analyzing Georgian phone: {phone}")
            
            # Georgian mobile carriers
            carriers = {
                '555': 'Beeline Georgia',
                '599': 'Beeline Georgia',
                '577': 'Caucasus Online',
                '593': 'Silknet',
                '595': 'Magti Communications',
                '591': 'Beeline Georgia',
                '596': 'Caucasus Online',
                '598': 'Caucasus Online',
            }
            
            prefix = phone[4:7] if len(phone) >= 7 else None
            
            if prefix and prefix in carriers:
                carrier = carriers[prefix]
                ctx.emit("link", "Carrier Identification", carrier,
                        {"phone": phone, "carrier": carrier, "prefix": prefix},
                        rel="georgian_carrier")
            
            # Viber lookup
            ctx.emit("link", "Viber Profile Lookup",
                    f"Search Viber: +{phone}",
                    {"phone": phone, "type": "viber"},
                    rel="georgian_viber")
            
            # Reverse lookup services
            ctx.emit("link", "Georgian Reverse Lookup",
                    f"Phone: +{phone}",
                    {"phone": phone, "type": "reverse_lookup"},
                    rel="georgian_phone")
                    
        except Exception as e:
            ctx.emit("link", "Phone Lookup Error", str(e)[:100],
                    {"error": str(e)}, rel="georgian_error")


MODULE = GeorgianPhoneLookup()
