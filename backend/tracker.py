"""
BuildReady-AI Usage Tracker
============================
Records REAL Gemini API usage to a local SQLite database.

- No fake/sample data is ever written.
- Every record is created only when a real Gemini API call completes or fails.
- Token values come directly from response.usage_metadata where available.
- The database survives backend restarts (file-based SQLite).
- The founder dashboard reads directly from this database.
"""
import sqlite3
import logging
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Database file lives in the backend directory alongside main.py
# On Render this is part of the ephemeral filesystem. For persistent storage
# on Render you would mount a persistent disk and point DB_PATH there.
_BASE = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("USAGE_DB_PATH", str(_BASE / "usage.db")))


def _connect() -> sqlite3.Connection:
    """Open a SQLite connection with foreign-keys enabled and row_factory set."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # safe for concurrent reads
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def _db():
    """Context manager that auto-commits or rolls back."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Create the usage table if it does not already exist.
    Called once at startup from main.py.
    This never inserts seed/demo data.
    """
    with _db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usage_events (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       TEXT    NOT NULL,
                timestamp     TEXT    NOT NULL,
                feature       TEXT    NOT NULL,
                input_tokens  INTEGER NOT NULL DEFAULT 0,
                output_tokens INTEGER NOT NULL DEFAULT 0,
                total_tokens  INTEGER NOT NULL DEFAULT 0,
                success       INTEGER NOT NULL DEFAULT 1,
                model_used    TEXT    DEFAULT '',
                notes         TEXT    DEFAULT ''
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_id  ON usage_events (user_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON usage_events (timestamp)"
        )
    logger.info("Usage tracker database ready at %s", DB_PATH)


def record_usage(
    *,
    user_id: str,
    feature: str,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
    success: bool,
    model_used: str = "",
    notes: str = "",
) -> None:
    """
    Insert one real usage event.
    Called only after a real Gemini API call (success OR failure).
    Token values must come from response.usage_metadata, NOT invented.
    """
    ts = datetime.now(timezone.utc).isoformat()
    try:
        with _db() as conn:
            conn.execute(
                """
                INSERT INTO usage_events
                    (user_id, timestamp, feature, input_tokens, output_tokens,
                     total_tokens, success, model_used, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    ts,
                    feature,
                    max(0, input_tokens),
                    max(0, output_tokens),
                    max(0, total_tokens),
                    1 if success else 0,
                    model_used,
                    notes,
                ),
            )
    except Exception as exc:
        # Never let tracker errors break the student experience
        logger.error("Usage tracker failed to record event: %s", exc)


# ---------------------------------------------------------------------------
# Query helpers used by the founder dashboard endpoints
# ---------------------------------------------------------------------------

def _period_filter(period: str) -> str:
    """Return a SQL WHERE fragment for the requested time period."""
    if period == "today":
        return "DATE(timestamp) = DATE('now')"
    if period == "7d":
        return "timestamp >= DATETIME('now', '-7 days')"
    if period == "30d":
        return "timestamp >= DATETIME('now', '-30 days')"
    return "1=1"   # all time


def get_summary(period: str = "all") -> dict:
    """
    Return aggregate statistics for the requested period.
    All values are calculated from real database records.
    Returns zeros (not fake data) when the database is empty.
    """
    where = _period_filter(period)
    with _db() as conn:
        row = conn.execute(f"""
            SELECT
                COUNT(DISTINCT user_id)   AS total_users,
                COUNT(*)                  AS total_requests,
                SUM(input_tokens)         AS input_tokens,
                SUM(output_tokens)        AS output_tokens,
                SUM(total_tokens)         AS total_tokens,
                SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) AS successful,
                SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) AS failed
            FROM usage_events
            WHERE {where}
        """).fetchone()

        total_users    = row["total_users"]    or 0
        total_requests = row["total_requests"] or 0
        input_tokens   = row["input_tokens"]   or 0
        output_tokens  = row["output_tokens"]  or 0
        total_tokens   = row["total_tokens"]   or 0
        successful     = row["successful"]     or 0
        failed         = row["failed"]         or 0

        avg_per_user    = round(total_tokens / total_users,    1) if total_users    > 0 else 0
        avg_per_request = round(total_tokens / total_requests, 1) if total_requests > 0 else 0

        # Highest and lowest usage users (by total_tokens)
        top_users = conn.execute(f"""
            SELECT user_id, SUM(total_tokens) AS tok
            FROM usage_events
            WHERE {where}
            GROUP BY user_id
            ORDER BY tok DESC
        """).fetchall()

        highest_user = {"user_id": top_users[0]["user_id"], "total_tokens": top_users[0]["tok"]} if top_users else None
        lowest_user  = {"user_id": top_users[-1]["user_id"], "total_tokens": top_users[-1]["tok"]} if top_users else None

    return {
        "period":           period,
        "total_users":      total_users,
        "total_requests":   total_requests,
        "input_tokens":     input_tokens,
        "output_tokens":    output_tokens,
        "total_tokens":     total_tokens,
        "successful":       successful,
        "failed":           failed,
        "avg_tokens_per_user":    avg_per_user,
        "avg_tokens_per_request": avg_per_request,
        "highest_usage_user":     highest_user,
        "lowest_usage_user":      lowest_user,
    }


def get_per_user_stats(period: str = "all") -> list[dict]:
    """
    Return per-user aggregates for the requested period.
    Returns an empty list (not fake users) when no data has been recorded.
    """
    where = _period_filter(period)
    with _db() as conn:
        rows = conn.execute(f"""
            SELECT
                user_id,
                COUNT(*)             AS requests,
                SUM(input_tokens)    AS input_tokens,
                SUM(output_tokens)   AS output_tokens,
                SUM(total_tokens)    AS total_tokens,
                MAX(timestamp)       AS last_active
            FROM usage_events
            WHERE {where}
            GROUP BY user_id
            ORDER BY total_tokens DESC
        """).fetchall()
    return [dict(r) for r in rows]


def get_recent_events(limit: int = 50) -> list[dict]:
    """Return the most recent raw usage events for the founder."""
    with _db() as conn:
        rows = conn.execute("""
            SELECT id, user_id, timestamp, feature, input_tokens, output_tokens,
                   total_tokens, success, model_used, notes
            FROM usage_events
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]
