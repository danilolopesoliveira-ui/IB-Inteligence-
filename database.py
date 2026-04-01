"""
SQLite persistence layer for IB-Agents.

Provides server-side state for operations, agent tasks, and agent-generated documents.
Replaces browser localStorage as the source of truth.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("./data/ib_agents.db")

_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS operations (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            type            TEXT NOT NULL,
            instrument      TEXT NOT NULL,
            company         TEXT NOT NULL,
            cnpj            TEXT DEFAULT '',
            sector          TEXT DEFAULT '',
            value           REAL DEFAULT 0,
            status          TEXT DEFAULT 'Em Estruturacao',
            stage           TEXT DEFAULT 'Etapa 1 — Revisao Documental',
            rating          TEXT DEFAULT '',
            priority        TEXT DEFAULT 'Media',
            deadline        TEXT DEFAULT '',
            guarantees      TEXT DEFAULT '[]',
            notes           TEXT DEFAULT '',
            paused          INTEGER DEFAULT 0,
            progress        INTEGER DEFAULT 0,
            opened_at       TEXT NOT NULL,
            client_docs     TEXT DEFAULT '[]',
            pending_docs    TEXT DEFAULT '[]',
            selected_docs   TEXT DEFAULT '[]',
            additional_request TEXT DEFAULT '',
            agents_config   TEXT DEFAULT '[]',
            created_at      TEXT,
            updated_at      TEXT
        );

        CREATE TABLE IF NOT EXISTS agent_tasks (
            id              TEXT PRIMARY KEY,
            operation_id    TEXT NOT NULL,
            agent_id        TEXT NOT NULL,
            title           TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'queued',
            column_name     TEXT DEFAULT 'Backlog',
            difficulty      INTEGER DEFAULT 3,
            hours_elapsed   REAL DEFAULT 0,
            max_hours       REAL DEFAULT 16,
            log             TEXT DEFAULT '[]',
            result_text     TEXT,
            error_message   TEXT,
            attempt_count   INTEGER DEFAULT 0,
            started_at      TEXT,
            completed_at    TEXT,
            created_at      TEXT,
            updated_at      TEXT,
            FOREIGN KEY (operation_id) REFERENCES operations(id)
        );
        CREATE INDEX IF NOT EXISTS idx_tasks_operation ON agent_tasks(operation_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON agent_tasks(status);

        CREATE TABLE IF NOT EXISTS agent_docs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_id    TEXT NOT NULL,
            agent_id        TEXT NOT NULL,
            name            TEXT NOT NULL,
            status          TEXT DEFAULT 'rascunho',
            version         TEXT DEFAULT 'v1.0',
            content_ref     TEXT,
            date            TEXT,
            created_at      TEXT,
            updated_at      TEXT,
            FOREIGN KEY (operation_id) REFERENCES operations(id)
        );
        CREATE INDEX IF NOT EXISTS idx_docs_operation ON agent_docs(operation_id);
    """)
    conn.commit()
    conn.close()


# ── Operations CRUD ──────────────────────────────────────────────────────────

_OP_JSON_FIELDS = {"guarantees", "client_docs", "pending_docs", "selected_docs", "agents_config"}


def _serialize_op(data: dict) -> dict:
    """Convert Python lists/dicts to JSON strings for JSON columns."""
    out = dict(data)
    for k in _OP_JSON_FIELDS:
        if k in out and not isinstance(out[k], str):
            out[k] = json.dumps(out[k], ensure_ascii=False)
    out.setdefault("created_at", _now())
    out["updated_at"] = _now()
    # Map frontend field names to DB column names
    if "openedAt" in out and "opened_at" not in out:
        out["opened_at"] = out.pop("openedAt")
    if "pendingDocs" in out and "pending_docs" not in out:
        out["pending_docs"] = json.dumps(out.pop("pendingDocs"), ensure_ascii=False) if not isinstance(out.get("pendingDocs"), str) else out.pop("pendingDocs")
    if "clientDocs" in out and "client_docs" not in out:
        out["client_docs"] = json.dumps(out.pop("clientDocs"), ensure_ascii=False) if not isinstance(out.get("clientDocs"), str) else out.pop("clientDocs")
    if "selectedDocs" in out and "selected_docs" not in out:
        out["selected_docs"] = json.dumps(out.pop("selectedDocs"), ensure_ascii=False) if not isinstance(out.get("selectedDocs"), str) else out.pop("selectedDocs")
    if "additionalRequest" in out and "additional_request" not in out:
        out["additional_request"] = out.pop("additionalRequest")
    # Remove keys not in the table
    valid_cols = {
        "id", "name", "type", "instrument", "company", "cnpj", "sector", "value",
        "status", "stage", "rating", "priority", "deadline", "guarantees", "notes",
        "paused", "progress", "opened_at", "client_docs", "pending_docs",
        "selected_docs", "additional_request", "agents_config", "created_at", "updated_at",
    }
    return {k: v for k, v in out.items() if k in valid_cols}


