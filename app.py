import os
from flask import Flask, jsonify, render_template, request
from company_os.config import load_company_config, save_company_config
from company_os.store import Store
from company_os.agents import ROSTER, get_agent_by_role
from company_os.engine import generate_plan, assign_loop, advance_board, compute_kpis
from company_os.shacl_procedure_merge import (
    PropertyShape,
    distill_procedure_memory,
    shacl_three_way_merge,
)

app = Flask(__name__, static_folder="static", template_folder="templates")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
store = Store(DATA_DIR)

def ensure_initialized():
    """Ensure company config, plan, board, and KPIs exist on launch."""
    config = load_company_config("company.json")
    plan = store.load_json("plan.json")
    if not plan:
        generate_plan(config, DATA_DIR)
        assign_loop(DATA_DIR)

ensure_initialized()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/company", methods=["GET"])
def get_company():
    config = load_company_config("company.json")
    mode = "LIVE" if os.environ.get("OPENROUTER_API_KEY") else "SIM"
    config["execution_mode"] = mode
    return jsonify(config)

@app.route("/api/plan", methods=["GET"])
def get_plan():
    plan = store.load_json("plan.json")
    if not plan:
        config = load_company_config("company.json")
        plan = generate_plan(config, DATA_DIR)
    return jsonify(plan)

@app.route("/api/board", methods=["GET"])
def get_board():
    board = store.load_json("board.json", {"tasks": []})
    tasks = board.get("tasks", [])
    grouped = {
        "backlog": [t for t in tasks if t.get("status") == "backlog"],
        "todo": [t for t in tasks if t.get("status") == "todo"],
        "doing": [t for t in tasks if t.get("status") == "doing"],
        "done": [t for t in tasks if t.get("status") == "done"]
    }
    return jsonify({
        "grouped": grouped,
        "tasks": tasks,
        "total": len(tasks),
        "last_updated": board.get("last_updated")
    })

@app.route("/api/agents", methods=["GET"])
def get_agents():
    mode = "LIVE" if os.environ.get("OPENROUTER_API_KEY") else "SIM"
    roster_data = []
    for agent in ROSTER:
        ag_dict = agent.to_dict()
        ag_dict["mode"] = mode
        roster_data.append(ag_dict)
    return jsonify({"agents": roster_data})

@app.route("/api/kpis", methods=["GET"])
def get_kpis():
    kpi_data = store.load_json("kpis.json")
    if not kpi_data:
        board = store.load_json("board.json", {"tasks": []})
        kpi_data = compute_kpis(board.get("tasks", []), [])
        store.save_json("kpis.json", kpi_data)
    return jsonify(kpi_data)

@app.route("/api/events", methods=["GET"])
def get_events():
    try:
        after_id = int(request.args.get("after", 0))
    except (ValueError, TypeError):
        after_id = 0
    events = store.get_events(after_id=after_id)
    return jsonify({"events": events, "count": len(events)})

@app.route("/api/rebuild", methods=["POST"])
def rebuild_plan():
    payload = request.get_json(silent=True) or {}
    config = load_company_config("company.json")
    if payload:
        config.update(payload)
        save_company_config(config, "company.json")
    
    new_plan = generate_plan(config, DATA_DIR)
    assign_result = assign_loop(DATA_DIR)
    
    board = store.load_json("board.json")
    kpis = store.load_json("kpis.json")
    
    return jsonify({
        "status": "success",
        "company": config,
        "plan": new_plan,
        "assigned": assign_result,
        "kpis": kpis.get("current")
    })

@app.route("/api/advance", methods=["POST"])
def advance_tasks():
    payload = request.get_json(silent=True) or {}
    steps = payload.get("steps", 2)
    try:
        steps = int(steps)
    except (ValueError, TypeError):
        steps = 2
    
    result = advance_board(DATA_DIR, steps=steps)
    return jsonify({
        "status": "success",
        "steps_requested": steps,
        "result": result
    })

@app.route("/api/agent/<name>/message", methods=["POST"])
def agent_message(name):
    target_agent = None
    name_clean = name.lower()
    for ag in ROSTER:
        if ag.name.lower() == name_clean or ag.role_id.lower() == name_clean or ag.department.lower() == name_clean:
            target_agent = ag
            break

    if not target_agent:
        return jsonify({"error": f"Agent '{name}' not found"}), 404

    payload = request.get_json(silent=True) or {}
    task_context = payload.get("task", {
        "title": payload.get("message", "Custom Prompt"),
        "department": target_agent.department,
        "status": "doing",
        "description": payload.get("message", "Custom Prompt")
    })
    company_info = store.load_json("plan.json", {})

    response = target_agent.think(task_context, company_info)
    store.append_event(
        event_type="AGENT_MESSAGE",
        details={
            "agent": target_agent.name,
            "message": payload.get("message"),
            "action": response.get("action")
        },
        agent=target_agent.name
    )
    return jsonify({
        "agent": target_agent.to_dict(),
        "response": response
    })


@app.route("/api/merge-graph", methods=["POST"])
def api_merge_graph():
    payload = request.get_json(silent=True) or {}
    base = [tuple(t) for t in payload.get("base", []) if len(t) == 3]
    left = [tuple(t) for t in payload.get("left", []) if len(t) == 3]
    right = [tuple(t) for t in payload.get("right", []) if len(t) == 3]
    raw_shapes = payload.get("shapes", {})
    shapes = {
        pred: PropertyShape(
            predicate=pred,
            max_count=spec.get("max_count"),
            min_count=int(spec.get("min_count", 0)),
        )
        for pred, spec in raw_shapes.items()
    }
    aliases = {str(k): str(v) for k, v in payload.get("entity_aliases", {}).items()}
    res = shacl_three_way_merge(base, left, right, shapes=shapes, entity_aliases=aliases)
    return jsonify({
        "merged_triples": [list(t) for t in res.merged_triples],
        "conflicts": [
            {
                "subject": c.subject,
                "predicate": c.predicate,
                "reason": c.reason,
            }
            for c in res.conflicts
        ],
        "naive_diff_prompts": res.naive_diff_prompts,
        "shacl_conflict_prompts": res.shacl_conflict_prompts,
    })


@app.route("/api/procedures/distill", methods=["POST"])
def api_distill_procedure():
    payload = request.get_json(silent=True) or {}
    proc_id = str(payload.get("procedure_id", "ops-runbook")).strip()
    events = payload.get("events", [])
    try:
        res = distill_procedure_memory(proc_id, events)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({
        "procedure_id": res.procedure_id,
        "step_count": len(res.steps),
        "raw_token_count": res.raw_token_count,
        "distilled_token_count": res.distilled_token_count,
        "token_reduction_ratio": res.token_reduction_ratio,
        "formatted_prompt_block": res.formatted_prompt_block,
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
