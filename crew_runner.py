"""
Bridge between the NiceGUI Dashboard and the CrewAI pipeline.
Integrates with cost_tracker for real-time cost tracking.
"""

from __future__ import annotations

import asyncio
import os
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import partial
from typing import Any, Callable

from loguru import logger

from dashboard_state import (
    AGENT_CONFIG,
    AgentID,
    DashboardState,
    TaskStatus,
)
from cost_tracker import tracker

_executor = ThreadPoolExecutor(max_workers=1)

_TASK_AGENT_ROLES = [
    ("Research Analyst", "SOP-1"),
    ("Accountant", "SOP-2"),
    ("Financial Modeler", "SOP-3"),
    ("Quant Analyst", "SOP-4"),
    ("Risk & Compliance", "SOP-5"),
    ("Deck Builder", "SOP-6"),
    ("Managing Director", "SOP-7"),
]


def _build_input_data(state):
    if state.use_demo:
        from main import _generate_demo_data
        return _generate_demo_data(state.company_name or "Demo Industria S.A.", state.sector)
    return {"file_path": state.uploaded_file_path, "company": state.company_name}


def _inject_methodology(state):
    config = {}
    for agent_id, params in state.methodologies.items():
        for key, param in params.items():
            config[f"{agent_id.value}__{key}"] = param.get("value")
    return config


def _run_crew_sync(state):
    from crew import IBAnalysisCrew

    company = state.company_name or "Demo Industria S.A."
    for key, value in _inject_methodology(state).items():
        os.environ[f"IB_{key.upper()}"] = str(value)

    tracker.start_session(name=f"Analise {company}", operation_id=state.deal_type)

    crew = IBAnalysisCrew(
        company_name=company,
        deal_type=state.deal_type,
        sector=state.sector,
        input_data=_build_input_data(state),
        mode="full_analysis",
    )
    result = crew.run()
    tracker.end_session()
    return result


async def execute_pipeline(state, refresh_fn):
    loop = asyncio.get_event_loop()
    state.log(AgentID.ORCHESTRATOR, "started", "Inicializando pipeline CrewAI...")

    for task in state.tasks:
        task.status = TaskStatus.WAITING
        task.progress = 0
    refresh_fn()

    async def update_task_progress(idx):
        if idx >= len(state.tasks):
            return
        task = state.tasks[idx]
        if idx < len(_TASK_AGENT_ROLES):
            role, sop = _TASK_AGENT_ROLES[idx]
            tracker.set_current_context(agent_role=role, task_sop=sop, operation_id=state.deal_type)
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        task.progress = 0
        state.log(task.agent_id, "started", f"{task.sop_id} - {task.title}")
        refresh_fn()
        for p in range(0, 90, 15):
            task.progress = p
            refresh_fn()
            await asyncio.sleep(2)

    progress_task = asyncio.create_task(update_task_progress(0))

    try:
        result = await loop.run_in_executor(_executor, partial(_run_crew_sync, state))
        progress_task.cancel()
        for task in state.tasks:
            task.status = TaskStatus.COMPLETED
            task.finished_at = datetime.now()
            task.progress = 100
            state.log(task.agent_id, "completed", f"{task.sop_id} - {task.title}")
        state.is_running = False
        summary = tracker.get_session_summary()
        state.log(AgentID.ORCHESTRATOR, "completed",
                  f"Pipeline concluido — Custo: R$ {summary.get('total_cost_brl', 0):.2f}")
        refresh_fn()
        return result
    except Exception as exc:
        progress_task.cancel()
        logger.error(f"Pipeline error: {traceback.format_exc()}")
        tracker.end_session()
        for task in state.tasks:
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.ERROR
                task.finished_at = datetime.now()
                task.result_summary = str(exc)[:100]
        state.is_running = False
        state.log(AgentID.ORCHESTRATOR, "error", f"Erro no pipeline: {exc}")
        refresh_fn()
        raise
