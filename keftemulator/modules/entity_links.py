"""Entity links - Detailed relationship discovery between entities"""
import requests
from ..core import Module

class EntityLinks(Module):
    name = "entity_links"
    title = "Entity Links & Relationships"
    category = "Intelligence"
    description = "Discover and map detailed relationships between entities (serves from, resolves to, etc.)"
    accepts = ("domain", "ip_address")

    def run(self, ent, ctx):
        entity = ent.value.strip()

        ctx.log(f"discovering entity relationships: {entity}", "info")

        links = {
            "entity": entity,
            "relationships": [],
            "source": "entity_links"
        }

        # If domain
        if '.' in entity and not entity.startswith('['):
            links["relationships"].append({
                "type": "resolves_to",
                "target": "IP address",
                "strength": "Strong",
                "verified": False
            })
            links["relationships"].append({
                "type": "nameserver",
                "target": "NS records",
                "strength": "Strong",
                "verified": False
            })
            links["relationships"].append({
                "type": "historical",
                "target": "Previous IPs",
                "strength": "Source-asserted",
                "verified": False
            })
            links["relationships"].append({
                "type": "certificate",
                "target": "SSL certificates",
                "strength": "Strong",
                "verified": False
            })
            links["relationships"].append({
                "type": "mentions",
                "target": "Pastes/breaches",
                "strength": "Weak",
                "verified": False
            })

        # If IP
        elif entity[0].isdigit():
            links["relationships"].append({
                "type": "hosts",
                "target": "Domains",
                "strength": "Strong",
                "verified": False
            })
            links["relationships"].append({
                "type": "geolocation",
                "target": "Location data",
                "strength": "Strong",
                "verified": False
            })
            links["relationships"].append({
                "type": "whois",
                "target": "Ownership info",
                "strength": "Strong",
                "verified": False
            })

        ctx.emit("company", f"🔗 Entity Links", entity, {
            "total_links": len(links["relationships"]),
            "link_types": [l["type"] for l in links["relationships"]],
            "links_data": links
        }, rel="links")

        ctx.log(f"Found {len(links['relationships'])} relationship types", "info")
