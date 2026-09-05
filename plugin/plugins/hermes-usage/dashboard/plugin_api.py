"""Hermes Usage — persistent token-usage backend (reads Hermes' own state.db).

A FastAPI router mounted at /api/plugins/hermes-usage/* by the dashboard/desktop
plugin system. It is the server-side half of a "dsh-token-usage"-style local
observability tool: it reads the SAME usage data Hermes already persists in
state.db (sessions + session_model_usage) and returns dsh-style aggregations —
totals, per provider/model, per session, daily trend, cache structure and
estimated cost. It never writes to the DB and never touches model history.

Env override for testing only: set HERMES_USAGE_DB to a state.db path
(e.g. a backup snapshot) to point the queries at a copy.
"""

from __future__ import annotations

import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

# Map of UTC date ranges over which cache_read/cache_write are authoritative.
# Cache fields are only summed when the source row populated them (see queries).

_UTC_DAY = 86400.0


def _resolve_db_path() -> Path:
    override = os.environ.get("HERMES_USAGE_DB")
    if override:
        return Path(override)
    home = os.environ.get("HERMES_HOME")
    if not home:
        try:
            from hermes_constants import get_process_hermes_home

            home = str(get_process_hermes_home())
        except Exception:
            home = None
    if not home:
        home = str(Path.home() / ".hermes")
    return Path(home) / "state.db"


def _connect(db_path: Path) -> sqlite3.Connection:
    """Read-only connection; degrades to immutable (no WAL) on lock errors."""
    uri = f"file:{db_path.as_posix()}?mode=ro"
    try:
        return sqlite3.connect(uri, uri=True, timeout=5)
    except sqlite3.Error:
        pass
    try:
        return sqlite3.connect(uri + "&immutable=1", uri=True, timeout=5)
    except sqlite3.Error:
        # Last resort: normal read-write open (safe for SELECTs in WAL mode).
        return sqlite3.connect(str(db_path), timeout=5)


def _f(v):
    return None if v is None else float(v)


def _now_utc_day() -> int:
    return int(time.time()) // 86400


@router.get("/health")
async def health():
    return {"ok": True, "db": str(_resolve_db_path())}


@router.get("/session_models")
async def session_models(session_id: str = ""):
    """Per-model usage breakdown for one session (session_id = durable session id)."""
    if not session_id:
        return {"ok": False, "error": "missing session_id query param"}
    db = _resolve_db_path()
    if not db.exists():
        return {"ok": False, "error": f"state.db not found at {db}"}
    conn = _connect(db)
    conn.row_factory = sqlite3.Row
    try:
        rows = [
            dict(r)
            for r in conn.execute(
                "select billing_provider as provider, model, "
                "sum(api_call_count) as calls, "
                "sum(input_tokens) as input, sum(output_tokens) as output, "
                "sum(cache_read_tokens) as cache_read, sum(cache_write_tokens) as cache_write, "
                "sum(reasoning_tokens) as reasoning, "
                "round(sum(coalesce(estimated_cost_usd, actual_cost_usd, 0)), 6) as est_usd "
                "from session_model_usage where session_id = ? "
                "group by billing_provider, model "
                "order by (sum(input_tokens)+sum(output_tokens)+sum(cache_read_tokens)+sum(cache_write_tokens)) desc",
                (session_id,),
            ).fetchall()
        ]
        for row in rows:
            t = (row.get("input") or 0) + (row.get("output") or 0)
            cr = row.get("cache_read") or 0
            row["total"] = t + cr + (row.get("cache_write") or 0)
            if row.get("est_usd") is not None:
                row["est_usd"] = round(row["est_usd"], 6)
        return {"ok": True, "session_id": session_id, "models": rows}
    finally:
        conn.close()


