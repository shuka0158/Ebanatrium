"""theHarvester Bridge - Direct integration of email/domain discovery"""
import sys
sys.path.insert(0, '/media/mount/OSINT_SOURCES/theHarvester')

from ..core import Module

class TheHarvesterBridge(Module):
    name = "theharvester_bridge"
    title = "theHarvester - Email & Domain Discovery"
    category = "Domain"
    description = "Email, subdomain, and hostname discovery using theHarvester"
    accepts = ("domain", "email_address")

    def run(self, ent, ctx):
        target = ent.value.strip()
        
        if "@" in target:
            domain = target.split("@")[1]
        else:
            domain = target
        
        ctx.log(f"Running theHarvester on: {domain}", "info")
        
        try:
            # Import theHarvester modules
            from theHarvester.lib import discovery
            
            # Run discovery
            all_emails = set()
            all_hosts = set()
            
            # Try multiple sources with theHarvester
            sources = ['google', 'bing', 'linkedin', 'hunter']
            
            for source in sources:
                try:
                    harvester = discovery.Discovery(domain, sources=[source], ports=None, initial_urls=None, virtual_hosts=True)
                    harvester.get_all()
                    
                    # Extract results
                    for email in harvester.emails:
                        if email and domain in email:
                            all_emails.add(email)
                            ctx.emit("email_address",
                                f"Email: {email}",
                                email,
                                {"source": "theHarvester", "harvester_source": source},
                                rel="harvester_email")
                    
                    for host in harvester.hostnames:
                        if host and domain in host:
                            all_hosts.add(host)
                            ctx.emit("domain",
                                f"Hostname: {host}",
                                f"https://{host}",
                                {"source": "theHarvester", "harvester_source": source},
                                rel="harvester_host")
                except:
                    pass
            
            ctx.log(f"✅ Found {len(all_emails)} emails, {len(all_hosts)} hosts", "info")
            
        except Exception as e:
            ctx.log(f"theHarvester error: {str(e)[:50]}", "warn")

