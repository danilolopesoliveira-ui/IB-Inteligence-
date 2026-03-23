"""
Real-time cost tracker for IB-Agents pipeline.

Intercepts LLM API calls via CrewAI callbacks and litellm hooks,
captures token usage per agent/task, computes cost in USD and BRL,
and persists a complete history in a local JSON database.

Usage:
    from cost_tracker import tracker
    tracker.start_session("Analise Eneva S.A.")
    # ... run pipeline ...
    summary = tracker.get_session_summary()
"""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

# ---------------------------------------------------------------------------
# Pricing table — USD per 1M tokens (as of 2025)
# Update these when Anthropic / OpenAI change prices
# ---------------------------------------------------------------------------

MODEL_PRICING: dict[str, dict[str, float]] = {
    # Anthropic Claude
    "claude-opus-4-6":          {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-6":        {"input":  3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output":  4.00},
    # Fallback aliases used in CrewAI
    "anthropic/claude-opus-4-6":          {"input": 15.00, "output": 75.00},
    "anthropic/claude-sonnet-4-6":        {"input":  3.00, "output": 15.00},
    "anthropic/claude-haiku-4-5-20251001": {"input": 0.80, "output":  4.00},
    # OpenAI (if ever used)
    "gpt-4o":                   {"input":  2.50, "output": 10.00},
    "gpt-4o-mini":              {"input":  0.15, "output":  0.60},
}

DEFAULT_PRICING = {"input": 3.00, "output": 15.00}

# Map CrewAI agent roles to our agent IDs
ROLE_TO_AGENT_ID = {
    "managing director":   "md_orchestrator",
    "deal orchestrator":   "md_orchestrator",
    "orchestrator":        "md_orchestrator",
    "research analyst":    "research_analyst",
    "research":            "research_analyst",
    "accountant":          "accountant",
    "contador":            "accountant",
    "financial modeler":   "financial_modeler",
    "modelador":           "financial_modeler",
    "consolidat":          "financial_modeler",
    "quant analyst":       "quant_analyst",
    "quantitativo":        "quant_analyst",
    "comps":               "quant_analyst",
    "risk":                "risk_compliance",
    "compliance":          "risk_compliance",
    "covenant":            "risk_compliance",
    "deck builder":        "deck_builder",
    "output":              "deck_builder",
    "pptx":                "deck_builder",
    "dcm specialist":      "dcm_specialist",
    "debt capital":        "dcm_specialist",
    "bond":                "dcm_specialist",
    "debenture":           "dcm_specialist",
    "ecm specialist":      "ecm_specialist",
    "equity capital":      "ecm_specialist",
    "ipo":                 "ecm_specialist",
    "bookbuilding":        "ecm_specialist",
}


def _match_agent_id(role_str: str) -> str:
    """Best-effort mapping of CrewAI role string to dashboard agent ID."""
    lower = role_str.lower()
    for keyword, agent_id in ROLE_TO_AGENT_ID.items():
        if keyword in lower:
            return agent_id
    return "md_orchestrator"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class LLMCall:
    """Single LLM API call record."""
    timestamp: str
    agent_id: str
    agent_role: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    cost_brl: float
    duration_ms: int
    task_sop: str = ""
    operation_id: str = ""


@dataclass
class AgentCostSummary:
    """Aggregated cost for a single agent."""
    agent_id: str
    agent_name: str
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_cost_brl: float = 0.0
    total_duration_ms: int = 0

    @property
    def avg_cost_per_call_brl(self) -> float:
        return self.total_cost_brl / self.total_calls if self.total_calls else 0

    @property
    def hours_logged(self) -> float:
        return self.total_duration_ms / 3_600_000


@dataclass
class Session:
    """A pipeline execution session."""
    session_id: str
    name: str
    operation_id: str
    started_at: str
    finished_at: str | None = None
    calls: list[LLMCall] = field(default_factory=list)
    total_cost_usd: float = 0.0
    total_cost_brl: float = 0.0
    total_tokens: int = 0
    status: str = "running"


# ---------------------------------------------------------------------------
# CostTracker — the main class
# ---------------------------------------------------------------------------

DB_PATH = Path("./data/cost_history.json")


