"""Relationship graph visualization - Map entity connections"""
from ..core import Module

class RelationshipGraph(Module):
    name = "relationship_graph"
    title = "Relationship Graph"
    category = "Visualization"
    description = "Generate interactive graph showing entity relationships and connections"
    accepts = ("domain", "ip_address", "email_address", "company", "name")

    def run(self, ent, ctx):
        entity = ent.value.strip()

        ctx.log(f"generating relationship graph for: {entity}", "info")

        graph_data = {
            "entity": entity,
            "nodes": [
                {"id": entity, "label": entity, "type": "primary", "size": 50}
            ],
            "edges": [],
            "source": "relationship_graph"
        }

        # This module prepares data that will be rendered as a graph
        # The web UI will handle the visualization

        ctx.emit("company", f"🕸️ Relationship Graph", entity, {
            "nodes": 1,
            "edges": 0,
            "graph_data": graph_data,
            "visualization_type": "network"
        }, rel="graph")

        ctx.log("Graph data prepared for visualization", "info")
