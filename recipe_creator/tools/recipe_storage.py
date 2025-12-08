"""Tools for saving recipes and exploring the recipes database."""

from __future__ import annotations

import re
from typing import Any

from pydantic import ValidationError
from sqlalchemy import text

from models.db import SavedRecipeDB
from models.recipe import Recipe
from storage.database import AsyncSessionLocal

# Blocked SQL patterns to prevent destructive operations.
BLOCKED_SQL = [
    ("DELETE", r"\bDELETE\b"),
    ("DROP", r"\bDROP\b"),
    ("TRUNCATE", r"\bTRUNCATE\b"),
    ("CREATE TABLE", r"\bCREATE\s+TABLE\b"),
    ("ALTER", r"\bALTER\b"),
    ("INSERT", r"\bINSERT\b"),
]


async def save_recipe(
    name: str,
    recipe_type: str,
    ingredients: list[dict[str, Any]],
    instructions: list[str],
    prep_time_minutes: int | None = None,
    cook_time_minutes: int | None = None,
    servings: int | None = None,
    notes: str | None = None,
    user_notes: str | None = None,
    tags: list[str] | None = None,
    source_references: list[str] | None = None,
    conversation_id: str | None = None,
) -> str:
    """Save a recipe to the database. Requires HITL approval upstream."""
    try:
        payload = Recipe(
            name=name,
            recipe_type=recipe_type,
            ingredients=ingredients,
            instructions=instructions,
            prep_time_minutes=prep_time_minutes,
            cook_time_minutes=cook_time_minutes,
            servings=servings,
            notes=notes,
            user_notes=user_notes,
            tags=tags or [],
            source_references=source_references or [],
            conversation_id=conversation_id,
        )
    except ValidationError as exc:
        first_error = exc.errors()[0]
        field = ".".join(str(loc) for loc in first_error.get("loc", []) if loc is not None)
        msg = first_error.get("msg", "Invalid recipe input")
        prefix = f"{field}: " if field else ""
        return f"❌ Invalid recipe: {prefix}{msg}"

    recipe = SavedRecipeDB(**payload.to_db_dict())

    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                session.add(recipe)
        return f"✓ Saved '{recipe.name}' to your collection!"
    except Exception as exc:  # pragma: no cover - surfaced to user
        return f"❌ Database error: {exc}"


async def explore_recipes_db(sql_query: str) -> str:
    """Run a SELECT or UPDATE query against the saved recipes database."""
    query_stripped = sql_query.strip()
    query_upper = query_stripped.upper()

    if not query_upper.startswith(("SELECT", "UPDATE")):
        return "❌ Only SELECT and UPDATE queries allowed"

    for label, pattern in BLOCKED_SQL:
        if re.search(pattern, query_upper):
            return f"❌ Blocked: {label} operations not allowed"

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text(sql_query))

            if query_upper.startswith("UPDATE"):
                await session.commit()
                return f"✓ Updated {result.rowcount} row(s)"

            rows = result.fetchall()
            if not rows:
                return "No results found."

            columns = result.keys()
            lines = [" | ".join(str(col) for col in columns), "-" * 40]

            for row in rows[:50]:
                lines.append(" | ".join(str(value) for value in row))

            if len(rows) > 50:
                lines.append(f"... +{len(rows) - 50} more rows")

            return "\n".join(lines)
    except Exception as exc:  # pragma: no cover - surfaced to user
        return f"❌ Query error: {exc}"

