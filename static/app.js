let lastEventId = 0;

document.addEventListener("DOMContentLoaded", () => {
    initDashboard();
    
    document.getElementById("btn-advance").addEventListener("click", advanceBoard);
    document.getElementById("btn-rebuild").addEventListener("click", rebuildPlan);
    document.getElementById("modal-close").addEventListener("click", closeModal);

    // Poll live events every 2 seconds
    setInterval(fetchLiveEvents, 2000);
});

async function initDashboard() {
    await fetchCompanyConfig();
    await fetchKPIs();
    await fetchAgents();
    await fetchBoard();
    await fetchLiveEvents();
}

async function fetchCompanyConfig() {
    try {
        const res = await fetch("/api/company");
        const data = await res.json();
        document.getElementById("company-name").textContent = data.name || "CompanyOS";
        document.getElementById("company-subtitle").textContent = `${data.industry || 'Enterprise'} • ${data.location || 'Global'}`;
        
        const modeBadge = document.getElementById("mode-badge");
        if (data.execution_mode === "LIVE") {
            modeBadge.textContent = "LIVE MODE";
            modeBadge.className = "badge mode-live";
        } else {
            modeBadge.textContent = "SIM MODE";
            modeBadge.className = "badge mode-sim";
        }
    } catch (err) {
        console.error("Error fetching company config:", err);
    }
}

async function fetchKPIs() {
    try {
        const res = await fetch("/api/kpis");
        const data = await res.json();
        const cur = data.current || {};
        
        document.getElementById("kpi-revenue").textContent = formatCurrency(cur.revenue || 0);
        document.getElementById("kpi-expenses").textContent = formatCurrency(cur.expenses || 0);
        document.getElementById("kpi-profit").textContent = formatCurrency(cur.profit || 0);
        document.getElementById("kpi-margin").textContent = `Margin: ${(cur.margin || 0).toFixed(1)}%`;
        document.getElementById("kpi-pipeline").textContent = formatCurrency(cur.pipeline_value || 0);
        document.getElementById("kpi-csat").textContent = `${(cur.csat || 0).toFixed(1)} / 100`;
    } catch (err) {
        console.error("Error fetching KPIs:", err);
    }
}

async function fetchAgents() {
    try {
        const res = await fetch("/api/agents");
        const data = await res.json();
        const roster = data.agents || [];
        
        const container = document.getElementById("roster-grid");
        container.innerHTML = roster.map(ag => `
            <div class="agent-item" onclick="openAgentModal('${ag.role_id}')">
                <div class="agent-avatar">${ag.emoji}</div>
                <div class="agent-info">
                    <div class="agent-name">${ag.name}</div>
                    <div class="agent-dept">${ag.department}</div>
                    <div class="agent-status" title="${ag.last_action}">${ag.last_action}</div>
                </div>
            </div>
        `).join("");
        
        document.getElementById("agent-count-tag").textContent = `${roster.length} Executive Agents`;
    } catch (err) {
        console.error("Error fetching agents:", err);
    }
}

async function fetchBoard() {
    try {
        const res = await fetch("/api/board");
        const data = await res.json();
        const grouped = data.grouped || { backlog: [], todo: [], doing: [], done: [] };

        renderColumn("backlog", grouped.backlog);
        renderColumn("todo", grouped.todo);
        renderColumn("doing", grouped.doing);
        renderColumn("done", grouped.done);

        const total = data.total || 0;
        document.getElementById("board-summary-text").textContent = 
            `${grouped.backlog.length} Backlog • ${grouped.todo.length} To Do • ${grouped.doing.length} In Progress • ${grouped.done.length} Completed`;
    } catch (err) {
        console.error("Error fetching board:", err);
    }
}

function renderColumn(statusKey, tasks) {
    const body = document.getElementById(`cards-${statusKey}`);
    const countPill = document.getElementById(`count-${statusKey}`);
    if (countPill) countPill.textContent = tasks.length;

    if (!tasks || tasks.length === 0) {
        body.innerHTML = `<div class="event-desc" style="padding:0.5rem; color:var(--text-muted);">No tasks</div>`;
        return;
    }

    body.innerHTML = tasks.map(task => {
        const prioClass = `prio-${(task.priority || 'medium').toLowerCase()}`;
        return `
            <div class="task-card" onclick="openTaskModal('${task.id}')">
                <div class="task-dept-badge">${task.department || 'General'}</div>
                <div class="task-title">${task.title}</div>
                <div class="task-footer">
                    <span>👤 ${task.owner_agent}</span>
                    <span class="${prioClass}">${task.priority}</span>
                </div>
            </div>
        `;
    }).join("");
}

async function fetchLiveEvents() {
    try {
        const res = await fetch(`/api/events?after=${lastEventId}`);
        const data = await res.json();
        const events = data.events || [];
        
        if (events.length > 0) {
            const list = document.getElementById("events-list");
            
            // If placeholder exists, clear it
            if (list.children.length === 1 && list.children[0].innerText.includes("Initializing")) {
                list.innerHTML = "";
            }

            events.forEach(ev => {
                if (ev.id > lastEventId) {
                    lastEventId = ev.id;
                }
                const row = document.createElement("div");
                row.className = "event-row";
                const desc = JSON.stringify(ev.details || {});
                row.innerHTML = `
                    <span class="event-time">${ev.timestamp ? ev.timestamp.split(" ")[1] : ''}</span>
                    <span class="event-type">${ev.type}</span>
                    <span class="event-agent">${ev.agent || 'System'}</span>
                    <span class="event-desc">${desc}</span>
                `;
                list.insertBefore(row, list.firstChild);
            });
        }
    } catch (err) {
        console.error("Error fetching live events:", err);
    }
}

