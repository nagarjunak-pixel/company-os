import json
import os
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional

class Agent:
    """Represents an executive AI agent in CompanyOS."""

    def __init__(self, role_id: str, name: str, emoji: str, department: str, mission: str):
        self.role_id = role_id
        self.name = name
        self.emoji = emoji
        self.department = department
        self.mission = mission
        self.status = "Idle"
        self.last_action = "Initialized"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_id": self.role_id,
            "name": self.name,
            "emoji": self.emoji,
            "department": self.department,
            "mission": self.mission,
            "status": self.status,
            "last_action": self.last_action
        }

    def think(self, task_context: Dict[str, Any], company_info: Optional[Dict[str, Any]] = None, mode: str = "AUTO") -> Dict[str, Any]:
        """Execute agent thinking cycle via LIVE mode if key is set, else SIM mode."""
        api_key = os.environ.get("OPENROUTER_API_KEY")
        
        # Decide if we attempt LIVE mode
        if (mode == "LIVE" or (mode == "AUTO" and api_key)) and api_key:
            live_res = self._think_live(task_context, company_info or {}, api_key)
            if live_res:
                self.status = "Active (LIVE)"
                self.last_action = live_res.get("action", "Executed LLM Decision")
                return live_res

        # Fallback / Default SIM Mode
        sim_res = self._think_sim(task_context, company_info or {})
        self.status = "Active (SIM)"
        self.last_action = sim_res.get("action", "Executed SIM Decision")
        return sim_res

    def _think_live(self, task_context: Dict[str, Any], company_info: Dict[str, Any], api_key: str) -> Optional[Dict[str, Any]]:
        """Call OpenRouter API using standard library urllib."""
        model = os.environ.get("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash")
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        system_prompt = (
            f"You are {self.name} ({self.role_id.upper()}), {self.mission} at {company_info.get('name', 'the company')}.\n"
            f"Provide a concise JSON output with keys: action (string), decision (string), next_steps (list of strings), notes (string)."
        )
        
        user_prompt = (
            f"Task Context:\nTitle: {task_context.get('title')}\n"
            f"Department: {task_context.get('department')}\n"
            f"Status: {task_context.get('status')}\n"
            f"Description: {task_context.get('description')}\n"
            f"Provide your strategic decision for advancing this task."
        )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 250,
            "temperature": 0.7
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                content_text = res_data["choices"][0]["message"]["content"].strip()
                
                # Attempt parsing JSON response
                try:
                    # Clean code block markers if present
                    if content_text.startswith("```"):
                        content_text = content_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                    parsed = json.loads(content_text)
                    parsed["mode"] = "LIVE"
                    parsed["agent"] = self.name
                    return parsed
                except Exception:
                    return {
                        "action": f"Evaluated {task_context.get('title', 'task')}",
                        "decision": content_text[:150],
                        "next_steps": ["Implement recommendation", "Review metrics"],
                        "notes": "Live response parsed as freeform text",
                        "mode": "LIVE",
                        "agent": self.name
                    }
        except Exception:
            # Fall back cleanly if network request fails or times out
            return None

    def _think_sim(self, task_context: Dict[str, Any], company_info: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic SIM execution handler based on role and task context."""
        title = task_context.get("title", "Strategic Initiative")
        dept = task_context.get("department", self.department)
        status = task_context.get("status", "backlog")
        c_name = company_info.get("name", "Company")
        
        # Role-specific decision patterns
        if self.role_id == "ceo":
            action = f"Approved strategy alignment for '{title}'"
            decision = f"Prioritizing {title} to drive Q3 growth targets for {c_name}."
            next_steps = ["Allocate budget resources", "Notify department leads", "Track KPI impact"]
        elif self.role_id == "coo":
            action = f"Optimized operational workflow for '{title}'"
            decision = f"Standardized process protocols and resource scheduling for {dept}."
            next_steps = ["Deploy operational checklist", "Review velocity bottlenecks"]
        elif self.role_id == "cmo":
            action = f"Launched campaign strategy for '{title}'"
            decision = f"Crafted targeted messaging and multi-channel distribution for {c_name}'s market."
            next_steps = ["A/B test ad creative", "Track conversion funnel", "Optimize channel ROI"]
        elif self.role_id == "sales":
            action = f"Structured sales pipeline for '{title}'"
            decision = f"Engaged high-value accounts and streamlined closing sequence for {c_name} products."
            next_steps = ["Schedule prospect demos", "Finalize contract terms", "Update CRM forecasts"]
        elif self.role_id == "finance":
            action = f"Audited budget allocation for '{title}'"
            decision = f"Validated cost structure and ROI projection to maintain target profit margins."
            next_steps = ["Approve purchase orders", "Reconcile quarterly ledger", "Monitor margin delta"]
        elif self.role_id == "product":
            action = f"Refined specification for '{title}'"
            decision = f"Designed user-centric features and quality standards for {c_name}'s product suite."
            next_steps = ["Conduct QA validation", "Update sprint backlog", "Prepare release notes"]
        elif self.role_id == "support":
            action = f"Enhanced customer experience workflow for '{title}'"
            decision = f"Updated support playbook and self-service articles for rapid ticket resolution."
            next_steps = ["Train support team", "Monitor CSAT feedback", "Reduce mean time to resolve"]
        else:
            action = f"Processed '{title}'"
            decision = f"Executed standard operational procedure for {dept}."
            next_steps = ["Complete assigned tasks", "Report status"]

        notes = f"[SIM Mode] Executed cleanly by {self.name} ({self.department}). Status transitioning from {status}."
        
        return {
            "action": action,
            "decision": decision,
            "next_steps": next_steps,
            "notes": notes,
            "mode": "SIM",
            "agent": self.name
        }


# Define the 7 executive agent roles
ROSTER: List[Agent] = [
    Agent(
        role_id="ceo",
        name="Elena Rostova",
        emoji="👑",
        department="Strategy",
        mission="Formulate corporate strategy, align departments, and oversee overall company growth."
    ),
    Agent(
        role_id="coo",
        name="Marcus Vance",
        emoji="⚙️",
        department="Operations",
        mission="Optimize operational workflows, supply chain efficiency, and cross-team execution."
    ),
    Agent(
        role_id="cmo",
        name="Sophia Chen",
        emoji="📢",
        department="Marketing",
        mission="Drive brand strategy, customer acquisition campaigns, and market positioning."
    ),
    Agent(
        role_id="sales",
        name="David Kim",
        emoji="💼",
        department="Sales",
        mission="Expand B2B/B2C sales pipeline, optimize deal closures, and scale revenue growth."
    ),
    Agent(
        role_id="finance",
        name="Rachel Adams",
        emoji="📊",
        department="Finance",
        mission="Manage capital allocation, track budget margins, and ensure financial compliance."
    ),
    Agent(
        role_id="product",
        name="Alex Thorne",
        emoji="🛠️",
        department="Product",
        mission="Innovate product roadmap, refine user experience, and oversee feature quality."
    ),
    Agent(
        role_id="support",
        name="Maya Patel",
        emoji="💬",
        department="Customer Support",
        mission="Elevate customer satisfaction, reduce resolution times, and maintain service SLAs."
    ),
]

AGENTS_BY_ROLE: Dict[str, Agent] = {agent.role_id: agent for agent in ROSTER}
AGENTS_BY_DEPT: Dict[str, Agent] = {agent.department.lower(): agent for agent in ROSTER}

def get_agent_by_role(role_id: str) -> Optional[Agent]:
    return AGENTS_BY_ROLE.get(role_id.lower())

def get_agent_by_dept(dept: str) -> Agent:
    return AGENTS_BY_DEPT.get(dept.lower(), ROSTER[0])
