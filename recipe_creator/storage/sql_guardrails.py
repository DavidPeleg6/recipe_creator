"""SQL validation and guardrails for agent-written queries."""

import re
from typing import Tuple

# Patterns that are FORBIDDEN (including DELETE - use soft delete instead)
FORBIDDEN_PATTERNS = [
    (r"\bDROP\s+", "DROP statements are not allowed"),
    (r"\bTRUNCATE\s+", "TRUNCATE statements are not allowed"),
    (r"\bALTER\s+", "ALTER statements are not allowed"),
    (r"\bCREATE\s+", "CREATE statements are not allowed"),
    (r"\bGRANT\s+", "GRANT statements are not allowed"),
    (r"\bREVOKE\s+", "REVOKE statements are not allowed"),
    (r"\bDELETE\s+", "DELETE not allowed - use UPDATE SET is_deleted = true"),
]


def validate_sql(query: str) -> Tuple[bool, str]:
    """
    Validate SQL query against guardrails.

    Args:
        query: SQL query to validate

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if query passes all guardrails
        - error_message: Empty string if valid, error description if invalid
    """
    query_upper = query.upper().strip()

    # Check forbidden patterns
    for pattern, error_msg in FORBIDDEN_PATTERNS:
        if re.search(pattern, query_upper, re.IGNORECASE):
            return False, error_msg

    # UPDATE must have WHERE clause
    if "UPDATE" in query_upper and "WHERE" not in query_upper:
        return False, "UPDATE statements must include a WHERE clause"

    return True, ""


def inject_soft_delete_filter(query: str) -> str:
    """
    Auto-inject is_deleted = false filter for SELECT queries.

    Transforms:
        SELECT * FROM saved_recipes WHERE name LIKE '%x%'
    To:
        SELECT * FROM saved_recipes WHERE is_deleted = false AND name LIKE '%x%'

    If the query already explicitly references is_deleted, no injection occurs.
    This allows the agent to query deleted recipes for un-delete operations:
        SELECT * FROM saved_recipes WHERE is_deleted = true  -- not modified

    Args:
        query: SQL query to process

    Returns:
        Query with is_deleted filter injected (for SELECT queries)
        Original query unchanged (for non-SELECT queries or explicit is_deleted)
    """
    if not query.strip().upper().startswith("SELECT"):
        return query

    query_upper = query.upper()

    # If agent explicitly references is_deleted, respect their intent (e.g., for un-delete)
    if "IS_DELETED" in query_upper:
        return query

    if "WHERE" in query_upper:
        # Insert after WHERE
        return re.sub(
            r"\bWHERE\b",
            "WHERE is_deleted = false AND ",
            query,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        # Insert WHERE before ORDER BY, LIMIT, GROUP BY, or at end
        # Check for common clauses that come after WHERE
        patterns = [
            (r"\bORDER\s+BY\b", r" WHERE is_deleted = false \g<0>"),
            (r"\bLIMIT\b", r" WHERE is_deleted = false \g<0>"),
            (r"\bGROUP\s+BY\b", r" WHERE is_deleted = false \g<0>"),
        ]

        for pattern, replacement in patterns:
            if re.search(pattern, query_upper):
                return re.sub(
                    pattern,
                    replacement,
                    query,
                    count=1,
                    flags=re.IGNORECASE,
                ).strip()

        # No ORDER BY, LIMIT, or GROUP BY - add at end
        return query.rstrip().rstrip(";") + " WHERE is_deleted = false"


def is_read_only(query: str) -> bool:
    """Check if query is read-only (SELECT).

    Args:
        query: SQL query to check

    Returns:
        True if query is a SELECT statement, False otherwise
    """
    return query.strip().upper().startswith("SELECT")

