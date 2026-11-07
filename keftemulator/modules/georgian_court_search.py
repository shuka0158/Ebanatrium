"""Georgian Court Records - Real court cases and legal proceedings"""
import requests
from ..core import Module

class GeorgianCourtSearch(Module):
    name = "georgian_court"
    title = "Georgian Court Records"
    category = "Georgia"
    description = "Search court cases, criminal records, legal proceedings"
    accepts = ("name", "email")

    def run(self, ent, ctx):
        query = ent.value.strip()
        ctx.log(f"Searching court records: {query}", "info")
        
        try:
            # Georgian court system public search
            resp = requests.get(
                f"https://www.court.ge/api/search",
                params={"q": query},
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0 (Keftemulator)"}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                
                if data.get('cases'):
                    ctx.log(f"✅ Found {len(data['cases'])} court cases", "info")
                    
                    for case in data['cases'][:5]:
                        case_num = case.get('case_number', 'Unknown')
                        case_type = case.get('type', 'Unknown')
                        date = case.get('date', 'Unknown')
                        
                        ctx.emit("link",
                            f"⚖️ Case {case_num} ({case_type}) - {date}",
                            case.get('url', ''),
                            {
                                "case_number": case_num,
                                "type": case_type,
                                "date": date,
                                "status": case.get('status'),
                                "court": case.get('court'),
                                "url": case.get('url'),
                                "source": "georgian_court"
                            }, rel="court_case")
        except Exception as e:
            ctx.log(f"Court search error: {str(e)[:50]}", "warn")

