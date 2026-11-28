import os
import pytest
from company_os.config import load_company_config, save_company_config, DEFAULT_COMPANY
from company_os.store import Store
from company_os.agents import ROSTER, get_agent_by_role
from company_os.engine import generate_plan, assign_loop, advance_board, compute_kpis
from app import app

@pytest.fixture
def temp_data_dir(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    return str(d)

def test_generate_plan(temp_data_dir):
    """GeneratePlan returns a non-empty backlog with valid tasks."""
    plan = generate_plan(DEFAULT_COMPANY, temp_data_dir)
    assert plan["company"] == DEFAULT_COMPANY["name"]
    assert len(plan["values"]) > 0
    assert len(plan["departments"]) == 7

    store = Store(temp_data_dir)
    board = store.load_json("board.json")
    tasks = board.get("tasks", [])
    
    assert len(tasks) >= 12
    for task in tasks:
        assert "id" in task
        assert "title" in task
        assert "department" in task
        assert "owner_role" in task
        assert "owner_agent" in task
        assert task["status"] == "backlog"
        assert task["priority"] in ["High", "Medium", "Low"]
        assert task["effort"] in ["Small", "Medium", "Large"]


def test_assign_loop(temp_data_dir):
    """AssignLoop moves backlog tasks to todo."""
    generate_plan(DEFAULT_COMPANY, temp_data_dir)
    res = assign_loop(temp_data_dir)
    assert res["assigned_count"] >= 12

    store = Store(temp_data_dir)
    board = store.load_json("board.json")
    for task in board.get("tasks", []):
        assert task["status"] == "todo"


def test_advance_board(temp_data_dir):
    """AdvanceBoard moves tasks through statuses and stops at done."""
    generate_plan(DEFAULT_COMPANY, temp_data_dir)
    assign_loop(temp_data_dir)

    # Step 1: Advance 4 tasks from todo -> doing
    res1 = advance_board(temp_data_dir, steps=4)
    assert res1["advanced_count"] == 4
    for item in res1["advanced_tasks"]:
        assert item["new_status"] == "doing"

    # Step 2: Advance again, tasks in doing move to done
    res2 = advance_board(temp_data_dir, steps=4)
    assert res2["advanced_count"] == 4
    statuses = [t["new_status"] for t in res2["advanced_tasks"]]
    assert "done" in statuses or "doing" in statuses


def test_kpis_change_and_history_grows(temp_data_dir):
    """KPIs change after advancing and history grows."""
    generate_plan(DEFAULT_COMPANY, temp_data_dir)
    store = Store(temp_data_dir)
    
    initial_kpi = store.load_json("kpis.json")
    initial_hist_len = len(initial_kpi.get("history", []))
    initial_rev = initial_kpi["current"]["revenue"]

    assign_loop(temp_data_dir)
    advance_board(temp_data_dir, steps=4)
    advance_board(temp_data_dir, steps=4)

    updated_kpi = store.load_json("kpis.json")
    new_hist_len = len(updated_kpi.get("history", []))
    new_rev = updated_kpi["current"]["revenue"]

    assert new_hist_len > initial_hist_len
    assert new_rev >= initial_rev


def test_events_appended_and_idempotent(temp_data_dir):
    """Events are appended and each advance appends expected new events."""
    generate_plan(DEFAULT_COMPANY, temp_data_dir)
    store = Store(temp_data_dir)
    
    events_1 = store.get_events(after_id=0)
    count_1 = len(events_1)
    assert count_1 >= 1  # PLAN_GENERATED event

    assign_loop(temp_data_dir)
    events_2 = store.get_events(after_id=0)
    count_2 = len(events_2)
    assert count_2 > count_1

    advance_board(temp_data_dir, steps=2)
    events_3 = store.get_events(after_id=0)
    count_3 = len(events_3)
    assert count_3 == count_2 + 2

    # Test query after_id filtering
    last_id = events_3[-1]["id"]
    new_events = store.get_events(after_id=last_id)
    assert len(new_events) == 0


def test_live_mode_fallback_without_api_key(monkeypatch, temp_data_dir):
    """With no OPENROUTER_API_KEY, agent think() returns a SIM result cleanly."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    
    agent = get_agent_by_role("ceo")
    task_context = {
        "title": "Test Fallback Strategy",
        "department": "Strategy",
        "status": "todo",
        "description": "Verify fallback behavior"
    }

    # Test AUTO mode (defaults to SIM when key missing)
    res_auto = agent.think(task_context, {"name": "Test Co"}, mode="AUTO")
    assert res_auto["mode"] == "SIM"
    assert "action" in res_auto
    assert "decision" in res_auto

    # Test explicit LIVE mode (should cleanly fall back to SIM without exception)
    res_live = agent.think(task_context, {"name": "Test Co"}, mode="LIVE")
    assert res_live["mode"] == "SIM"
    assert "action" in res_live


def test_flask_api_routes():
    """Test Flask HTTP API endpoints."""
    client = app.test_client()

    res_company = client.get("/api/company")
    assert res_company.status_code == 200
    assert "name" in res_company.get_json()

    res_plan = client.get("/api/plan")
    assert res_plan.status_code == 200
    assert "mission" in res_plan.get_json()

    res_board = client.get("/api/board")
    assert res_board.status_code == 200
    assert "grouped" in res_board.get_json()

    res_agents = client.get("/api/agents")
    assert res_agents.status_code == 200
    assert len(res_agents.get_json()["agents"]) == 7

    res_kpis = client.get("/api/kpis")
    assert res_kpis.status_code == 200
    assert "current" in res_kpis.get_json()

    res_events = client.get("/api/events")
    assert res_events.status_code == 200
    assert "events" in res_events.get_json()

    res_advance = client.post("/api/advance", json={"steps": 2})
    assert res_advance.status_code == 200
    assert res_advance.get_json()["status"] == "success"

    res_msg = client.post("/api/agent/ceo/message", json={"message": "Analyze market competitors"})
    assert res_msg.status_code == 200
    assert "response" in res_msg.get_json()


def test_shacl_three_way_merge_and_alias_canonicalization():
    """SHACL 3-way merge auto-merges set predicates and flags only true cardinality conflicts."""
    from company_os.shacl_procedure_merge import PropertyShape, shacl_three_way_merge

    shapes = {
        "hasOwner": PropertyShape(predicate="hasOwner", max_count=1, min_count=1),
        "hasTag": PropertyShape(predicate="hasTag", max_count=None, min_count=0),
    }
    aliases = {"proj:alpha_v1": "proj:alpha", "user:alice_lead": "user:alice"}

    base = [
        ("proj:alpha", "hasOwner", "user:bob"),
        ("proj:alpha", "hasTag", "core"),
        ("proj:beta", "hasOwner", "user:carol"),
    ]
    # Left adds 10 non-conflicting tags + changes proj:beta owner to alice (via alias)
    left = [
        ("proj:alpha_v1", "hasOwner", "user:bob"),
        ("proj:alpha", "hasTag", "core"),
        *[(f"proj:alpha", "hasTag", f"tag_l_{i}") for i in range(10)],
        ("proj:beta", "hasOwner", "user:alice_lead"),
    ]
    # Right adds 10 distinct tags + changes proj:beta owner to dave -> 1 true SHACL conflict vs 22 naive diffs!
    right = [
        ("proj:alpha", "hasOwner", "user:bob"),
        ("proj:alpha", "hasTag", "core"),
        *[(f"proj:alpha", "hasTag", f"tag_r_{i}") for i in range(10)],
        ("proj:beta", "hasOwner", "user:dave"),
    ]

    res = shacl_three_way_merge(base, left, right, shapes=shapes, entity_aliases=aliases)
    assert res.naive_diff_prompts == 22
    assert res.shacl_conflict_prompts == 1
    assert res.conflicts[0].subject == "proj:beta"
    assert res.conflicts[0].reason == "shacl_max_count_exceeded:1"
    assert ("proj:alpha", "hasTag", "tag_l_0") in res.merged_triples
    assert ("proj:alpha", "hasTag", "tag_r_9") in res.merged_triples

    # Single-branch functional update (only right modifies hasOwner) merges cleanly without conflict
    clean_one_side = shacl_three_way_merge(
        base=[("proj:gamma", "hasOwner", "user:bob")],
        left=[("proj:gamma", "hasOwner", "user:bob")],
        right=[("proj:gamma", "hasOwner", "user:alice")],
        shapes=shapes,
    )
    assert clean_one_side.shacl_conflict_prompts == 0
    assert ("proj:gamma", "hasOwner", "user:alice") in clean_one_side.merged_triples

    # Min-count violation caught when both branches remove mandatory owner
    min_viol = shacl_three_way_merge(
        base=[("proj:delta", "hasOwner", "user:bob")],
        left=[],
        right=[],
        shapes=shapes,
    )
    assert min_viol.shacl_conflict_prompts == 1
    assert min_viol.conflicts[0].reason == "shacl_min_count_violated:1"


def test_okf_procedure_memory_distillation_and_flask_endpoints():
    """OKF procedure distillation compresses verbose traces by >=90% and exposes Flask routes."""
    from company_os.shacl_procedure_merge import distill_procedure_memory

    with pytest.raises(ValueError, match="procedure_id"):
        distill_procedure_memory("", [{"action": "a"}])
    with pytest.raises(ValueError, match="episodic_events"):
        distill_procedure_memory("p1", [])

    verbose_trace = (
        "Evaluated full historical sprint context across 14 upstream tickets and "
        "verified schema invariants against quarterly budget ledger constraints " * 8
    )
    events = [
        {
            "department": "Finance",
            "action": "validate_budget_cap",
            "guard": "variance_le_2pct",
            "reasoning_trace": verbose_trace,
        },
        {
            "department": "Finance",
            "action": "validate_budget_cap",
            "guard": "variance_le_2pct",
            "reasoning_trace": verbose_trace,
        },
        {
            "department": "Ops",
            "action": "transient_timeout_attempt",
            "status": "reverted",
            "reasoning_trace": verbose_trace,
        },
        {
            "department": "Support",
            "action": "publish_sla_digest",
            "guard": "citations_bound",
            "reasoning_trace": verbose_trace,
        },
    ]
    distilled = distill_procedure_memory("quarterly-close", events)
    assert len(distilled.steps) == 2
    assert distilled.token_reduction_ratio >= 0.90

    client = app.test_client()
    m_resp = client.post(
        "/api/merge-graph",
        json={
            "base": [["task:1", "status", "todo"]],
            "left": [["task:1", "status", "doing"]],
            "right": [["task:1", "status", "todo"]],
            "shapes": {"status": {"max_count": 1, "min_count": 1}},
        },
    )
    assert m_resp.status_code == 200
    assert m_resp.get_json()["shacl_conflict_prompts"] == 0

    d_resp = client.post(
        "/api/procedures/distill",
        json={"procedure_id": "close-v1", "events": events},
    )
    assert d_resp.status_code == 200
    assert d_resp.get_json()["token_reduction_ratio"] >= 0.90

    bad_resp = client.post("/api/procedures/distill", json={"procedure_id": "x", "events": []})
    assert bad_resp.status_code == 400
