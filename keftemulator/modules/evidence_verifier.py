"""Evidence verifier - Mark and verify OSINT findings"""
from ..core import Module

class EvidenceVerifier(Module):
    name = "evidence_verifier"
    title = "Evidence Verifier"
    category = "Intelligence"
    description = "Verify findings, mark confidence levels, add comments, and track evidence authenticity"
    accepts = ("url", "domain", "ip_address", "email_address")

    def run(self, ent, ctx):
        entity = ent.value.strip()

        ctx.log(f"initializing evidence verification: {entity}", "info")

        evidence = {
            "entity": entity,
            "status": "unverified",
            "confidence": "unknown",
            "verified_by": [],
            "comments": [],
            "source": "evidence_verifier"
        }

        ctx.emit("company", f"✅ Evidence Status", entity, {
            "status": "unverified",
            "confidence_levels": ["High", "Medium", "Low", "Unverified"],
            "verification_status": "Pending manual verification",
            "can_confirm": True,
            "can_dispute": True,
            "evidence": evidence
        }, rel="evidence")

        ctx.log("Evidence verifier initialized", "info")
