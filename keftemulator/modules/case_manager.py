"""Case manager - Group and organize OSINT investigations"""
from ..core import Module

class CaseManager(Module):
    name = "case_manager"
    title = "Case Manager"
    category = "Intelligence"
    description = "Create and manage investigation cases, group related entities, add team members"
    accepts = ("domain", "ip_address", "email_address", "company", "name", "phone")

    def run(self, ent, ctx):
        entity = ent.value.strip()

        ctx.log(f"adding to case investigation: {entity}", "info")

        case_data = {
            "entity": entity,
            "case_type": "investigation",
            "created": "now",
            "related_entities": [entity],
            "members": [],
            "tags": [],
            "source": "case_manager"
        }

        ctx.emit("company", f"📋 Investigation Case", entity, {
            "case_name": f"Case for {entity}",
            "related_count": 1,
            "members_count": 1,
            "case_data": case_data,
            "case_id": entity.replace(" ", "_").lower()
        }, rel="case")

        ctx.log("Case created for investigation", "info")
