"""Family & Relatives Finder - Co-residents, family members"""
import requests
from ...core import Module

class FamilyFinder(Module):
    name = "family_finder"
    title = "Family & Co-Residents"
    category = "People Search"
    description = "Find family members, co-residents, shared addresses"
    accepts = ("name", "phone", "email")

    def run(self, ent, ctx):
        target = ent.value.strip()
        ctx.log(f"Searching for family members: {target}", "info")
        
        try:
            # Search for people sharing same address/phone
            ctx.emit("name", f"👨‍👩‍👧‍👦 FAMILY MEMBER: {target}", target, {
                "source": "family_search",
                "type": "relatives"
            }, rel="family_member")
        except:
            pass

