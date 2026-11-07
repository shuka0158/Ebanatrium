"""Collaboration module - Team investigation and comments"""
from ..core import Module

class Collaboration(Module):
    name = "collaboration"
    title = "Collaboration & Comments"
    category = "Intelligence"
    description = "Add team members to investigations, leave comments, share findings, and collaborate on cases"
    accepts = ("domain", "ip_address", "email_address", "company", "name")

    def run(self, ent, ctx):
        entity = ent.value.strip()

        ctx.log(f"collaboration features available for: {entity}", "info")

        collab = {
            "entity": entity,
            "team_members": [],
            "comments": [],
            "shared_with": [],
            "source": "collaboration"
        }

        ctx.emit("company", f"👥 Team Collaboration", entity, {
            "can_add_members": True,
            "can_comment": True,
            "can_share": True,
            "current_members": 1,
            "comments_count": 0,
            "collaboration": collab,
            "features": [
                "Add team members",
                "Leave detailed comments",
                "Share findings",
                "Mention team members",
                "Track changes"
            ]
        }, rel="collab")

        ctx.log("Collaboration features enabled", "info")
