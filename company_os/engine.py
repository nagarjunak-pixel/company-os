import time
from typing import Dict, List, Any, Optional
from company_os.store import Store
from company_os.agents import ROSTER, AGENTS_BY_ROLE, get_agent_by_role, get_agent_by_dept

def generate_plan(company_config: Dict[str, Any], data_dir: str = "data") -> Dict[str, Any]:
    """Generate company mission, values, quarterly goals, and backlog tasks."""
    store = Store(data_dir)
    name = company_config.get("name", "Aurora Coffee Co.")
    industry = company_config.get("industry", "Specialty Coffee")
    products = company_config.get("products", ["Core Offerings"])
    target_market = company_config.get("target_market", "Global Customers")

    mission = f"To pioneer excellence in {industry} by delivering top-tier products ({', '.join(products[:2])}) tailored for {target_market}."
    
    values = [
        "Customer Obsession",
        "Operational Precision",
        "Sustainable Growth",
        "Innovative Product Engineering",
        "Transparent Governance"
    ]

    departments = [
        {"name": "Strategy", "lead": "Elena Rostova (CEO)", "focus": "Executive Strategy & Corporate Expansion"},
        {"name": "Operations", "lead": "Marcus Vance (COO)", "focus": "Supply Chain, Logistics & Internal Workflows"},
        {"name": "Marketing", "lead": "Sophia Chen (CMO)", "focus": "Brand Awareness & Multi-Channel Acquisition"},
        {"name": "Sales", "lead": "David Kim (Head of Sales)", "focus": "Enterprise Accounts & Revenue Generation"},
        {"name": "Finance", "lead": "Rachel Adams (Head of Finance)", "focus": "Capital Allocation, Margins & Cash Flow"},
        {"name": "Product", "lead": "Alex Thorne (Head of Product)", "focus": "R&D, UX Design & Feature Quality"},
        {"name": "Customer Support", "lead": "Maya Patel (Head of Support)", "focus": "Customer Retention, CSAT & SLA Metrics"}
    ]

    goals = [
        {"quarter": "Q3", "department": "Strategy", "objective": f"Expand market share in {industry} by 25%"},
        {"quarter": "Q3", "department": "Operations", "objective": "Reduce fulfillment cycle time by 30%"},
        {"quarter": "Q3", "department": "Marketing", "objective": f"Increase qualified lead volume for {products[0]}"},
        {"quarter": "Q3", "department": "Sales", "objective": "Scale ARR by 35% through B2B partnership deals"},
        {"quarter": "Q3", "department": "Finance", "objective": "Maintain gross profit margin above 60%"},
        {"quarter": "Q3", "department": "Product", "objective": f"Ship v2.0 features for {', '.join(products[:2])}"},
        {"quarter": "Q3", "department": "Customer Support", "objective": "Achieve 98%+ customer satisfaction score"}
    ]

    # Generate 16 realistic backlog tasks
    raw_tasks = [
        ("Formulate 3-Year Strategic Vision & Expansion Roadmap", "Strategy", "ceo", "High", "Large", f"Define corporate milestones and capital deployment strategy for {name}."),
        ("Optimize Supply Chain & Supplier Vendor SLA Contracts", "Operations", "coo", "High", "Medium", f"Renegotiate vendor terms to improve margins on {products[0]}."),
        ("Launch Multi-Channel Acquisition Campaign", "Marketing", "cmo", "High", "Medium", f"Target {target_market} across digital and partner channels."),
        ("Establish B2B Enterprise Prospecting Pipeline", "Sales", "sales", "High", "Large", "Build outbound sales cadence for high-volume accounts."),
        ("Conduct Quarterly Financial Audit & Margin Analysis", "Finance", "finance", "High", "Medium", "Review P&L statements and optimize operational expenditures."),
        ("Upgrade Core Product UX Feature Set", "Product", "product", "High", "Large", f"Enhance customer portal and order experience for {name}."),
        ("Implement Automated Customer Support SLA Escalations", "Support", "support", "Medium", "Small", "Reduce ticket response latency and establish VIP queues."),
        ("Establish International Expansion Strategy", "Strategy", "ceo", "Medium", "Large", "Evaluate regulatory and logistics readiness for overseas markets."),
        ("Streamline Inventory & Warehouse Logistics", "Operations", "coo", "High", "Medium", "Implement real-time inventory tracking software."),
        ("Execute Re-branding & Influencer Partnership Drive", "Marketing", "cmo", "Medium", "Medium", "Partner with industry leaders to boost brand domain authority."),
        ("Structure Tiered Pricing & Sales Commission Plan", "Sales", "sales", "High", "Medium", "Align sales compensation with high-margin product tier sales."),
        ("Optimize Working Capital & Cash Flow Forecasting", "Finance", "finance", "Medium", "Small", "Build dynamic 12-month rolling cash flow model."),
        ("Build Next-Gen Product Subscription Features", "Product", "product", "High", "Medium", "Add recurring order customization and automated billing."),
        ("Develop Customer Onboarding Knowledge Base", "Support", "support", "Low", "Small", "Create interactive FAQ and self-service video walkthroughs."),
        ("Initiate Strategic M&A and Partner Scouting", "Strategy", "ceo", "Low", "Large", "Identify complementary market players for synergistic partnerships."),
        ("Standardize Cross-Departmental Operational Playbook", "Operations", "coo", "Medium", "Small", "Publish company-wide SOP directory and onboarding guides.")
    ]

    backlog = []
    for idx, (title, dept, role_id, priority, effort, desc) in enumerate(raw_tasks, start=101):
        agent = get_agent_by_role(role_id)
        task = {
            "id": f"TSK-{idx}",
            "title": title,
            "department": dept,
            "owner_role": role_id,
            "owner_agent": agent.name if agent else "Unassigned",
            "priority": priority,
            "effort": effort,
            "status": "backlog",
            "description": desc,
            "log": [f"Task created in backlog for {dept}."]
        }
        backlog.append(task)

    plan_data = {
        "company": name,
        "mission": mission,
        "values": values,
        "departments": departments,
        "goals": goals,
        "task_count": len(backlog)
    }

    board_data = {
        "tasks": backlog,
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    store.save_json("plan.json", plan_data)
    store.save_json("board.json", board_data)

    # Initialize KPIs
    initial_kpis = compute_kpis(backlog, [])
    store.save_json("kpis.json", initial_kpis)

    # Log Event
    store.append_event(
        event_type="PLAN_GENERATED",
        details={
            "mission": mission,
            "task_count": len(backlog),
            "company": name
        },
        agent="Elena Rostova (CEO)"
    )

    return plan_data


def assign_loop(data_dir: str = "data") -> Dict[str, Any]:
    """Assign backlog tasks to agents and transition them to 'todo' status."""
    store = Store(data_dir)
    board = store.load_json("board.json", {"tasks": []})
    tasks = board.get("tasks", [])
    
    company_info = store.load_json("plan.json", {})

    assigned_count = 0
    for task in tasks:
        if task.get("status") == "backlog":
            task["status"] = "todo"
            role_id = task.get("owner_role", "ceo")
            agent = get_agent_by_role(role_id) or ROSTER[0]
            
            # Execute agent thinking cycle
            think_result = agent.think(task, company_info)
            action_msg = think_result.get("action", "Assigned task to todo queue")
            
            task.setdefault("log", []).append(f"Assigned to {agent.name}: {action_msg}")
            assigned_count += 1

            store.append_event(
                event_type="TASK_ASSIGNED",
                details={
                    "task_id": task.get("id"),
                    "title": task.get("title"),
                    "owner": agent.name,
                    "department": task.get("department")
                },
                agent=agent.name
            )

    board["tasks"] = tasks
    board["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    store.save_json("board.json", board)

    # Update KPIs
    kpi_data = store.load_json("kpis.json", {"current": {}, "history": []})
    updated_kpis = compute_kpis(tasks, kpi_data.get("history", []))
    store.save_json("kpis.json", updated_kpis)

    return {
        "assigned_count": assigned_count,
        "total_tasks": len(tasks)
    }


def advance_board(data_dir: str = "data", steps: int = 2) -> Dict[str, Any]:
    """Advance tasks across Kanban columns (todo -> doing -> done) and update KPIs."""
    store = Store(data_dir)
    board = store.load_json("board.json", {"tasks": []})
    tasks = board.get("tasks", [])
    company_info = store.load_json("plan.json", {})

    advanced = []
    remaining_steps = steps

    # 1. Advance 'doing' -> 'done' first
    for task in tasks:
        if remaining_steps <= 0:
            break
        if task.get("status") == "doing":
            task["status"] = "done"
            role_id = task.get("owner_role", "ceo")
            agent = get_agent_by_role(role_id) or ROSTER[0]
            
            think_res = agent.think(task, company_info)
            decision = think_res.get("decision", "Completed task execution successfully.")
            
            task.setdefault("log", []).append(f"Completed by {agent.name}: {decision}")
            advanced.append({"task_id": task["id"], "title": task["title"], "new_status": "done", "agent": agent.name})
            
            store.append_event(
                event_type="TASK_COMPLETED",
                details={
                    "task_id": task["id"],
                    "title": task["title"],
                    "owner": agent.name,
                    "decision": decision
                },
                agent=agent.name
            )
            remaining_steps -= 1

    # 2. Advance 'todo' -> 'doing'
    for task in tasks:
        if remaining_steps <= 0:
            break
        if task.get("status") == "todo":
            task["status"] = "doing"
            role_id = task.get("owner_role", "ceo")
            agent = get_agent_by_role(role_id) or ROSTER[0]

            think_res = agent.think(task, company_info)
            action = think_res.get("action", "Started task execution")

            task.setdefault("log", []).append(f"In Progress ({agent.name}): {action}")
            advanced.append({"task_id": task["id"], "title": task["title"], "new_status": "doing", "agent": agent.name})

            store.append_event(
                event_type="TASK_ADVANCED",
                details={
                    "task_id": task["id"],
                    "title": task["title"],
                    "owner": agent.name,
                    "new_status": "doing",
                    "action": action
                },
                agent=agent.name
            )
            remaining_steps -= 1

    # 3. Advance 'backlog' -> 'todo' if steps still remaining
    for task in tasks:
        if remaining_steps <= 0:
            break
        if task.get("status") == "backlog":
            task["status"] = "todo"
            role_id = task.get("owner_role", "ceo")
            agent = get_agent_by_role(role_id) or ROSTER[0]

            think_res = agent.think(task, company_info)
            action = think_res.get("action", "Moved to todo queue")

            task.setdefault("log", []).append(f"Assigned to todo ({agent.name}): {action}")
            advanced.append({"task_id": task["id"], "title": task["title"], "new_status": "todo", "agent": agent.name})

            store.append_event(
                event_type="TASK_ADVANCED",
                details={
                    "task_id": task["id"],
                    "title": task["title"],
                    "owner": agent.name,
                    "new_status": "todo"
                },
                agent=agent.name
            )
            remaining_steps -= 1

    board["tasks"] = tasks
    board["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    store.save_json("board.json", board)

    # Re-compute and update KPIs
    kpi_store = store.load_json("kpis.json", {"current": {}, "history": []})
    new_kpis = compute_kpis(tasks, kpi_store.get("history", []))
    store.save_json("kpis.json", new_kpis)

    return {
        "advanced_count": len(advanced),
        "advanced_tasks": advanced,
        "kpis": new_kpis["current"]
    }


def compute_kpis(tasks: List[Dict[str, Any]], history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate current KPIs from task board state and update history."""
    base_revenue = 75000.0
    base_expenses = 35000.0

    completed_revenue = 0.0
    completed_expenses = 0.0
    pipeline_val = 0.0
    completed_prod_supp = 0

    effort_multiplier = {
        "Small": (6000.0, 2500.0),
        "Medium": (18000.0, 7000.0),
        "Large": (45000.0, 16000.0)
    }

    for task in tasks:
        status = task.get("status")
        effort = task.get("effort", "Medium")
        rev_val, exp_val = effort_multiplier.get(effort, (18000.0, 7000.0))

        if status == "done":
            completed_revenue += rev_val
            completed_expenses += exp_val
            if task.get("department") in ["Product", "Customer Support", "Support"]:
                completed_prod_supp += 1
        elif status in ["todo", "doing"]:
            pipeline_val += rev_val

    total_revenue = base_revenue + completed_revenue
    total_expenses = base_expenses + completed_expenses
    profit = total_revenue - total_expenses
    margin = (profit / total_revenue * 100.0) if total_revenue > 0 else 0.0
    csat = min(99.0, 82.5 + (completed_prod_supp * 2.8))

    current = {
        "revenue": round(total_revenue, 2),
        "expenses": round(total_expenses, 2),
        "profit": round(profit, 2),
        "margin": round(margin, 1),
        "pipeline_value": round(pipeline_val, 2),
        "csat": round(csat, 1),
        "done_tasks": sum(1 for t in tasks if t.get("status") == "done"),
        "total_tasks": len(tasks)
    }

    new_history = list(history)
    new_history.append({
        "tick": len(new_history) + 1,
        "timestamp": time.strftime("%H:%M:%S"),
        "revenue": current["revenue"],
        "expenses": current["expenses"],
        "profit": current["profit"],
        "margin": current["margin"],
        "pipeline_value": current["pipeline_value"],
        "csat": current["csat"]
    })

    return {
        "current": current,
        "history": new_history
    }
