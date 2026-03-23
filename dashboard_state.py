"""
Shared state for the IB-Agents Dashboard.
Manages agents, tasks (SOPs), activity log, metrics, and methodology configuration.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable


# ---------------------------------------------------------------------------
# Color Palette (from spec)
# ---------------------------------------------------------------------------

class Colors:
    TEXT_PRIMARY = "#111827"
    TEXT_SECONDARY = "#6B7280"
    TEXT_TERTIARY = "#9CA3AF"
    BG_PAGE = "#F3F4F6"
    BG_CARD = "#FFFFFF"
    BG_SIDEBAR = "#FAFAFA"
    BORDER = "#E5E7EB"
    BORDER_SIDEBAR = "#EAEAEA"
    BLUE = "#2563EB"
    RED = "#EF4444"
    GREEN = "#10B981"
    AMBER = "#F59E0B"
    BLACK = "#000000"
    GRAY_DARK = "#374151"
    PURPLE = "#8B5CF6"
    INDIGO = "#6366F1"


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TaskStatus(str, Enum):
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    BLOCKED = "blocked"


class AgentID(str, Enum):
    SOPHIA = "sophia_celestino"
    VP_ENGINEERING = "vp_engineering"
    VP_COMMUNICATIONS = "vp_communications"
    VP_CONTENT = "vp_content"
    RESEARCH = "research_analyst"
    ACCOUNTANT = "accountant"
    MODELER = "financial_modeler"
    QUANT = "quant_analyst"
    RISK = "risk_compliance"
    DECK = "deck_builder"
    ORCHESTRATOR = "orchestrator"


# ---------------------------------------------------------------------------
# Agent Configuration
# ---------------------------------------------------------------------------

AGENT_CONFIG = {
    AgentID.SOPHIA: {
        "name": "Sophia Celestino",
        "title": "Coordenadora",
        "short": "SC",
        "color": Colors.BLUE,
        "icon": "person",
        "initials": "SC",
        "order": 0,
    },
    AgentID.VP_ENGINEERING: {
        "name": "VP Engineering",
        "title": "Vice President of Engineering",
        "short": "VPE",
        "color": Colors.GREEN,
        "icon": "engineering",
        "initials": "VE",
        "order": 1,
    },
    AgentID.VP_COMMUNICATIONS: {
        "name": "VP Communications",
        "title": "Vice President of Communications",
        "short": "VPC",
        "color": Colors.PURPLE,
        "icon": "campaign",
        "initials": "VC",
        "order": 2,
    },
    AgentID.VP_CONTENT: {
        "name": "VP Content",
        "title": "Vice President of Content",
        "short": "VPT",
        "color": Colors.AMBER,
        "icon": "edit_note",
        "initials": "VT",
        "order": 3,
    },
    AgentID.RESEARCH: {
        "name": "Research Analyst",
        "title": "Analista de Pesquisa",
        "short": "RA",
        "color": "#3B82F6",
        "icon": "search",
        "initials": "RA",
        "order": 4,
    },
    AgentID.ACCOUNTANT: {
        "name": "Accountant",
        "title": "Contador / IFRS",
        "short": "ACC",
        "color": "#059669",
        "icon": "account_balance",
        "initials": "AC",
        "order": 5,
    },
    AgentID.MODELER: {
        "name": "Financial Modeler",
        "title": "Modelador Financeiro",
        "short": "FM",
        "color": "#7C3AED",
        "icon": "analytics",
        "initials": "FM",
        "order": 6,
    },
    AgentID.QUANT: {
        "name": "Quant Analyst",
        "title": "Analista Quantitativo",
        "short": "QA",
        "color": "#D97706",
        "icon": "bar_chart",
        "initials": "QA",
        "order": 7,
    },
    AgentID.RISK: {
        "name": "Risk & Compliance",
        "title": "Risco e Compliance",
        "short": "RC",
        "color": "#DC2626",
        "icon": "shield",
        "initials": "RC",
        "order": 8,
    },
    AgentID.DECK: {
        "name": "Deck Builder",
        "title": "Gerador de Outputs",
        "short": "DB",
        "color": "#B45309",
        "icon": "slideshow",
        "initials": "DB",
        "order": 9,
    },
    AgentID.ORCHESTRATOR: {
        "name": "MD Orchestrator",
        "title": "Managing Director",
        "short": "MD",
        "color": "#4338CA",
        "icon": "supervisor_account",
        "initials": "MD",
        "order": 10,
    },
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class AgentTask:
    id: str
    sop_id: str
    title: str
    description: str
    agent_id: AgentID
    status: TaskStatus = TaskStatus.WAITING
    progress: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result_summary: str = ""


@dataclass
class ActivityEntry:
    timestamp: datetime
    agent_id: AgentID
    action: str       # "commented on", "created", "completed", "started"
    target: str        # SOP or task description
    level: str = "info"


@dataclass
class Metric:
    label: str
    value: str | int
    detail: str
    icon: str = ""
    color: str = Colors.TEXT_PRIMARY


# ---------------------------------------------------------------------------
# Methodology Defaults (configurable per agent)
# ---------------------------------------------------------------------------

DEFAULT_METHODOLOGIES: dict[AgentID, dict[str, Any]] = {
    AgentID.RESEARCH: {
        "parse_mode": {"value": "auto", "options": ["auto", "excel", "pdf"], "label": "Modo de Parsing"},
        "detect_currency": {"value": True, "label": "Detectar Moeda Automaticamente"},
    },
    AgentID.ACCOUNTANT: {
        "apply_ifrs16": {"value": True, "label": "Aplicar IFRS 16 (Leases)"},
        "normalize_ebitda": {"value": True, "label": "Normalizar EBITDA"},
        "check_provisions": {"value": True, "label": "Verificar Provisoes"},
        "depreciation_check": {"value": True, "label": "Verificar Depreciacao"},
    },
    AgentID.MODELER: {
        "wacc_method": {"value": "capm_br", "options": ["capm_br", "capm_us_adj", "manual"], "label": "Metodo WACC"},
        "wacc_manual": {"value": 12.5, "label": "WACC Manual (%)"},
        "projection_years": {"value": 5, "label": "Anos de Projecao"},
        "terminal_growth": {"value": 4.0, "label": "Crescimento Perpetuidade (%)"},
        "tax_rate": {"value": 34.0, "label": "Aliquota IR/CS (%)"},
    },
    AgentID.QUANT: {
        "comps_source": {"value": "b3", "options": ["b3", "global", "custom"], "label": "Fonte de Comparaveis"},
        "multiples": {"value": "EV/EBITDA,P/E,EV/Revenue", "label": "Multiplos"},
        "chart_style": {"value": "light", "options": ["light", "dark", "corporate"], "label": "Estilo dos Graficos"},
    },
    AgentID.RISK: {
        "max_leverage": {"value": 3.5, "label": "Leverage Maximo (x EBITDA)"},
        "min_coverage": {"value": 2.5, "label": "Cobertura Minima (EBITDA/Juros)"},
        "stress_scenarios": {"value": True, "label": "Rodar Cenarios de Stress"},
    },
    AgentID.DECK: {
        "output_pptx": {"value": True, "label": "Gerar Pitch Book (PPTX)"},
        "output_xlsx": {"value": True, "label": "Gerar Modelo Financeiro (XLSX)"},
        "output_pdf_report": {"value": True, "label": "Gerar Research Report (PDF)"},
        "output_pdf_memo": {"value": True, "label": "Gerar Executive Memo (PDF)"},
        "language": {"value": "pt-BR", "options": ["pt-BR", "en-US"], "label": "Idioma dos Outputs"},
    },
    AgentID.ORCHESTRATOR: {
        "store_memory": {"value": True, "label": "Armazenar na Memoria RAG"},
        "final_review": {"value": True, "label": "Revisao Final do MD"},
    },
}

# Sidebar navigation
SIDEBAR_NAV = [
    {"section": None, "items": [
        {"id": "dashboard", "label": "Dashboard", "icon": "dashboard", "badge": None, "badge_color": Colors.BLUE},
        {"id": "inbox", "label": "Inbox", "icon": "inbox", "badge": "2", "badge_color": Colors.RED},
    ]},
    {"section": "WORK", "items": [
        {"id": "issues", "label": "Issues", "icon": "bug_report", "badge": None, "badge_color": None},
        {"id": "goals", "label": "Goals", "icon": "flag", "badge": None, "badge_color": None},
    ]},
    {"section": "PROJECTS", "items": [
        {"id": "ma_project", "label": "M&A Pipeline", "icon": "folder", "badge": None, "badge_color": None},
        {"id": "due_diligence", "label": "Due Diligence", "icon": "folder", "badge": None, "badge_color": None},
        {"id": "pitch_decks", "label": "Pitch Decks", "icon": "folder", "badge": None, "badge_color": None},
    ]},
    {"section": "COMPANY", "items": [
        {"id": "org", "label": "Org", "icon": "business", "badge": None, "badge_color": None},
        {"id": "costs", "label": "Costs", "icon": "payments", "badge": None, "badge_color": None},
        {"id": "activity", "label": "Activity", "icon": "timeline", "badge": None, "badge_color": None},
        {"id": "settings", "label": "Settings", "icon": "settings", "badge": None, "badge_color": None},
    ]},
]


# ---------------------------------------------------------------------------
# Dashboard State
# ---------------------------------------------------------------------------

class DashboardState:

    def __init__(self) -> None:
        self.tasks: list[AgentTask] = []
        self.activity_log: list[ActivityEntry] = []
        self.methodologies: dict[AgentID, dict[str, Any]] = {
            aid: {k: dict(v) for k, v in params.items()}
            for aid, params in DEFAULT_METHODOLOGIES.items()
        }
        self.is_running = False
        self.company_name = ""
        self.deal_type = "M&A"
        self.sector = "industria"
        self.uploaded_file_path: str | None = None
        self.uploaded_file_name: str | None = None
        self.use_demo = False
        self.active_nav = "dashboard"
        self.filter_agent: AgentID | None = None
        self._listeners: list[Callable] = []

    # -- Listeners --
    def add_listener(self, fn: Callable) -> None:
        if fn not in self._listeners:
            self._listeners.append(fn)

    def remove_listener(self, fn: Callable) -> None:
        self._listeners = [f for f in self._listeners if f is not fn]

    async def _notify(self) -> None:
        for fn in self._listeners:
            try:
                result = fn()
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                pass

    # -- Activity Log --
    def log(self, agent_id: AgentID, action: str, target: str, level: str = "info") -> None:
        self.activity_log.insert(0, ActivityEntry(
            timestamp=datetime.now(),
            agent_id=agent_id,
            action=action,
            target=target,
            level=level,
        ))
        if len(self.activity_log) > 200:
            self.activity_log = self.activity_log[:200]

    # -- Tasks --
    def init_tasks(self) -> None:
        """Create the standard IB pipeline tasks as SOPs."""
        self.tasks = [
            AgentTask("t1", "SOP-1", "Data Ingestion & Parsing",
                      "Parsing e estruturacao dos dados financeiros do arquivo enviado",
                      AgentID.RESEARCH),
            AgentTask("t2", "SOP-2", "Ajustes Contabeis IFRS",
                      "Revisao IFRS 16, normalizacao EBITDA, provisoes, depreciacao",
                      AgentID.ACCOUNTANT),
            AgentTask("t3", "SOP-3", "Consolidacao & Modelagem DCF",
                      "Consolidacao de DFs, modelo DCF, analise de credito, LBO",
                      AgentID.MODELER),
            AgentTask("t4", "SOP-4", "Trading Comps & Charts",
                      "Comparaveis de mercado, multiplos, football field, graficos",
                      AgentID.QUANT),
            AgentTask("t5", "SOP-5", "Risk Assessment & Compliance",
                      "Red flags, covenants, stress test, parecer de risco",
                      AgentID.RISK),
            AgentTask("t6", "SOP-6", "Output Generation",
                      "Pitch Book PPTX, Modelo XLSX, Research PDF, Executive Memo",
                      AgentID.DECK),
            AgentTask("t7", "SOP-7", "MD Final Review",
                      "Revisao de consistencia, validacao de valuation, parecer final",
                      AgentID.ORCHESTRATOR),
        ]

    def init_demo_tasks(self) -> None:
        """Create demo tasks with mixed statuses for visual preview."""
        now = datetime.now()
        self.tasks = [
            AgentTask("t1", "SOP-2", "Meta 4: Go-Live",
                      "Go-Live da operacao M&A — 12/03 19h BRT",
                      AgentID.SOPHIA, TaskStatus.RUNNING, 65,
                      now - timedelta(minutes=32)),
            AgentTask("t2", "SOP-38", "Alternar fase da turma para Due Diligence",
                      "Transicao da fase de analise para due diligence formal",
                      AgentID.SOPHIA, TaskStatus.RUNNING, 40,
                      now - timedelta(minutes=18)),
            AgentTask("t3", "SOP-4", "Infrastructure Pronta",
                      "Validacao de infraestrutura para deploy do modelo",
                      AgentID.VP_ENGINEERING, TaskStatus.RUNNING, 80,
                      now - timedelta(hours=1)),
            AgentTask("t4", "SOP-26", "Fluxo n8n — Pipeline de Dados",
                      "Configuracao do pipeline automatizado via n8n",
                      AgentID.VP_ENGINEERING, TaskStatus.COMPLETED, 100,
                      now - timedelta(hours=3), now - timedelta(hours=1)),
            AgentTask("t5", "SOP-41", "Monitorar membros online durante aula ao vivo",
                      "Tracking de participantes na sessao de apresentacao",
                      AgentID.SOPHIA, TaskStatus.WAITING),
            AgentTask("t6", "SOP-25", "Enviar credenciais aos participantes",
                      "Distribuicao de acessos para a plataforma",
                      AgentID.VP_COMMUNICATIONS, TaskStatus.RUNNING, 25,
                      now - timedelta(minutes=45)),
            AgentTask("t7", "SOP-12", "Preparar Pitch Deck v2",
                      "Revisao e atualizacao do pitch deck com novos dados",
                      AgentID.VP_CONTENT, TaskStatus.RUNNING, 55,
                      now - timedelta(hours=2)),
            AgentTask("t8", "SOP-8", "Analise de Comparaveis — Setor Tech",
                      "Levantamento de multiplos de empresas listadas",
                      AgentID.VP_COMMUNICATIONS, TaskStatus.COMPLETED, 100,
                      now - timedelta(hours=5), now - timedelta(hours=2)),
            AgentTask("t9", "SOP-15", "Revisao Compliance CVM",
                      "Checklist de compliance regulatorio CVM",
                      AgentID.VP_COMMUNICATIONS, TaskStatus.WAITING),
        ]

    def init_demo_activity(self) -> None:
        """Create demo activity entries."""
        now = datetime.now()
        entries = [
            (AgentID.VP_ENGINEERING, "commented on", "SOP-4 - Meta 2: Infrastructure Pronta", 2),
            (AgentID.SOPHIA, "commented on", "SOP-2 - Meta 4: Go-Live — 12/03 19h BRT", 5),
            (AgentID.SOPHIA, "created", "SOP-41 - Monitorar membros online durante aula ao vivo", 8),
            (AgentID.VP_CONTENT, "started", "SOP-12 - Preparar Pitch Deck v2", 10),
            (AgentID.VP_COMMUNICATIONS, "completed", "SOP-8 - Analise de Comparaveis — Setor Tech", 12),
            (AgentID.VP_ENGINEERING, "completed", "SOP-26 - Fluxo n8n — Pipeline de Dados", 14),
            (AgentID.SOPHIA, "assigned", "SOP-25 - Enviar credenciais aos participantes → VP Communications", 16),
            (AgentID.VP_CONTENT, "commented on", "SOP-12 - Precisa de dados atualizados do Q4", 18),
        ]
        self.activity_log = []
        for agent_id, action, target, hours_ago in entries:
            self.activity_log.append(ActivityEntry(
                timestamp=now - timedelta(hours=hours_ago),
                agent_id=agent_id,
                action=action,
                target=target,
            ))

    def get_tasks_by_status(self, status: TaskStatus) -> list[AgentTask]:
        return [t for t in self.tasks if t.status == status]

    def get_agent_live_count(self, agent_id: AgentID) -> int:
        return len([t for t in self.tasks
                    if t.agent_id == agent_id and t.status == TaskStatus.RUNNING])

    def get_filtered_tasks(self) -> list[AgentTask]:
        if self.filter_agent:
            return [t for t in self.tasks if t.agent_id == self.filter_agent]
        return self.tasks

    # -- Metrics --
    def get_metrics(self) -> list[Metric]:
        running = len(self.get_tasks_by_status(TaskStatus.RUNNING))
        completed = len(self.get_tasks_by_status(TaskStatus.COMPLETED))
        waiting = len(self.get_tasks_by_status(TaskStatus.WAITING))
        errors = len(self.get_tasks_by_status(TaskStatus.ERROR))
        blocked = len(self.get_tasks_by_status(TaskStatus.BLOCKED))
        active_agents = len(set(t.agent_id for t in self.tasks if t.status == TaskStatus.RUNNING))
        total_agents = len(set(t.agent_id for t in self.tasks))

        return [
            Metric("Agents Enabled", total_agents,
                   f"{active_agents} running, 0 paused, {errors} errors",
                   "smart_toy", Colors.BLUE),
            Metric("Tasks in Progress", running,
                   f"{waiting} open, {blocked} blocked",
                   "task_alt", Colors.GREEN),
            Metric("Completed", completed,
                   f"{completed}/{len(self.tasks)} total tasks",
                   "check_circle", Colors.GREEN),
            Metric("Month Spend", "$8.19",
                   "Unlimited Budget",
                   "payments", Colors.TEXT_PRIMARY),
        ]

    # -- Methodology --
    def get_methodology_value(self, agent_id: AgentID, param_key: str) -> Any:
        return self.methodologies.get(agent_id, {}).get(param_key, {}).get("value")

    def set_methodology_value(self, agent_id: AgentID, param_key: str, value: Any) -> None:
        if agent_id in self.methodologies and param_key in self.methodologies[agent_id]:
            self.methodologies[agent_id][param_key]["value"] = value

    # -- Chart Data --
    def get_run_activity_data(self) -> dict:
        """Data for the Run Activity stacked bar chart."""
        return {
            "categories": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "series": [
                {"name": "Completed", "data": [12, 8, 15, 10, 14, 6, 9], "color": Colors.BLACK},
                {"name": "Errors", "data": [1, 0, 2, 1, 0, 0, 1], "color": Colors.RED},
                {"name": "Running", "data": [3, 5, 4, 6, 3, 2, 4], "color": Colors.GREEN},
            ],
        }

    def get_issues_priority_data(self) -> dict:
        """Data for Issues by Priority chart."""
        return {
            "categories": ["High", "Medium", "Low"],
            "values": [4, 8, 3],
            "colors": [Colors.RED, Colors.AMBER, Colors.GREEN],
        }

    def get_issues_status_data(self) -> dict:
        """Data for Issues by Status chart."""
        return {
            "categories": ["Open", "In Progress", "Closed"],
            "values": [6, 5, 12],
            "colors": [Colors.TEXT_TERTIARY, Colors.AMBER, Colors.GREEN],
        }


# Global instance
state = DashboardState()
