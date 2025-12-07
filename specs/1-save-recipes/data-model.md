# Data Model: Save Recipes

**Feature**: 1-save-recipes  
**Date**: December 7, 2025  

---

## Entity Relationship Diagram

```
┌──────────────────────────┐
│      SavedRecipeDB       │  (SQLite + SQLAlchemy)
├──────────────────────────┤
│ id: TEXT (PK)            │
│ name: TEXT               │
│ recipe_type: TEXT        │
│ ingredients: JSON        │
│ instructions: JSON       │
│ prep_time_minutes: INT   │
│ cook_time_minutes: INT   │
│ servings: INT            │
│ notes: TEXT              │
│ user_notes: TEXT         │
│ tags: JSON               │
│ saved_at: DATETIME       │
│ is_deleted: BOOL         │
└──────────────────────────┘
         │
         │ contains (JSON array)
         ▼
┌─────────────────────┐
│    Ingredient       │
├─────────────────────┤
│ name: String        │
│ quantity: String    │
│ unit: String?       │
└─────────────────────┘
```

---

## Entities

### SavedRecipeDB

Single table for all saved recipes. Direct SQLAlchemy access (no repository pattern).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | TEXT (UUID) | Yes | Unique identifier |
| name | TEXT | Yes | Recipe name (e.g., "Old Fashioned") |
| recipe_type | TEXT | Yes | 'cocktail', 'food', or 'dessert' |
| ingredients | JSON | Yes | Array of `{name, quantity, unit}` |
| instructions | JSON | Yes | Array of step strings |
| prep_time_minutes | INTEGER | No | Preparation time in minutes |
| cook_time_minutes | INTEGER | No | Cooking time in minutes |
| servings | INTEGER | No | Number of servings |
| source_references | JSON | No | Array of source URLs |
| notes | TEXT | No | Recipe tips (from agent) |
| user_notes | TEXT | No | User-added notes |
| tags | JSON | No | Array of user tags |
| saved_at | DATETIME | Yes | When saved (auto) |
| conversation_id | TEXT | No | Source conversation ref |
| is_deleted | BOOLEAN (INTEGER) | Yes | 0=false/active, 1=true/deleted |

### Ingredient (embedded in JSON)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | String | Yes | e.g., "bourbon" |
| quantity | String | Yes | e.g., "2", "1/2" |
| unit | String | No | e.g., "oz", "cups" |

### RecipeType (TEXT values)

| Value | Description |
|-------|-------------|
| cocktail | Drinks |
| food | Main dishes, sides |
| dessert | Sweets |

---

## SQLAlchemy Model

**File**: `models/saved_recipe.py`

```python
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class SavedRecipeDB(Base):
    """SQLAlchemy model for saved recipes."""
    
    __tablename__ = "saved_recipes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False, index=True)
    recipe_type = Column(String(20), nullable=False, index=True)
    ingredients = Column(JSON, nullable=False)
    instructions = Column(JSON, nullable=False)
    prep_time_minutes = Column(Integer)
    cook_time_minutes = Column(Integer)
    servings = Column(Integer)
    source_references = Column(JSON, default=list)
    notes = Column(String(2000))
    user_notes = Column(String(2000))
    tags = Column(JSON, default=list)
    saved_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    conversation_id = Column(String(100))
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
```

---

## Database Schema (SQLite)

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
    source_references TEXT DEFAULT '[]',
    notes TEXT,
    user_notes TEXT,
    tags TEXT DEFAULT '[]',
    saved_at TEXT NOT NULL,
    conversation_id TEXT,
    is_deleted INTEGER DEFAULT 0 NOT NULL
);

CREATE INDEX idx_name ON saved_recipes(name);
CREATE INDEX idx_type ON saved_recipes(recipe_type);
CREATE INDEX idx_deleted ON saved_recipes(is_deleted);
CREATE INDEX idx_saved_at ON saved_recipes(saved_at DESC);
```

**Note**: SQLite doesn't have a native BOOLEAN type. SQLAlchemy's `Boolean` column is stored as INTEGER (0=false, 1=true). The ORM handles conversion automatically, but raw SQL queries use 0/1.

---

## Soft Delete Pattern

Records are never physically deleted:

```sql
-- Delete = mark as deleted
UPDATE saved_recipes SET is_deleted = 1 WHERE id = ?

-- Active recipes only
SELECT * FROM saved_recipes WHERE is_deleted = 0

-- Include deleted (recovery)
SELECT * FROM saved_recipes WHERE id = ?
```

---

## Data Flow

```
1. User: "Save this recipe"
        │
        ▼
2. Agent extracts recipe data, calls save_recipe tool
        │
        ▼
3. HumanInTheLoopMiddleware triggers interrupt
        │
        ▼
4. Agent Chat UI shows tool args + Approve/Reject
        │
        ▼
5a. Approve → INSERT into saved_recipes → "✓ Saved!"
5b. Reject  → Skip tool → "No problem, maybe next time"
```

---

## Example Data

### Ingredient JSON

```json
[
  {"name": "bourbon", "quantity": "2", "unit": "oz"},
  {"name": "sugar cube", "quantity": "1", "unit": null},
  {"name": "Angostura bitters", "quantity": "2", "unit": "dashes"}
]
```

### Instructions JSON

```json
[
  "Place sugar cube in glass",
  "Add bitters and a splash of water",
  "Muddle until dissolved",
  "Add bourbon and ice",
  "Stir and garnish"
]
```

---

*Data model complete. Simple single-table design with direct SQLAlchemy access.*