async function advanceBoard() {
    const btn = document.getElementById("btn-advance");
    btn.disabled = true;
    btn.textContent = "⏳ Advancing...";
    
    try {
        await fetch("/api/advance", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ steps: 2 })
        });
        await fetchBoard();
        await fetchKPIs();
        await fetchAgents();
        await fetchLiveEvents();
    } catch (err) {
        console.error("Error advancing board:", err);
    } finally {
        btn.disabled = false;
        btn.textContent = "⚡ Advance Board";
    }
}

async function rebuildPlan() {
    if (!confirm("Rebuild plan from company.json? This will regenerate backlog and resets KPIs.")) return;

    const btn = document.getElementById("btn-rebuild");
    btn.disabled = true;
    btn.textContent = "⏳ Rebuilding...";

    try {
        await fetch("/api/rebuild", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({})
        });
        lastEventId = 0;
        document.getElementById("events-list").innerHTML = "";
        await initDashboard();
    } catch (err) {
        console.error("Error rebuilding plan:", err);
    } finally {
        btn.disabled = false;
        btn.textContent = "🔄 Rebuild Plan";
    }
}

async function openTaskModal(taskId) {
    try {
        const res = await fetch("/api/board");
        const data = await res.json();
        const task = (data.tasks || []).find(t => t.id === taskId);
        if (!task) return;

        const body = document.getElementById("modal-body");
        document.getElementById("modal-title").textContent = `Task ${task.id}: ${task.title}`;
        
        const logsHtml = (task.log || []).map(l => `<li style="margin-bottom:0.4rem;">${l}</li>`).join("");

        body.innerHTML = `
            <div><strong>Department:</strong> ${task.department}</div>
            <div><strong>Owner Agent:</strong> ${task.owner_agent}</div>
            <div><strong>Priority:</strong> ${task.priority} | <strong>Effort:</strong> ${task.effort}</div>
            <div><strong>Status:</strong> <span class="badge mode-sim">${task.status}</span></div>
            <div style="margin-top:0.5rem;"><strong>Description:</strong><p style="color:var(--text-muted);">${task.description}</p></div>
            <div style="margin-top:0.8rem;"><strong>Execution Log:</strong>
                <ul style="padding-left:1.2rem; margin-top:0.3rem; color:#cbd5e1;">${logsHtml}</ul>
            </div>
        `;
        document.getElementById("modal-backdrop").classList.remove("hidden");
    } catch (err) {
        console.error("Error opening task modal:", err);
    }
}

async function openAgentModal(roleId) {
    try {
        const res = await fetch("/api/agents");
        const data = await res.json();
        const agent = (data.agents || []).find(a => a.role_id === roleId);
        if (!agent) return;

        document.getElementById("modal-title").textContent = `${agent.emoji} ${agent.name} (${agent.department})`;
        const body = document.getElementById("modal-body");
        
        body.innerHTML = `
            <div><strong>Mission:</strong> <p style="color:var(--text-muted);">${agent.mission}</p></div>
            <div><strong>Current Status:</strong> ${agent.status}</div>
            <div><strong>Last Action:</strong> ${agent.last_action}</div>
            <div style="margin-top:1rem; border-top:1px solid #334155; padding-top:0.8rem;">
                <strong>Direct Executive Prompt:</strong>
                <textarea id="agent-prompt-input" rows="3" style="width:100%; margin-top:0.4rem; background:#0f172a; color:white; border:1px solid #334155; border-radius:6px; padding:0.5rem;" placeholder="Ask ${agent.name} a question or give a command..."></textarea>
                <button onclick="sendAgentMessage('${agent.role_id}')" class="btn btn-primary" style="margin-top:0.5rem;">Send Message</button>
            </div>
            <div id="agent-prompt-result" style="margin-top:0.5rem;"></div>
        `;
        document.getElementById("modal-backdrop").classList.remove("hidden");
    } catch (err) {
        console.error("Error opening agent modal:", err);
    }
}

async function sendAgentMessage(roleId) {
    const input = document.getElementById("agent-prompt-input");
    const resultDiv = document.getElementById("agent-prompt-result");
    if (!input || !input.value.trim()) return;

    resultDiv.innerHTML = "<span style='color:var(--text-muted);'>Thinking...</span>";
    try {
        const res = await fetch(`/api/agent/${roleId}/message`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: input.value.trim() })
        });
        const data = await res.json();
        const resp = data.response || {};
        resultDiv.innerHTML = `
            <div style="background:#0f172a; padding:0.8rem; border-radius:6px; border:1px solid var(--accent-blue);">
                <div style="font-weight:bold; color:var(--accent-blue);">${resp.action || 'Decision'}</div>
                <div style="color:white; margin-top:0.3rem;">${resp.decision || ''}</div>
                <div style="font-size:0.75rem; color:var(--text-muted); margin-top:0.4rem;">Mode: ${resp.mode}</div>
            </div>
        `;
        await fetchAgents();
        await fetchLiveEvents();
    } catch (err) {
        resultDiv.innerHTML = `<span style="color:var(--accent-rose);">Error sending message</span>`;
    }
}

function closeModal() {
    document.getElementById("modal-backdrop").classList.add("hidden");
}

function formatCurrency(val) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);
}