def _deserialize_op(row: sqlite3.Row) -> dict:
    """Convert a DB row to a dict with JSON fields parsed."""
    d = dict(row)
    for k in _OP_JSON_FIELDS:
        if k in d and isinstance(d[k], str):
            try:
                d[k] = json.loads(d[k])
            except (json.JSONDecodeError, TypeError):
                pass
    d["paused"] = bool(d.get("paused", 0))
    # Map back to frontend camelCase
    d["openedAt"] = d.pop("opened_at", "")
    d["pendingDocs"] = d.pop("pending_docs", [])
    d["clientDocs"] = d.pop("client_docs", [])
    d["selectedDocs"] = d.pop("selected_docs", [])
    d["additionalRequest"] = d.pop("additional_request", "")
    d["agentsConfig"] = d.pop("agents_config", [])
    return d


def save_operation(op: dict):
    data = _serialize_op(op)
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    updates = ", ".join(f"{k}=excluded.{k}" for k in data if k != "id")
    with _lock:
        conn = get_connection()
        conn.execute(
            f"INSERT INTO operations ({cols}) VALUES ({placeholders}) ON CONFLICT(id) DO UPDATE SET {updates}",
            list(data.values()),
        )
        conn.commit()
        conn.close()


def get_operation(op_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM operations WHERE id = ?", (op_id,)).fetchone()
    conn.close()
    return _deserialize_op(row) if row else None


def list_operations() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM operations ORDER BY created_at DESC").fetchall()
    conn.close()
    return [_deserialize_op(r) for r in rows]


def update_operation(op_id: str, updates: dict):
    data = _serialize_op({**updates, "id": op_id})
    data.pop("id", None)
    data.pop("created_at", None)
    if not data:
        return
    sets = ", ".join(f"{k} = ?" for k in data)
    with _lock:
        conn = get_connection()
        conn.execute(f"UPDATE operations SET {sets} WHERE id = ?", [*data.values(), op_id])
        conn.commit()
        conn.close()


# ── Agent Tasks CRUD ─────────────────────────────────────────────────────────

_TASK_JSON_FIELDS = {"log"}


def _serialize_task(data: dict) -> dict:
    out = dict(data)
    for k in _TASK_JSON_FIELDS:
        if k in out and not isinstance(out[k], str):
            out[k] = json.dumps(out[k], ensure_ascii=False)
    out.setdefault("created_at", _now())
    out["updated_at"] = _now()
    # Map frontend names
    if "operation" in out and "operation_id" not in out:
        out["operation_id"] = out.pop("operation")
    if "agent" in out and "agent_id" not in out:
        out["agent_id"] = out.pop("agent")
    if "column" in out and "column_name" not in out:
        out["column_name"] = out.pop("column")
    if "hoursElapsed" in out and "hours_elapsed" not in out:
        out["hours_elapsed"] = out.pop("hoursElapsed")
    if "maxHours" in out and "max_hours" not in out:
        out["max_hours"] = out.pop("maxHours")
    valid_cols = {
        "id", "operation_id", "agent_id", "title", "status", "column_name",
        "difficulty", "hours_elapsed", "max_hours", "log", "result_text",
        "error_message", "attempt_count", "started_at", "completed_at",
        "created_at", "updated_at",
    }
    return {k: v for k, v in out.items() if k in valid_cols}


def _deserialize_task(row: sqlite3.Row) -> dict:
    d = dict(row)
    for k in _TASK_JSON_FIELDS:
        if k in d and isinstance(d[k], str):
            try:
                d[k] = json.loads(d[k])
            except (json.JSONDecodeError, TypeError):
                pass
    # Map back to frontend names
    d["operation"] = d.pop("operation_id", "")
    d["agent"] = d.pop("agent_id", "")
    d["column"] = d.pop("column_name", "Backlog")
    d["hoursElapsed"] = d.pop("hours_elapsed", 0)
    d["maxHours"] = d.pop("max_hours", 16)
    return d


def save_task(task: dict):
    data = _serialize_task(task)
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    updates = ", ".join(f"{k}=excluded.{k}" for k in data if k != "id")
    with _lock:
        conn = get_connection()
        conn.execute(
            f"INSERT INTO agent_tasks ({cols}) VALUES ({placeholders}) ON CONFLICT(id) DO UPDATE SET {updates}",
            list(data.values()),
        )
        conn.commit()
        conn.close()


def get_task(task_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM agent_tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return _deserialize_task(row) if row else None


def list_tasks(operation_id: str | None = None, status: str | None = None) -> list[dict]:
    conn = get_connection()
    query = "SELECT * FROM agent_tasks WHERE 1=1"
    params: list = []
    if operation_id:
        query += " AND operation_id = ?"
        params.append(operation_id)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [_deserialize_task(r) for r in rows]


def update_task(task_id: str, updates: dict):
    data = _serialize_task({**updates, "id": task_id})
    data.pop("id", None)
    data.pop("created_at", None)
    if not data:
        return
    sets = ", ".join(f"{k} = ?" for k in data)
    with _lock:
        conn = get_connection()
        conn.execute(f"UPDATE agent_tasks SET {sets} WHERE id = ?", [*data.values(), task_id])
        conn.commit()
        conn.close()


def get_interrupted_tasks() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM agent_tasks WHERE status = 'running'").fetchall()
    conn.close()
    return [_deserialize_task(r) for r in rows]


def recover_interrupted_tasks() -> list[dict]:
    """Find tasks stuck as 'running' (server crashed mid-execution) and re-queue them."""
    interrupted = get_interrupted_tasks()
    if interrupted:
        with _lock:
            conn = get_connection()
            conn.execute(
                "UPDATE agent_tasks SET status = 'queued', "
                "attempt_count = attempt_count + 1, "
                "updated_at = ? "
                "WHERE status = 'running'",
                (_now(),),
            )
            conn.commit()
            conn.close()
    return interrupted


# ── Agent Docs CRUD ──────────────────────────────────────────────────────────

def save_agent_doc(doc: dict) -> int:
    data = dict(doc)
    data.setdefault("created_at", _now())
    data["updated_at"] = _now()
    # Map frontend names
    if "opId" in data and "operation_id" not in data:
        data["operation_id"] = data.pop("opId")
    if "agent" in data and "agent_id" not in data:
        data["agent_id"] = data.pop("agent")
    valid_cols = {
        "operation_id", "agent_id", "name", "status", "version",
        "content_ref", "date", "created_at", "updated_at",
    }
    data = {k: v for k, v in data.items() if k in valid_cols}
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    with _lock:
        conn = get_connection()
        # Upsert: if same operation+agent exists, update instead of duplicating
        existing = conn.execute(
            "SELECT id FROM agent_docs WHERE operation_id = ? AND agent_id = ?",
            (data.get("operation_id", ""), data.get("agent_id", "")),
        ).fetchone()
        if existing:
            doc_id = existing["id"]
            sets = ", ".join(f"{k} = ?" for k in data)
            conn.execute(f"UPDATE agent_docs SET {sets} WHERE id = ?", [*data.values(), doc_id])
        else:
            cursor = conn.execute(f"INSERT INTO agent_docs ({cols}) VALUES ({placeholders})", list(data.values()))
            doc_id = cursor.lastrowid
        conn.commit()
        conn.close()
    return doc_id


def list_agent_docs(operation_id: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM agent_docs WHERE operation_id = ? ORDER BY created_at ASC",
        (operation_id,),
    ).fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        d["agent"] = d.pop("agent_id", "")
        d["opId"] = d.pop("operation_id", "")
        results.append(d)
    return results


def update_agent_doc(doc_id: int, updates: dict):
    data = dict(updates)
    data["updated_at"] = _now()
    valid = {"name", "status", "version", "content_ref", "date", "updated_at"}
    data = {k: v for k, v in data.items() if k in valid}
    if not data:
        return
    sets = ", ".join(f"{k} = ?" for k in data)
    with _lock:
        conn = get_connection()
        conn.execute(f"UPDATE agent_docs SET {sets} WHERE id = ?", [*data.values(), doc_id])
        conn.commit()
        conn.close()


# ── Agent timing stats ───────────────────────────────────────────────────────

def get_agent_timing_stats() -> dict:
    """Return execution time stats per agent based on completed tasks."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT agent_id, started_at, completed_at FROM agent_tasks "
        "WHERE status = 'completed' AND started_at IS NOT NULL AND completed_at IS NOT NULL"
    ).fetchall()
    conn.close()

    from collections import defaultdict
    stats: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        try:
            start = datetime.fromisoformat(r["started_at"])
            end = datetime.fromisoformat(r["completed_at"])
            seconds = (end - start).total_seconds()
            if seconds > 0:
                stats[r["agent_id"]].append(seconds)
        except (ValueError, TypeError):
            continue

    result = {}
    for agent_id, times in stats.items():
        avg = sum(times) / len(times)
        result[agent_id] = {
            "avg_seconds": round(avg, 1),
            "min_seconds": round(min(times), 1),
            "max_seconds": round(max(times), 1),
            "executions": len(times),
        }
    return result


# ── Bulk state endpoint helper ───────────────────────────────────────────────

def get_full_state() -> dict:
    """Return all operations, tasks, and agent docs for frontend hydration."""
    ops = list_operations()
    tasks_list = list_tasks()
    # Attach agent_docs to each operation
    for op in ops:
        op["agentDocs"] = list_agent_docs(op["id"])
    return {
        "operations": ops,
        "tasks": tasks_list,
    }
