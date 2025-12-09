"""MCP server exposing unrestricted Postgres access via the .env connection string.

This server:
- loads POSTGRESS_CONNECTION (or POSTGRES_CONNECTION) from the .env file
- opens a psycopg connection
- exposes a single MCP tool `run_sql` that executes arbitrary SQL

The intent is to be used from an MCP-compatible client (e.g., Claude Desktop)
that wants to let the agent issue raw SQL statements.
"""

from __future__ import annotations

import os
from typing import Sequence

from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

try:
    from mcp.server.fastmcp import FastMCP
except Exception as exc:  # pragma: no cover - optional dependency
    raise SystemExit(
        "The 'mcp' package is required to run this server. "
        "Install with `pip install mcp` (or the MCP Python SDK)."
    ) from exc

# Load local .env so the server can find the connection string when run directly.
load_dotenv()

DB_URL = os.getenv("POSTGRESS_CONNECTION") or os.getenv("POSTGRES_CONNECTION")
if not DB_URL:
    raise SystemExit(
        "Missing POSTGRESS_CONNECTION (or POSTGRES_CONNECTION) in .env; "
        "add your Postgres connection string before running the MCP server."
    )

mcp = FastMCP("postgres-db")


def _format_rows(columns: Sequence[str], rows: Sequence[dict], extra_count: int) -> str:
    header = " | ".join(columns)
    divider = "-" * max(len(header), 40)
    lines = [header, divider]

    for row in rows:
        lines.append(" | ".join(str(row.get(col)) for col in columns))

    if extra_count > 0:
        lines.append(f"... +{extra_count} more rows")

    return "\n".join(lines)


@mcp.tool(description="Run arbitrary SQL against the configured Postgres database")
def run_sql(sql: str, limit: int = 200) -> str:
    """Execute any SQL statement using the connection string from .env."""
    if not sql or not sql.strip():
        return "SQL cannot be empty."

    limit = max(1, min(limit, 1000))

    try:
        with psycopg.connect(DB_URL, autocommit=True) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql)

                if cur.description:
                    columns = [col.name for col in cur.description]
                    fetched = cur.fetchmany(limit + 1)
                    rows = fetched[:limit]
                    extra = max(len(fetched) - limit, 0)
                    return _format_rows(columns, rows, extra)

                affected = cur.rowcount
                affected_text = (
                    f"{affected} row(s) affected"
                    if affected is not None and affected >= 0
                    else "statement executed"
                )
                return f"✓ {affected_text}"
    except Exception as exc:  # pragma: no cover - surfaced to client
        return f"Database error: {exc}"


if __name__ == "__main__":
    # Default to stdio transport for MCP clients (e.g., Claude Desktop).
    mcp.run()