class CostTracker:
    """
    Singleton tracker that:
    1. Hooks into litellm callbacks to capture every LLM call
    2. Computes costs using the pricing table
    3. Persists all data to a local JSON file
    4. Exposes methods for the dashboard API
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._usd_to_brl: float = float(os.getenv("USD_BRL_RATE", "5.80"))
        self._sessions: list[Session] = []
        self._current_session: Session | None = None
        self._current_agent_role: str = ""
        self._current_task_sop: str = ""
        self._current_operation: str = ""
        self._load()
        self._install_hooks()

    # -- Persistence --------------------------------------------------------

    def _load(self) -> None:
        if DB_PATH.exists():
            try:
                data = json.loads(DB_PATH.read_text(encoding="utf-8"))
                self._sessions = []
                for s in data.get("sessions", []):
                    calls = [LLMCall(**c) for c in s.pop("calls", [])]
                    session = Session(**s, calls=calls)
                    self._sessions.append(session)
                self._usd_to_brl = data.get("usd_brl_rate", self._usd_to_brl)
            except Exception as exc:
                logger.warning(f"cost_tracker: failed to load history: {exc}")

    def _save(self) -> None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "usd_brl_rate": self._usd_to_brl,
            "sessions": [asdict(s) for s in self._sessions],
            "last_updated": datetime.now().isoformat(),
        }
        try:
            DB_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.error(f"cost_tracker: failed to save: {exc}")

    # -- litellm hooks (captures ALL LLM calls) ----------------------------

    def _install_hooks(self) -> None:
        """Install litellm success callback to capture token usage."""
        try:
            import litellm
            litellm.success_callback = [self._on_llm_success]
            logger.info("cost_tracker: litellm success callback installed")
        except ImportError:
            logger.info("cost_tracker: litellm not found — will use manual tracking")

    def _on_llm_success(self, kwargs: dict, completion_response: Any, start_time: float, end_time: float) -> None:
        """Called by litellm after every successful LLM completion."""
        try:
            model = kwargs.get("model", "unknown")
            usage = getattr(completion_response, "usage", None) or {}
            if hasattr(usage, "prompt_tokens"):
                input_tokens = usage.prompt_tokens
                output_tokens = usage.completion_tokens
            elif isinstance(usage, dict):
                input_tokens = usage.get("prompt_tokens", 0) or usage.get("input_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0) or usage.get("output_tokens", 0)
            else:
                input_tokens = 0
                output_tokens = 0

            duration_ms = int((end_time - start_time) * 1000) if isinstance(start_time, (int, float)) else 0

            self.record_call(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=duration_ms,
            )
        except Exception as exc:
            logger.debug(f"cost_tracker: callback error: {exc}")

    # -- Public API ---------------------------------------------------------

    def set_usd_brl(self, rate: float) -> None:
        """Update the USD→BRL exchange rate."""
        self._usd_to_brl = rate
        self._save()

    def start_session(self, name: str = "", operation_id: str = "") -> str:
        """Start a new tracking session (= one pipeline run)."""
        with self._lock:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            self._current_session = Session(
                session_id=session_id,
                name=name or f"Session {session_id}",
                operation_id=operation_id,
                started_at=datetime.now().isoformat(),
            )
            self._sessions.append(self._current_session)
            self._save()
            logger.info(f"cost_tracker: session started — {name}")
            return session_id

    def end_session(self) -> None:
        with self._lock:
            if self._current_session:
                self._current_session.finished_at = datetime.now().isoformat()
                self._current_session.status = "completed"
                self._save()
            self._current_session = None

    def set_current_context(self, agent_role: str = "", task_sop: str = "", operation_id: str = "") -> None:
        """Set the current agent/task context so calls are attributed correctly."""
        self._current_agent_role = agent_role
        self._current_task_sop = task_sop
        self._current_operation = operation_id

    def record_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: int = 0,
        agent_role: str = "",
        task_sop: str = "",
        operation_id: str = "",
    ) -> LLMCall:
        """Record a single LLM API call with cost computation."""
        role = agent_role or self._current_agent_role
        agent_id = _match_agent_id(role) if role else "md_senior"
        sop = task_sop or self._current_task_sop
        op = operation_id or self._current_operation

        # Compute cost
        pricing = MODEL_PRICING.get(model, DEFAULT_PRICING)
        cost_input = (input_tokens / 1_000_000) * pricing["input"]
        cost_output = (output_tokens / 1_000_000) * pricing["output"]
        cost_usd = cost_input + cost_output
        cost_brl = cost_usd * self._usd_to_brl

        call = LLMCall(
            timestamp=datetime.now().isoformat(),
            agent_id=agent_id,
            agent_role=role,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=round(cost_usd, 6),
            cost_brl=round(cost_brl, 4),
            duration_ms=duration_ms,
            task_sop=sop,
            operation_id=op,
        )

        with self._lock:
            if self._current_session:
                self._current_session.calls.append(call)
                self._current_session.total_cost_usd += cost_usd
                self._current_session.total_cost_brl += cost_brl
                self._current_session.total_tokens += call.total_tokens
            self._save()

        logger.debug(
            f"cost_tracker: {agent_id} | {model} | "
            f"{input_tokens}+{output_tokens} tokens | "
            f"R$ {cost_brl:.4f}"
        )
        return call

    # -- Query methods for dashboard ----------------------------------------

    def get_all_calls(self) -> list[dict]:
        """All recorded calls across all sessions."""
        calls = []
        for s in self._sessions:
            for c in s.calls:
                calls.append(asdict(c))
        return calls

    def get_cost_by_agent(self) -> list[dict]:
        """Aggregate costs per agent across all sessions."""
        agents: dict[str, AgentCostSummary] = {}
        agent_names = {
            "md_orchestrator": "MD Orchestrator",
            "research_analyst": "Research Analyst",
            "accountant": "Accountant / Contador",
            "financial_modeler": "Financial Modeler",
            "quant_analyst": "Quant Analyst",
            "risk_compliance": "Risk & Compliance",
            "deck_builder": "Deck Builder",
            "dcm_specialist": "DCM Specialist",
            "ecm_specialist": "ECM Specialist",
        }

        for s in self._sessions:
            for c in s.calls:
                if c.agent_id not in agents:
                    agents[c.agent_id] = AgentCostSummary(
                        agent_id=c.agent_id,
                        agent_name=agent_names.get(c.agent_id, c.agent_id),
                    )
                a = agents[c.agent_id]
                a.total_calls += 1
                a.total_input_tokens += c.input_tokens
                a.total_output_tokens += c.output_tokens
                a.total_tokens += c.total_tokens
                a.total_cost_usd += c.cost_usd
                a.total_cost_brl += c.cost_brl
                a.total_duration_ms += c.duration_ms

        return [
            {
                **asdict(a),
                "avg_cost_per_call_brl": round(a.avg_cost_per_call_brl, 4),
                "hours_logged": round(a.hours_logged, 2),
            }
            for a in sorted(agents.values(), key=lambda x: x.total_cost_brl, reverse=True)
        ]

    def get_cost_by_operation(self) -> list[dict]:
        """Aggregate costs per operation across all sessions."""
        ops: dict[str, dict] = {}
        for s in self._sessions:
            op_id = s.operation_id or s.session_id
            if op_id not in ops:
                ops[op_id] = {
                    "operation_id": op_id,
                    "name": s.name,
                    "total_cost_usd": 0,
                    "total_cost_brl": 0,
                    "total_tokens": 0,
                    "total_calls": 0,
                }
            for c in s.calls:
                ops[op_id]["total_cost_usd"] += c.cost_usd
                ops[op_id]["total_cost_brl"] += c.cost_brl
                ops[op_id]["total_tokens"] += c.total_tokens
                ops[op_id]["total_calls"] += 1
        return list(ops.values())

    def get_cost_timeline(self) -> list[dict]:
        """Daily cost aggregation for the timeline chart."""
        daily: dict[str, dict] = {}
        for s in self._sessions:
            for c in s.calls:
                day = c.timestamp[:10]
                if day not in daily:
                    daily[day] = {"date": day, "cost_brl": 0, "tokens": 0, "calls": 0}
                daily[day]["cost_brl"] += c.cost_brl
                daily[day]["tokens"] += c.total_tokens
                daily[day]["calls"] += 1
        return sorted(daily.values(), key=lambda x: x["date"])

    def get_session_summary(self) -> dict:
        """Summary of the current or most recent session."""
        s = self._current_session or (self._sessions[-1] if self._sessions else None)
        if not s:
            return {"status": "no_sessions", "total_cost_brl": 0}
        return {
            "session_id": s.session_id,
            "name": s.name,
            "status": s.status,
            "started_at": s.started_at,
            "finished_at": s.finished_at,
            "total_calls": len(s.calls),
            "total_tokens": s.total_tokens,
            "total_cost_usd": round(s.total_cost_usd, 4),
            "total_cost_brl": round(s.total_cost_brl, 2),
            "usd_brl_rate": self._usd_to_brl,
        }

    def get_dashboard_data(self) -> dict:
        """Complete data package for the frontend CostPanel."""
        return {
            "by_agent": self.get_cost_by_agent(),
            "by_operation": self.get_cost_by_operation(),
            "timeline": self.get_cost_timeline(),
            "current_session": self.get_session_summary(),
            "usd_brl_rate": self._usd_to_brl,
            "model_pricing": {k: v for k, v in MODEL_PRICING.items() if "/" not in k},
        }


# Singleton
tracker = CostTracker()
