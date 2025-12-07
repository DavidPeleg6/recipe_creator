# API Contracts: Save Recipes

**Feature**: 1-save-recipes  
**Date**: December 7, 2025  

---

## Overview

This feature uses **3 simple tools** + `HumanInTheLoopMiddleware`. No custom repository pattern or message types needed.

| Tool | Purpose | HITL Approval |
|------|---------|---------------|
| `save_recipe` | Save a recipe to database | ✓ Required |
| `explore_recipes_db` | Run SELECT/UPDATE SQL queries | No |

---

## Agent Tools

### Tool: save_recipe

Saves a recipe to the database. **Requires HITL approval** via middleware.

```python
async def save_recipe(
    name: str,
    recipe_type: str,
    ingredients: list[dict],
    instructions: list[str],
    prep_time_minutes: int | None = None,
    cook_time_minutes: int | None = None,
    servings: int | None = None,
    notes: str | None = None
) -> str:
    """
    Save a recipe to your collection.
    
    This tool requires user approval before executing.
    Extract all recipe data from the conversation first.
    
    Args:
        name: Recipe name (e.g., "Old Fashioned")
        recipe_type: One of: 'cocktail', 'food', 'dessert'
        ingredients: List of {"name": str, "quantity": str, "unit": str?, "notes": str?}
        instructions: List of preparation steps
        prep_time_minutes: Prep time in minutes
        cook_time_minutes: Cook time in minutes
        servings: Number of servings
        notes: Tips or variations
    
    Returns:
        Confirmation message with recipe ID
    
    Example:
        >>> save_recipe(
        ...     name="Old Fashioned",
        ...     recipe_type="cocktail",
        ...     ingredients=[{"name": "bourbon", "quantity": "2", "unit": "oz"}],
        ...     instructions=["Add ingredients to glass", "Stir", "Garnish"],
        ...     prep_time_minutes=5,
        ...     servings=1
        ... )
        "✓ Saved 'Old Fashioned' to your collection!"
    """
```

---

### Tool: explore_recipes_db

Run SELECT or UPDATE queries on the recipes database.

```python
async def explore_recipes_db(sql_query: str) -> str:
    """
    Run a SELECT or UPDATE query on the saved recipes database.
    
    Use this to explore, search, analyze, and modify saved recipes.
    SELECT and UPDATE allowed - hard DELETE blocked.
    
    Args:
        sql_query: A SELECT or UPDATE query against saved_recipes table
    
    Available columns:
        - id (text, UUID)
        - name (text)
        - recipe_type (text: 'cocktail', 'food', 'dessert')
        - ingredients (JSON array)
        - instructions (JSON array)
        - prep_time_minutes (integer)
        - cook_time_minutes (integer)
        - servings (integer)
        - tags (JSON array)
        - notes (text)
        - user_notes (text)
        - saved_at (datetime)
        - is_deleted (boolean, stored as 0=false/1=true in SQLite)
    
    Returns:
        Query results (SELECT) or confirmation message (UPDATE)
    
    Example SELECT queries:
        >>> explore_recipes_db("SELECT name, recipe_type FROM saved_recipes WHERE is_deleted = 0")
        "name | recipe_type\n-----------\nOld Fashioned | cocktail"
        
        >>> explore_recipes_db("SELECT name FROM saved_recipes WHERE ingredients LIKE '%bourbon%'")
        "name\n----\nOld Fashioned\nManhattan"
    
    Example UPDATE queries (soft delete, add notes, etc.):
        >>> explore_recipes_db("UPDATE saved_recipes SET is_deleted = 1 WHERE name = 'Old Fashioned'")
        "✓ Updated 1 row(s)"
        
        >>> explore_recipes_db("UPDATE saved_recipes SET user_notes = 'My favorite!' WHERE name = 'Mojito'")
        "✓ Updated 1 row(s)"
    
    Blocked operations (will return error):
        - DELETE (hard delete)
        - DROP, TRUNCATE
        - CREATE TABLE, ALTER TABLE
        - INSERT (use save_recipe tool instead)
    """
```

---

## Guardrails for explore_recipes_db

| Blocked Pattern | Reason |
|-----------------|--------|
| `DELETE` | Hard delete blocked - use UPDATE with `is_deleted = 1` |
| `DROP` | Prevents table destruction |
| `TRUNCATE` | Prevents mass data loss |
| `CREATE TABLE` | Prevents schema changes |
| `ALTER TABLE` | Prevents schema changes |
| `INSERT` | Use `save_recipe` tool instead |

**Allowed**:
- `SELECT` - all queries
- `UPDATE` - soft deletes, add notes, modify tags, etc.

**Limits**:
- SELECT results capped at 50 rows
- Query must start with `SELECT` or `UPDATE`

---

## Database Schema

Single table, direct SQLAlchemy access (no repository pattern):

```sql
CREATE TABLE saved_recipes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    recipe_type TEXT NOT NULL CHECK(recipe_type IN ('cocktail', 'food', 'dessert')),
    ingredients TEXT NOT NULL,      -- JSON array
    instructions TEXT NOT NULL,     -- JSON array
    prep_time_minutes INTEGER,
    cook_time_minutes INTEGER,
    servings INTEGER,
    source_references TEXT,         -- JSON array
    notes TEXT,
    user_notes TEXT,
    tags TEXT DEFAULT '[]',         -- JSON array
    saved_at TEXT NOT NULL,
    conversation_id TEXT,
    is_deleted INTEGER DEFAULT 0 NOT NULL
);

CREATE INDEX idx_name ON saved_recipes(name);
CREATE INDEX idx_type ON saved_recipes(recipe_type);
CREATE INDEX idx_deleted ON saved_recipes(is_deleted);
```

---

## Error Handling

Tools return error messages as strings:

```python
# Save errors
"❌ Recipe name is required"
"❌ Invalid recipe_type. Must be: cocktail, food, or dessert"
"❌ Database error: {details}"

# Delete errors  
"❌ No recipe found matching '{name}'"

# Query errors
"❌ Only SELECT queries allowed"
"❌ Blocked: DELETE operations not allowed"
"❌ Query error: {sqlite_error}"
```

---

## HITL Middleware Configuration

```python
from langchain.agents.middleware import HumanInTheLoopMiddleware

hitl = HumanInTheLoopMiddleware(
    interrupt_on={
        "save_recipe": True,  # Always require approval
    },
    description_prefix="Save this recipe to your collection?"
)
```

The hosted Agent Chat UI handles the approval prompt automatically.

---

*Simplified API contracts - 2 tools, no repository pattern.*
