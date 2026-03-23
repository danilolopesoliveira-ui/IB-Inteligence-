"""
IB-Agents Dashboard — Painel de Controle Multi-Agentes
Run:  python app.py   (or:  py app.py)
Open: http://localhost:8080
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path

from nicegui import ui, app, events

from dashboard_state import (
    AGENT_CONFIG,
    AgentID,
    Colors,
    DashboardState,
    DEFAULT_METHODOLOGIES,
    SIDEBAR_NAV,
    TaskStatus,
    state,
)

# ---------------------------------------------------------------------------
# Upload directory
# ---------------------------------------------------------------------------
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# CSS — Light professional theme following the spec
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --text-primary: #111827;
    --text-secondary: #6B7280;
    --text-tertiary: #9CA3AF;
    --bg-page: #F3F4F6;
    --bg-card: #FFFFFF;
    --bg-sidebar: #FAFAFA;
    --border: #E5E7EB;
    --border-sidebar: #EAEAEA;
    --blue: #2563EB;
    --red: #EF4444;
    --green: #10B981;
    --amber: #F59E0B;
}

* { font-family: 'Inter', system-ui, -apple-system, sans-serif !important; }
body { background: var(--bg-page) !important; margin: 0; }
.q-page { background: var(--bg-page) !important; }
.q-header { display: none !important; }
.q-drawer { background: var(--bg-sidebar) !important; border-right: 1px solid var(--border-sidebar) !important; }
.q-drawer .q-scrollarea__content { padding: 0 !important; }
.q-layout { background: var(--bg-page) !important; }
.q-page-container { background: var(--bg-page) !important; }

/* Sidebar */
.sidebar-section-label {
    font-size: 11px;
    font-weight: 600;
    color: var(--text-tertiary);
    text-transform: uppercase;
    letter-spacing: 1.2px;
    padding: 20px 20px 8px 20px;
}
.sidebar-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 20px;
    cursor: pointer;
    border-radius: 6px;
    margin: 1px 8px;
    transition: background 0.15s ease;
    font-size: 14px;
    color: var(--text-secondary);
    text-decoration: none;
}
.sidebar-item:hover { background: #F0F0F0; }
.sidebar-item.active { background: #EBF5FF; color: var(--blue); font-weight: 600; }
.sidebar-item .material-icons { font-size: 18px; }

.sidebar-badge {
    font-size: 11px;
    font-weight: 600;
    color: white;
    padding: 1px 7px;
    border-radius: 10px;
    margin-left: auto;
}
.sidebar-agent-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
}
.sidebar-agent-live {
    font-size: 11px;
    color: var(--blue);
    margin-left: auto;
    font-weight: 500;
}

/* Task Cards */
.task-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    transition: box-shadow 0.15s ease, transform 0.1s ease;
    cursor: pointer;
}
.task-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    transform: translateY(-1px);
}
.task-card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
}
.task-card-agent-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}
.task-card-agent-name {
    font-size: 12px;
    color: var(--text-secondary);
    font-weight: 500;
}
.task-card-badge-live {
    font-size: 11px;
    font-weight: 600;
    color: white;
    background: var(--blue);
    padding: 1px 8px;
    border-radius: 10px;
}
.task-card-badge-done {
    font-size: 11px;
    font-weight: 600;
    color: white;
    background: var(--green);
    padding: 1px 8px;
    border-radius: 10px;
}
.task-card-badge-waiting {
    font-size: 11px;
    font-weight: 600;
    color: white;
    background: var(--text-tertiary);
    padding: 1px 8px;
    border-radius: 10px;
}
.task-card-badge-error {
    font-size: 11px;
    font-weight: 600;
    color: white;
    background: var(--red);
    padding: 1px 8px;
    border-radius: 10px;
}
.task-card-link {
    margin-left: auto;
    color: var(--text-tertiary);
    font-size: 16px;
    cursor: pointer;
}
.task-card-link:hover { color: var(--blue); }
.task-card-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 6px;
    line-height: 1.4;
}
.task-card-status {
    font-size: 12px;
    color: var(--text-secondary);
}
.task-card-progress {
    margin-top: 10px;
    height: 4px;
    background: #E5E7EB;
    border-radius: 2px;
    overflow: hidden;
}
.task-card-progress-bar {
    height: 100%;
    border-radius: 2px;
    transition: width 0.3s ease;
}

/* Metric Cards */
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
}
.metric-value {
    font-size: 32px;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1;
    margin-bottom: 4px;
}
.metric-label {
    font-size: 14px;
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: 2px;
}
.metric-detail {
    font-size: 12px;
    color: var(--text-tertiary);
}

/* Activity Feed */
.activity-item {
    display: flex;
    gap: 12px;
    padding: 12px 0;
    border-bottom: 1px solid var(--border);
    align-items: flex-start;
}
.activity-item:last-child { border-bottom: none; }
.activity-avatar {
    width: 32px; height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
    color: white;
    flex-shrink: 0;
}
.activity-content { flex: 1; }
.activity-agent { font-weight: 600; color: var(--text-primary); font-size: 14px; }
.activity-action { color: var(--text-secondary); font-size: 14px; }
.activity-target { color: var(--text-primary); font-size: 14px; }
.activity-time { font-size: 12px; color: var(--text-tertiary); margin-top: 2px; }

/* Charts section */
.chart-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
}
.chart-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 16px;
}

/* Section title */
.section-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 12px;
}

/* Upload dialog */
.upload-area {
    border: 2px dashed var(--border);
    border-radius: 12px;
    padding: 40px 20px;
    text-align: center;
    background: #FAFAFA;
    transition: border-color 0.2s, background 0.2s;
    cursor: pointer;
}
.upload-area:hover {
    border-color: var(--blue);
    background: #F0F7FF;
}

/* Config drawer */
.config-group {
    background: #FAFAFA;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 10px;
}
.config-group-title {
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #D1D5DB; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #9CA3AF; }
</style>
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def time_ago(dt: datetime) -> str:
    diff = datetime.now() - dt
    minutes = int(diff.total_seconds() / 60)
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes} min ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    days = hours // 24
    return f"{days} day{'s' if days > 1 else ''} ago"


def status_badge_class(status: TaskStatus) -> str:
    return {
        TaskStatus.RUNNING: "task-card-badge-live",
        TaskStatus.COMPLETED: "task-card-badge-done",
        TaskStatus.WAITING: "task-card-badge-waiting",
        TaskStatus.ERROR: "task-card-badge-error",
        TaskStatus.BLOCKED: "task-card-badge-error",
    }[status]


def status_label(status: TaskStatus) -> str:
    return {
        TaskStatus.RUNNING: "Live",
        TaskStatus.COMPLETED: "Done",
        TaskStatus.WAITING: "Waiting",
        TaskStatus.ERROR: "Error",
        TaskStatus.BLOCKED: "Blocked",
    }[status]


# ---------------------------------------------------------------------------
# Reusable render functions
# ---------------------------------------------------------------------------

# We keep references to dynamic containers so we can refresh them
_refs: dict[str, Any] = {}


def render_sidebar():
    """Render the left navigation sidebar."""
    with ui.column().classes("w-full h-full py-3").style("user-select:none;"):
        # Logo area
        with ui.row().classes("items-center gap-2 px-5 pb-4").style(
            f"border-bottom:1px solid {Colors.BORDER_SIDEBAR};"
        ):
            ui.icon("account_tree").style(f"color:{Colors.BLUE}; font-size:22px;")
            ui.label("IB-Agents").style(
                f"color:{Colors.TEXT_PRIMARY}; font-size:16px; font-weight:700;"
            )

        # Nav sections
        for section_group in SIDEBAR_NAV:
            section_label = section_group["section"]
            if section_label:
                ui.html(f'<div class="sidebar-section-label">{section_label}</div>')

            for item in section_group["items"]:
                is_active = state.active_nav == item["id"]
                active_cls = " active" if is_active else ""

                with ui.element("div").classes(f"sidebar-item{active_cls}").on(
                    "click", lambda _, iid=item["id"]: set_active_nav(iid)
                ):
                    ui.icon(item["icon"]).style("font-size:18px;")
                    ui.label(item["label"])
                    if item.get("badge"):
                        bg = item.get("badge_color", Colors.RED)
                        ui.html(
                            f'<span class="sidebar-badge" style="background:{bg};">'
                            f'{item["badge"]}</span>'
                        )

            # Add "+" button after PROJECTS section
            if section_label == "PROJECTS":
                with ui.element("div").classes("sidebar-item").style("color:#9CA3AF;"):
                    ui.icon("add").style("font-size:18px;")
                    ui.label("Add Project")

        # AGENTS section
        ui.html('<div class="sidebar-section-label">AGENTS</div>')

        # Only show agents that have tasks
        sidebar_agents = [
            AgentID.SOPHIA, AgentID.VP_ENGINEERING,
            AgentID.VP_COMMUNICATIONS, AgentID.VP_CONTENT,
        ]
        for agent_id in sidebar_agents:
            cfg = AGENT_CONFIG[agent_id]
            live = state.get_agent_live_count(agent_id)
            is_active = state.filter_agent == agent_id

            with ui.element("div").classes(
                f"sidebar-item{'  active' if is_active else ''}"
            ).on("click", lambda _, aid=agent_id: toggle_agent_filter(aid)):
                ui.html(f'<span class="sidebar-agent-dot" style="background:{cfg["color"]};"></span>')
                ui.label(cfg["name"]).style("font-size:13px;")
                if live > 0:
                    ui.html(f'<span class="sidebar-agent-live">{live} live</span>')

        # Pipeline agents (IB-specific)
        ui.html('<div class="sidebar-section-label">PIPELINE AGENTS</div>')
        pipeline_agents = [
            AgentID.RESEARCH, AgentID.ACCOUNTANT, AgentID.MODELER,
            AgentID.QUANT, AgentID.RISK, AgentID.DECK, AgentID.ORCHESTRATOR,
        ]
        for agent_id in pipeline_agents:
            cfg = AGENT_CONFIG[agent_id]
            live = state.get_agent_live_count(agent_id)
            is_active = state.filter_agent == agent_id

            with ui.element("div").classes(
                f"sidebar-item{'  active' if is_active else ''}"
            ).on("click", lambda _, aid=agent_id: toggle_agent_filter(aid)):
                ui.html(f'<span class="sidebar-agent-dot" style="background:{cfg["color"]};"></span>')
                ui.label(cfg["short"]).style("font-size:13px;")
                if live > 0:
                    ui.html(f'<span class="sidebar-agent-live">{live} live</span>')


def render_task_card(task):
    """Render a single task card."""
    agent_cfg = AGENT_CONFIG[task.agent_id]
    badge_cls = status_badge_class(task.status)
    badge_lbl = status_label(task.status)

    with ui.column().classes("task-card"):
        # Header: dot + agent name + badge + link
        ui.html(
            f'<div class="task-card-header">'
            f'<span class="task-card-agent-dot" style="background:{agent_cfg["color"]};"></span>'
            f'<span class="task-card-agent-name">{agent_cfg["initials"]}  {agent_cfg["name"]}</span>'
            f'<span class="{badge_cls}">{badge_lbl}</span>'
            f'<span class="task-card-link material-icons">open_in_new</span>'
            f'</div>'
        )
        # Title
        ui.html(
            f'<div class="task-card-title">{task.sop_id} - {task.title}</div>'
        )
        # Status text
        if task.status == TaskStatus.RUNNING:
            ui.html(f'<div class="task-card-status">Processing... {task.progress}%</div>')
        elif task.status == TaskStatus.WAITING:
            ui.html('<div class="task-card-status">Waiting for output...</div>')
        elif task.status == TaskStatus.COMPLETED:
            elapsed = ""
            if task.started_at and task.finished_at:
                diff = task.finished_at - task.started_at
                mins = int(diff.total_seconds() / 60)
                elapsed = f" in {mins}min" if mins > 0 else ""
            ui.html(f'<div class="task-card-status" style="color:{Colors.GREEN};">Completed{elapsed}</div>')
        elif task.status == TaskStatus.ERROR:
            ui.html(f'<div class="task-card-status" style="color:{Colors.RED};">Error: {task.result_summary}</div>')

        # Progress bar for running tasks
        if task.status == TaskStatus.RUNNING and task.progress > 0:
            color = agent_cfg["color"]
            ui.html(
                f'<div class="task-card-progress">'
                f'<div class="task-card-progress-bar" style="width:{task.progress}%; background:{color};"></div>'
                f'</div>'
            )

        # Timestamp
        if task.started_at:
            ui.html(f'<div style="font-size:11px; color:{Colors.TEXT_TERTIARY}; margin-top:6px;">'
                    f'{time_ago(task.started_at)}</div>')


def render_task_grid():
    """Render the grid of task cards."""
    container = ui.element("div").style(
        "display:grid; grid-template-columns:repeat(3,1fr); gap:16px; width:100%;"
    )
    _refs["task_grid"] = container
    with container:
        tasks = state.get_filtered_tasks()
        if not tasks:
            with ui.column().classes("items-center justify-center").style(
                "grid-column:1/-1; padding:60px; text-align:center;"
            ):
                ui.icon("inbox").style(f"font-size:48px; color:{Colors.TEXT_TERTIARY};")
                ui.label("Nenhuma tarefa encontrada").style(
                    f"color:{Colors.TEXT_SECONDARY}; font-size:14px; margin-top:8px;"
                )
        else:
            for task in tasks:
                render_task_card(task)


def render_metrics():
    """Render the KPI metric cards."""
    metrics = state.get_metrics()
    container = ui.element("div").style(
        "display:grid; grid-template-columns:repeat(4,1fr); gap:16px; width:100%;"
    )
    _refs["metrics"] = container
    with container:
        for m in metrics:
            with ui.column().classes("metric-card"):
                ui.html(f'<div class="metric-value">{m.value}</div>')
                ui.html(f'<div class="metric-label">{m.label}</div>')
                ui.html(f'<div class="metric-detail">{m.detail}</div>')


def render_charts():
    """Render the three charts."""
    container = ui.element("div").style(
        "display:grid; grid-template-columns:repeat(3,1fr); gap:16px; width:100%;"
    )
    _refs["charts"] = container
    with container:
        # Chart 1: Run Activity (stacked bar)
        run_data = state.get_run_activity_data()
        with ui.column().classes("chart-card"):
            ui.html('<div class="chart-title">Run Activity</div>')
            ui.echart({
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                "legend": {"bottom": 0, "textStyle": {"fontSize": 11, "color": Colors.TEXT_SECONDARY}},
                "grid": {"left": 30, "right": 10, "top": 10, "bottom": 40},
                "xAxis": {"type": "category", "data": run_data["categories"],
                          "axisLabel": {"fontSize": 11, "color": Colors.TEXT_SECONDARY}},
                "yAxis": {"type": "value",
                          "axisLabel": {"fontSize": 11, "color": Colors.TEXT_SECONDARY}},
                "series": [
                    {"name": s["name"], "type": "bar", "stack": "total",
                     "data": s["data"],
                     "itemStyle": {"color": s["color"], "borderRadius": [2, 2, 0, 0]}}
                    for s in run_data["series"]
                ],
            }).style("height:220px; width:100%;")

        # Chart 2: Issues by Priority
        prio_data = state.get_issues_priority_data()
        with ui.column().classes("chart-card"):
            ui.html('<div class="chart-title">Issues by Priority</div>')
            ui.echart({
                "tooltip": {"trigger": "axis"},
                "grid": {"left": 30, "right": 10, "top": 10, "bottom": 30},
                "xAxis": {"type": "category", "data": prio_data["categories"],
                          "axisLabel": {"fontSize": 11, "color": Colors.TEXT_SECONDARY}},
                "yAxis": {"type": "value",
                          "axisLabel": {"fontSize": 11, "color": Colors.TEXT_SECONDARY}},
                "series": [{
                    "type": "bar",
                    "data": [
                        {"value": v, "itemStyle": {"color": c, "borderRadius": [4, 4, 0, 0]}}
                        for v, c in zip(prio_data["values"], prio_data["colors"])
                    ],
                    "barWidth": "40%",
                }],
            }).style("height:220px; width:100%;")

        # Chart 3: Issues by Status
        status_data = state.get_issues_status_data()
        with ui.column().classes("chart-card"):
            ui.html('<div class="chart-title">Issues by Status</div>')
            ui.echart({
                "tooltip": {"trigger": "axis"},
                "grid": {"left": 30, "right": 10, "top": 10, "bottom": 30},
                "xAxis": {"type": "category", "data": status_data["categories"],
                          "axisLabel": {"fontSize": 11, "color": Colors.TEXT_SECONDARY}},
                "yAxis": {"type": "value",
                          "axisLabel": {"fontSize": 11, "color": Colors.TEXT_SECONDARY}},
                "series": [{
                    "type": "bar",
                    "data": [
                        {"value": v, "itemStyle": {"color": c, "borderRadius": [4, 4, 0, 0]}}
                        for v, c in zip(status_data["values"], status_data["colors"])
                    ],
                    "barWidth": "40%",
                }],
            }).style("height:220px; width:100%;")


def render_activity_feed():
    """Render the Activity Feed section."""
    container = ui.column().classes("w-full")
    _refs["activity"] = container
    with container:
        if not state.activity_log:
            ui.label("No activity yet.").style(
                f"color:{Colors.TEXT_SECONDARY}; font-size:14px; padding:20px 0;"
            )
            return
        for entry in state.activity_log[:10]:
            agent_cfg = AGENT_CONFIG[entry.agent_id]
            ui.html(
                f'<div class="activity-item">'
                f'<div class="activity-avatar" style="background:{agent_cfg["color"]};">'
                f'{agent_cfg["initials"]}</div>'
                f'<div class="activity-content">'
                f'<div><span class="activity-agent">{agent_cfg["name"]}</span> '
                f'<span class="activity-action">{entry.action}</span> '
                f'<span class="activity-target">{entry.target}</span></div>'
                f'<div class="activity-time">{time_ago(entry.timestamp)}</div>'
                f'</div></div>'
            )


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

def set_active_nav(nav_id: str):
    state.active_nav = nav_id
    refresh_all()


def toggle_agent_filter(agent_id: AgentID):
    if state.filter_agent == agent_id:
        state.filter_agent = None
    else:
        state.filter_agent = agent_id
    refresh_all()


def refresh_all():
    """Rebuild all dynamic sections."""
    for key in ["task_grid", "metrics", "activity"]:
        ref = _refs.get(key)
        if ref:
            ref.clear()

    # Re-render task grid
    tg = _refs.get("task_grid")
    if tg:
        with tg:
            tasks = state.get_filtered_tasks()
            if not tasks:
                with ui.column().classes("items-center justify-center").style(
                    "grid-column:1/-1; padding:60px; text-align:center;"
                ):
                    ui.icon("inbox").style(f"font-size:48px; color:{Colors.TEXT_TERTIARY};")
                    ui.label("Nenhuma tarefa encontrada").style(
                        f"color:{Colors.TEXT_SECONDARY}; font-size:14px; margin-top:8px;"
                    )
            else:
                for task in tasks:
                    render_task_card(task)

    # Re-render metrics
    mc = _refs.get("metrics")
    if mc:
        with mc:
            for m in state.get_metrics():
                with ui.column().classes("metric-card"):
                    ui.html(f'<div class="metric-value">{m.value}</div>')
                    ui.html(f'<div class="metric-label">{m.label}</div>')
                    ui.html(f'<div class="metric-detail">{m.detail}</div>')

    # Re-render activity
    ac = _refs.get("activity")
    if ac:
        with ac:
            if not state.activity_log:
                ui.label("No activity yet.").style(
                    f"color:{Colors.TEXT_SECONDARY}; font-size:14px; padding:20px 0;"
                )
            else:
                for entry in state.activity_log[:10]:
                    agent_cfg = AGENT_CONFIG[entry.agent_id]
                    ui.html(
                        f'<div class="activity-item">'
                        f'<div class="activity-avatar" style="background:{agent_cfg["color"]};">'
                        f'{agent_cfg["initials"]}</div>'
                        f'<div class="activity-content">'
                        f'<div><span class="activity-agent">{agent_cfg["name"]}</span> '
                        f'<span class="activity-action">{entry.action}</span> '
                        f'<span class="activity-target">{entry.target}</span></div>'
                        f'<div class="activity-time">{time_ago(entry.timestamp)}</div>'
                        f'</div></div>'
                    )


# ---------------------------------------------------------------------------
# Upload & Analysis Dialogs
# ---------------------------------------------------------------------------

def open_upload_dialog():
    with ui.dialog().props("maximized=false") as dlg, ui.card().style(
        "width:600px; max-width:90vw; padding:24px;"
    ):
        ui.label("Nova Analise").style(
            f"font-size:18px; font-weight:700; color:{Colors.TEXT_PRIMARY}; margin-bottom:16px;"
        )

        company_input = ui.input(
            label="Nome da Empresa",
            placeholder="Ex: Empresa XYZ S.A.",
        ).classes("w-full mb-3")

        with ui.row().classes("w-full gap-3 mb-3"):
            deal_select = ui.select(
                options=["M&A", "PE_Investment", "Debt_Advisory", "IPO_Readiness"],
                value="M&A",
                label="Tipo de Transacao",
            ).classes("flex-grow")
            sector_input = ui.input(
                label="Setor",
                value="industria",
                placeholder="Ex: tecnologia, saude...",
            ).classes("flex-grow")

        ui.label("Arquivo de Dados").style(
            f"font-size:13px; font-weight:600; color:{Colors.TEXT_PRIMARY}; margin-bottom:8px;"
        )

        upload_ref = {"name": None}

        def on_upload(e: events.UploadEventArguments):
            dest = UPLOAD_DIR / e.name
            dest.write_bytes(e.content.read())
            state.uploaded_file_path = str(dest)
            state.uploaded_file_name = e.name
            upload_ref["name"] = e.name
            ui.notify(f"Arquivo '{e.name}' carregado!", type="positive")

        ui.upload(
            label="Arraste ou clique (XLSX, PDF, CSV)",
            auto_upload=True,
            on_upload=on_upload,
        ).classes("w-full mb-3").props('accept=".xlsx,.xls,.pdf,.csv" flat bordered')

        demo_switch = ui.switch("Usar dados demo (sinteticos)").classes("mb-3")

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancelar", on_click=dlg.close).props("flat")
            ui.button("Iniciar Analise", icon="rocket_launch", on_click=lambda: start_analysis(
                dlg, company_input.value, deal_select.value, sector_input.value, demo_switch.value
            )).props('color="primary"')

    dlg.open()


def open_config_drawer():
    with ui.dialog().props("position=right full-height maximized=false") as dlg, ui.card().style(
        "width:420px; max-width:90vw; padding:24px; height:100vh; overflow-y:auto;"
    ):
        ui.label("Metodologias dos Agentes").style(
            f"font-size:18px; font-weight:700; color:{Colors.TEXT_PRIMARY}; margin-bottom:4px;"
        )
        ui.label("Ajuste parametros antes de iniciar a analise").style(
            f"font-size:12px; color:{Colors.TEXT_SECONDARY}; margin-bottom:20px;"
        )

        for agent_id, params in DEFAULT_METHODOLOGIES.items():
            if not params:
                continue
            cfg = AGENT_CONFIG[agent_id]
            with ui.column().classes("config-group"):
                ui.html(
                    f'<div class="config-group-title">'
                    f'<span class="material-icons" style="font-size:18px; color:{cfg["color"]};">'
                    f'{cfg["icon"]}</span>'
                    f'<span style="color:{cfg["color"]};">{cfg["name"]}</span>'
                    f'</div>'
                )
                for key, param in params.items():
                    label = param.get("label", key)
                    value = param.get("value")
                    options = param.get("options")

                    if options:
                        ui.select(
                            options=options, value=value, label=label,
                            on_change=lambda e, aid=agent_id, k=key: state.set_methodology_value(aid, k, e.value),
                        ).classes("w-full mb-1").props("dense outlined")
                    elif isinstance(value, bool):
                        ui.switch(
                            label, value=value,
                            on_change=lambda e, aid=agent_id, k=key: state.set_methodology_value(aid, k, e.value),
                        )
                    elif isinstance(value, (int, float)):
                        ui.number(
                            label=label, value=value,
                            on_change=lambda e, aid=agent_id, k=key: state.set_methodology_value(aid, k, e.value),
                        ).classes("w-full mb-1").props("dense outlined")
                    else:
                        ui.input(
                            label=label, value=str(value),
                            on_change=lambda e, aid=agent_id, k=key: state.set_methodology_value(aid, k, e.value),
                        ).classes("w-full mb-1").props("dense outlined")

        with ui.row().classes("w-full justify-end mt-4"):
            ui.button("Fechar", on_click=dlg.close).props("flat")

    dlg.open()


# ---------------------------------------------------------------------------
# Analysis Execution
# ---------------------------------------------------------------------------

async def start_analysis(dlg, company, deal_type, sector, use_demo):
    dlg.close()

    state.company_name = company or "Demo Industria S.A."
    state.deal_type = deal_type
    state.sector = sector or "industria"
    state.use_demo = use_demo
    state.is_running = True

    if use_demo:
        state.init_demo_tasks()
        state.init_demo_activity()
    else:
        state.init_tasks()
        state.activity_log.clear()

    state.log(AgentID.ORCHESTRATOR, "started", f"Pipeline para {state.company_name} ({state.deal_type})")
    refresh_all()

    if not use_demo:
        asyncio.create_task(run_crew_pipeline())


async def run_crew_pipeline():
    try:
        from crew_runner import execute_pipeline
        await execute_pipeline(state, refresh_all)
    except ImportError:
        await simulate_pipeline()
    except Exception as exc:
        state.log(AgentID.ORCHESTRATOR, "error", f"Erro critico: {exc}")
        state.is_running = False
        refresh_all()


async def simulate_pipeline():
    """Simulated pipeline for visual demo."""
    state.log(AgentID.ORCHESTRATOR, "started", "Modo simulacao (sem API key)")

    for task in state.tasks:
        if task.status != TaskStatus.WAITING:
            continue
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        state.log(task.agent_id, "started", f"{task.sop_id} - {task.title}")
        refresh_all()

        for p in range(0, 101, 10):
            task.progress = p
            refresh_all()
            await asyncio.sleep(0.3)

        task.status = TaskStatus.COMPLETED
        task.finished_at = datetime.now()
        task.progress = 100
        task.result_summary = ""
        state.log(task.agent_id, "completed", f"{task.sop_id} - {task.title}")
        refresh_all()

    state.is_running = False
    state.log(AgentID.ORCHESTRATOR, "completed", "Pipeline concluido com sucesso!")
    refresh_all()
    ui.notify("Analise concluida!", type="positive")


# ---------------------------------------------------------------------------
# Main Page
# ---------------------------------------------------------------------------

@ui.page("/")
def main_page():
    ui.add_head_html(CUSTOM_CSS)
    ui.add_head_html('<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">')

    # Initialize demo data on first load
    if not state.tasks:
        state.init_demo_tasks()
        state.init_demo_activity()

    # Sidebar (left drawer, always open on desktop)
    with ui.left_drawer(value=True, fixed=True, bordered=False).style(
        f"width:260px; background:{Colors.BG_SIDEBAR}; "
        f"border-right:1px solid {Colors.BORDER_SIDEBAR};"
    ).props('width=260 breakpoint=800'):
        render_sidebar()

    # Main content
    with ui.column().classes("w-full p-6 gap-6").style(f"background:{Colors.BG_PAGE};"):

        # Page Header
        with ui.row().classes("w-full items-center"):
            ui.label("Dashboard").style(
                f"font-size:24px; font-weight:700; color:{Colors.TEXT_PRIMARY};"
            )
            ui.space()

            # Live count badge
            live_count = len(state.get_tasks_by_status(TaskStatus.RUNNING))
            if live_count > 0:
                ui.html(
                    f'<span style="background:{Colors.BLUE}; color:white; font-size:12px; '
                    f'font-weight:600; padding:3px 10px; border-radius:12px;">'
                    f'{live_count} live</span>'
                )

            ui.button("Config", icon="tune", on_click=open_config_drawer).props(
                "flat dense"
            ).style(f"color:{Colors.TEXT_SECONDARY};")

            ui.button("Nova Analise", icon="add", on_click=open_upload_dialog).props(
                'color="primary" size="md"'
            )

        # KPI Metrics
        render_metrics()

        # Task Grid
        ui.html(f'<div class="section-title">Tasks</div>')
        render_task_grid()

        # Charts
        ui.html(f'<div class="section-title" style="margin-top:8px;">Analytics</div>')
        render_charts()

        # Activity Feed
        with ui.column().classes("w-full").style(
            f"background:{Colors.BG_CARD}; border:1px solid {Colors.BORDER}; "
            f"border-radius:8px; padding:20px;"
        ):
            ui.html('<div class="section-title">Recent Activity</div>')
            render_activity_feed()


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="IB-Agents | Dashboard",
        port=8080,
        dark=False,
        reload=True,
        favicon="https://api.iconify.design/mdi:chart-tree.svg",
    )