@router.get("/overview")
async def overview():
    db = _resolve_db_path()
    if not db.exists():
        return {
            "ok": False,
            "error": f"state.db not found at {db}",
            "meta": {},
            "totals": {},
            "per_model": [],
            "per_session": [],
            "daily": [],
        }
    conn = _connect(db)
    conn.row_factory = sqlite3.Row
    try:
        meta = dict(conn.execute(
            "select count(*) as api_calls, count(distinct session_id) as sessions, "
            "count(distinct model) as models, "
            "min(first_seen) as first_seen, max(last_seen) as last_seen "
            "from session_model_usage"
        ).fetchone())

        totals = dict(conn.execute(
            "select coalesce(sum(input_tokens),0) as input, "
            "coalesce(sum(output_tokens),0) as output, "
            "coalesce(sum(cache_read_tokens),0) as cache_read, "
            "coalesce(sum(cache_write_tokens),0) as cache_write, "
            "coalesce(sum(reasoning_tokens),0) as reasoning, "
            "coalesce(sum(api_call_count),0) as api_calls "
            "from session_model_usage"
        ).fetchone())

        # Estimated cost across the whole table (estimated where present, else actual).
        cost = conn.execute(
            "select coalesce(sum(coalesce(estimated_cost_usd, actual_cost_usd, 0)),0) as est_usd, "
            "count(*) filter (where estimated_cost_usd is not null and estimated_cost_usd > 0) as est_rows, "
            "count(*) filter (where actual_cost_usd is not null and actual_cost_usd > 0) as act_rows "
            "from session_model_usage"
        ).fetchone()
        meta["est_rows"] = cost["est_rows"]
        meta["act_rows"] = cost["act_rows"]
        meta["est_usd"] = round(_f(cost["est_usd"]) or 0.0, 6)

        tin = totals["input"] or 0
        cache_read = totals["cache_read"] or 0
        totals["total"] = tin + (totals["output"] or 0) + cache_read + (totals["cache_write"] or 0)
        totals["cache_share_of_input"] = round(cache_read / tin, 4) if tin else None
        totals["est_usd"] = meta["est_usd"]

        per_model = [
            dict(r)
            for r in conn.execute(
                "select billing_provider as provider, model, count(*) as calls, "
                "sum(input_tokens) as input, sum(output_tokens) as output, "
                "sum(cache_read_tokens) as cache_read, sum(cache_write_tokens) as cache_write, "
                "sum(reasoning_tokens) as reasoning, "
                "round(sum(coalesce(estimated_cost_usd, actual_cost_usd, 0)), 6) as est_usd "
                "from session_model_usage group by billing_provider, model "
                "order by (sum(input_tokens)+sum(output_tokens)+sum(cache_read_tokens)+sum(cache_write_tokens)) desc"
            ).fetchall()
        ]
        for row in per_model:
            t = (row.get("input") or 0) + (row.get("output") or 0)
            cr = row.get("cache_read") or 0
            row["total"] = t + cr + (row.get("cache_write") or 0)
            row["cache_share_of_input"] = round(cr / (row.get("input") or 0), 4) if row.get("input") else None
            if row.get("est_usd") is not None:
                row["est_usd"] = round(row["est_usd"], 6)

        per_session = [
            dict(r)
            for r in conn.execute(
                "select u.session_id, coalesce(s.title, s.display_name, substr(s.session_key,1,60), u.session_id) as title, "
                "s.started_at, s.last_activity_at, u.model, u.billing_provider as provider, "
                "sum(u.input_tokens) as input, sum(u.output_tokens) as output, "
                "sum(u.cache_read_tokens) as cache_read, sum(u.cache_write_tokens) as cache_write, "
                "sum(u.reasoning_tokens) as reasoning, sum(u.api_call_count) as calls, "
                "round(sum(coalesce(u.estimated_cost_usd, u.actual_cost_usd, 0)), 6) as est_usd "
                "from session_model_usage u left join sessions s on s.id = u.session_id "
                "group by u.session_id order by (sum(u.input_tokens)+sum(u.output_tokens)+"
                "sum(u.cache_read_tokens)+sum(u.cache_write_tokens)) desc limit 30"
            ).fetchall()
        ]
        for row in per_session:
            t = (row.get("input") or 0) + (row.get("output") or 0)
            cr = row.get("cache_read") or 0
            row["total"] = t + cr + (row.get("cache_write") or 0)

        # Daily trend over the last N complete-ish UTC days, bucketed by first_seen.
        n_days = 30
        start = _now_utc_day() - (n_days - 1)
        rows = conn.execute(
            "select cast(first_seen / 86400.0 as int) as day, "
            "sum(input_tokens) as input, sum(output_tokens) as output, "
            "sum(cache_read_tokens) as cache_read, sum(cache_write_tokens) as cache_write, "
            "sum(reasoning_tokens) as reasoning, "
            "round(sum(coalesce(estimated_cost_usd, actual_cost_usd, 0)), 6) as est_usd "
            "from session_model_usage group by day"
        ).fetchall()
        by_day = {r["day"]: r for r in rows}
        daily = []
        for d in range(start, start + n_days):
            r = by_day.get(d)
            day_date = datetime.fromtimestamp(d * _UTC_DAY, tz=timezone.utc).strftime("%Y-%m-%d")
            if r is None:
                daily.append({"date": day_date, "day": d, "active": False})
                continue
            total = (r["input"] or 0) + (r["output"] or 0) + (r["cache_read"] or 0) + (r["cache_write"] or 0)
            daily.append({
                "date": day_date, "day": d, "active": True, "total": total,
                "input": r["input"] or 0, "output": r["output"] or 0,
                "cache_read": r["cache_read"] or 0, "cache_write": r["cache_write"] or 0,
                "reasoning": r["reasoning"] or 0,
                "est_usd": round(r["est_usd"] or 0, 6) if r["est_usd"] is not None else None,
            })

        return {
            "ok": True,
            "meta": meta,
            "totals": totals,
            "per_model": per_model,
            "per_session": per_session,
            "daily": daily,
        }
    finally:
        conn.close()
