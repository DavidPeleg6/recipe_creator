# Data Model: Recipe Storage

**Feature**: 4-recipe-storage  
**Date**: December 2, 2025  

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Recipe                               │
├─────────────────────────────────────────────────────────────┤
│ PK  id: UUID                                                │
│     name: String (required)                                 │
│     recipe_type: Enum[cocktail, food, dessert] (required)   │
│     ingredients: List[Ingredient] (required)                │
│     instructions: List[String] (required)                   │
│     prep_time: Integer (minutes, optional)                  │
│     cook_time: Integer (minutes, optional)                  │
│     servings: Integer (optional)                            │
│     source_references: List[String]                         │
│     notes: String (optional)                                │
│     image_url: String (optional)                            │
│     tags: List[String]                                      │
│     is_deleted: Boolean (default false)                     │
│     created_at: Timestamp (auto)                            │
│     last_accessed_at: Timestamp (auto-updated)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ embedded
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Ingredient                             │
├─────────────────────────────────────────────────────────────┤
│     name: String (required)                                 │
│     quantity: String (required)                             │
│     unit: String (optional)                                 │
│     notes: String (optional)                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Entities

### Recipe

The existing `Recipe` model extended with persistence fields (consolidated, not a separate model).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Yes | Unique identifier (auto-generated) |
| name | String | Yes | Recipe name |
| recipe_type | Enum | Yes | One of: cocktail, food, dessert |
| ingredients | List[Ingredient] | Yes | Ingredients with quantities |
| instructions | List[String] | Yes | Ordered preparation steps |
| prep_time | Integer | No | Preparation time in minutes |
| cook_time | Integer | No | Cooking time in minutes (food only) |
| servings | Integer | No | Number of servings |
| source_references | List[String] | No | URLs where recipe was found |
| notes | String | No | Tips, variations, or additional info |
| image_url | String | No | GCS URL for generated image |
| tags | List[String] | No | User-defined and auto-generated tags |
| is_deleted | Boolean | Yes | Soft delete flag (default: false) |
| created_at | Timestamp | Yes | When recipe was saved (auto) |
| last_accessed_at | Timestamp | Yes | Last retrieval time (auto-updated) |

**Validation Rules**:
- `name` must be non-empty, max 200 characters
- `recipe_type` must be valid enum value
- `ingredients` must contain at least 1 item
- `instructions` must contain at least 1 step
- `servings` must be positive integer if provided

**State Transitions** (Soft Delete):
```
[New] → save_recipe → [Active] (is_deleted = false)
[Active] → update_recipe → [Active]
[Active] → soft_delete → [Deleted] (is_deleted = true)
[Deleted] → restore → [Active] (is_deleted = false)
```

**Query Filter**: All SELECT queries auto-filter `WHERE is_deleted = false`

### Ingredient

Embedded entity within Recipe (stored as JSON in database).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | String | Yes | Ingredient name |
| quantity | String | Yes | Amount (e.g., "2", "1/2") |
| unit | String | No | Measurement unit (oz, cups, ml) |
| notes | String | No | Preparation notes (diced, chilled) |

---

## Storage Schema (SQLite/PostgreSQL-compatible)

```sql
-- Main recipes table
CREATE TABLE saved_recipes (
    id TEXT PRIMARY KEY,                -- UUID as text (PostgreSQL: UUID type)
    name TEXT NOT NULL,
    recipe_type TEXT NOT NULL CHECK (recipe_type IN ('cocktail', 'food', 'dessert')),
    ingredients_json TEXT NOT NULL,     -- JSON array of Ingredient objects
    instructions_json TEXT NOT NULL,    -- JSON array of strings
    prep_time INTEGER,                  -- Minutes
    cook_time INTEGER,                  -- Minutes
    servings INTEGER CHECK (servings > 0),
    source_references_json TEXT,        -- JSON array of URLs
    notes TEXT,
    image_url TEXT,                     -- GCS bucket URL
    tags_json TEXT,                     -- JSON array of strings
    is_deleted BOOLEAN DEFAULT FALSE,   -- Soft delete flag
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for search performance
CREATE INDEX idx_recipe_name ON saved_recipes(name);
CREATE INDEX idx_recipe_type ON saved_recipes(recipe_type);
CREATE INDEX idx_recipe_is_deleted ON saved_recipes(is_deleted);

-- Composite index for common query pattern (active recipes)
CREATE INDEX idx_recipe_active ON saved_recipes(is_deleted, name);

-- Full-text search for ingredient queries (SQLite only, optional)
-- CREATE VIRTUAL TABLE recipe_fts USING fts5(
--     name,
--     ingredients_text,
--     tags_text,
--     content='saved_recipes',
--     content_rowid='rowid'
-- );
```

**Soft Delete Operations**:
```sql
-- "Delete" a recipe (soft delete)
UPDATE saved_recipes SET is_deleted = true WHERE id = 'uuid-here';

-- Restore a deleted recipe
UPDATE saved_recipes SET is_deleted = false WHERE id = 'uuid-here';

-- All SELECTs auto-filter via guardrails:
-- SELECT * FROM saved_recipes WHERE is_deleted = false AND ...
```

---

## Pydantic Model

**File**: `models/recipe.py` (extend existing)

```python
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class RecipeType(str, Enum):
    """Types of recipes the agent can generate."""
    COCKTAIL = "cocktail"
    FOOD = "food"
    DESSERT = "dessert"


class Ingredient(BaseModel):
    """Individual ingredient with quantity information."""
    name: str = Field(..., min_length=1, max_length=100)
    quantity: str = Field(..., min_length=1)
    unit: Optional[str] = None
    notes: Optional[str] = None


class Recipe(BaseModel):
    """Recipe model - used for both generation and persistence.
    
    Consolidated from original Recipe + persistence fields.
    Changes from original:
    - prep_time/cook_time: timedelta → int (minutes)
    - Added: id, image_url, tags, is_deleted, created_at, last_accessed_at
    """
    # Core recipe fields
    name: str = Field(..., min_length=1, max_length=200)
    recipe_type: RecipeType
    ingredients: list[Ingredient] = Field(..., min_length=1)
    instructions: list[str] = Field(..., min_length=1)
    prep_time: Optional[int] = Field(default=None, ge=0, description="Minutes")
    cook_time: Optional[int] = Field(default=None, ge=0, description="Minutes")
    servings: Optional[int] = Field(default=None, gt=0)
    source_references: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
    
    # Persistence fields (NEW)
    id: UUID = Field(default_factory=uuid4)
    image_url: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

# NOTE: No separate models needed for listing/searching.
# Agent has direct SQL access and can SELECT whatever columns it needs.
```

---

## Search Capabilities

### By Name
```sql
SELECT * FROM saved_recipes WHERE name LIKE '%old fashioned%' COLLATE NOCASE;
```

### By Ingredient
```sql
SELECT * FROM saved_recipes 
WHERE ingredients_json LIKE '%bourbon%' COLLATE NOCASE;
```

### By Type
```sql
SELECT * FROM saved_recipes WHERE recipe_type = 'cocktail';
```

### By Tags
```sql
SELECT * FROM saved_recipes 
WHERE tags_json LIKE '%"whiskey"%';
```

---

## Data Migration

**From**: None (new feature)  
**To**: `saved_recipes` table

Initial setup script:
```python
def init_database(db_path: str = "recipes.db"):
    """Initialize the recipe storage database."""
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return engine
```

---

*Data model complete. Ready for API contract definition.*

