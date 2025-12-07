# Tool Contracts: Recipe Storage

**Feature**: 4-recipe-storage  
**Date**: December 2, 2025  
**Updated**: Architecture simplified to 2 tools

---

## Overview

This document defines the LangChain tool interfaces for recipe storage functionality. The agent has **only 2 new tools** to minimize complexity:

1. **`execute_recipe_sql`** - Direct SQL access with guardrails
2. **`save_recipe`** - Triggers subflow for recipe structuring + image generation

---

## Tool 1: execute_recipe_sql

Execute SQL queries against the recipe database with safety guardrails.

### Signature

```python
def execute_recipe_sql(query: str) -> dict:
    """
    Execute a SQL query against the recipe database.
    
    The agent writes its own SQL queries for maximum flexibility.
    
    GUARDRAILS (enforced):
    - No DROP, TRUNCATE, ALTER, CREATE, GRANT, REVOKE
    - No DELETE (use soft delete: UPDATE SET is_deleted = true)
    - UPDATE MUST include WHERE clause
    - Operations limited to single rows for UPDATE
    
    Table Schema (saved_recipes):
    - id (UUID): Primary key
    - name (VARCHAR 200): Recipe name
    - recipe_type (VARCHAR 20): 'cocktail', 'food', or 'dessert'
    - ingredients (JSONB): Array of {name, quantity, unit, notes}
    - instructions (JSONB): Array of step strings
    - prep_time, cook_time (INTEGER): Time in minutes
    - servings (INTEGER)
    - source_references (JSONB): Array of URLs
    - notes (TEXT)
    - image_url (VARCHAR 500): GCS bucket URL
    - tags (JSONB): Array of strings
    - is_deleted (BOOLEAN): Soft delete flag (default: false)
    - created_at, last_accessed_at (TIMESTAMP)
    
    SOFT DELETE: To "delete" a recipe:
        UPDATE saved_recipes SET is_deleted = true WHERE id = 'uuid'
    
    NOTE: All SELECT queries auto-filter WHERE is_deleted = false
    
    Args:
        query: SQL query to execute (SELECT, INSERT, UPDATE with WHERE)
        
    Returns:
        For SELECT: {"status": "success", "rows": [...], "count": N}
        For INSERT/UPDATE: {"status": "success", "rows_affected": N, "message": "..."}
        For blocked queries: {"status": "error", "error": "Query blocked: ...", "query": "..."}
    """
```

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "SQL query to execute"
    }
  },
  "required": ["query"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["success", "error"]
    },
    "rows": {
      "type": "array",
      "description": "Query results (SELECT only)"
    },
    "count": {
      "type": "integer",
      "description": "Number of rows returned (SELECT only)"
    },
    "rows_affected": {
      "type": "integer",
      "description": "Rows affected (INSERT/UPDATE/DELETE)"
    },
    "error": {
      "type": "string",
      "description": "Error message if query blocked or failed"
    },
    "message": {
      "type": "string"
    }
  }
}
```

### Example Queries

**Search by ingredient** (auto-filters is_deleted = false):
```sql
SELECT id, name, recipe_type, tags 
FROM saved_recipes 
WHERE ingredients::text ILIKE '%bourbon%'
```

**List all recipes (headers only)** (auto-filters is_deleted = false):
```sql
SELECT id, name, recipe_type, tags FROM saved_recipes
```

**Get full recipe** (auto-filters is_deleted = false):
```sql
SELECT * FROM saved_recipes WHERE id = 'uuid-here'
```

**Update servings:**
```sql
UPDATE saved_recipes SET servings = 4 WHERE id = 'uuid-here'
```

**Soft delete recipe** (use UPDATE, not DELETE):
```sql
UPDATE saved_recipes SET is_deleted = true WHERE id = 'uuid-here'
```

**Restore deleted recipe:**
```sql
UPDATE saved_recipes SET is_deleted = false WHERE id = 'uuid-here'
```

### Blocked Queries (Examples)

```sql
-- BLOCKED: No DROP
DROP TABLE saved_recipes;

-- BLOCKED: No TRUNCATE
TRUNCATE saved_recipes;

-- BLOCKED: No DELETE (use soft delete UPDATE instead)
DELETE FROM saved_recipes WHERE id = 'uuid-here';

-- BLOCKED: UPDATE without WHERE
UPDATE saved_recipes SET servings = 4;
```

---

## Tool 2: save_recipe

Triggers subflow to structure recipe and generate image.

### Signature

```python
def save_recipe(raw_recipe_data: str) -> dict:
    """
    Save a recipe to the user's personal collection with auto-generated image.
    
    WHEN TO USE:
    - User explicitly says "save this", "keep this recipe", "add to favorites"
    - User confirms after you offer to save (e.g., "yes, save it")
    - Do NOT use just because user likes a recipe - always ask first!
    
    WHAT THIS DOES AUTOMATICALLY:
    1. Structures the raw recipe into proper format (name, ingredients, instructions)
    2. Generates a professional food photography image
    3. Uploads image to cloud storage
    4. Saves everything to the recipe database
    
    WHAT TO INCLUDE in raw_recipe_data:
    - Recipe name
    - All ingredients with quantities and units
    - Step-by-step instructions
    - Prep time and cook time (in minutes)
    - Number of servings
    - Recipe type: "cocktail", "food", or "dessert"
    - Source URLs (if from web search or YouTube)
    - Any tips or variations mentioned
    
    Example raw_recipe_data:
        "Old Fashioned cocktail. Ingredients: 2 oz bourbon, 1 sugar cube, 
        2 dashes Angostura bitters, orange peel. Instructions: 1) Muddle sugar 
        with bitters, 2) Add bourbon and ice, 3) Stir, 4) Garnish with orange peel.
        Prep time: 5 minutes. Serves: 1. Type: cocktail."
    
    Args:
        raw_recipe_data: Complete recipe information as a string. Include all
                         details - the system will format it properly.
        
    Returns:
        dict with:
            - status: "saved" or "error"
            - recipe_id: UUID of saved recipe (use for future reference)
            - recipe_name: Formatted recipe name
            - image_url: URL of generated image (show to user!)
            - message: Confirmation message to display
    
    After successful save, inform the user and show them the image_url.
    If they reject or want changes, use execute_recipe_sql to UPDATE or soft-delete.
    """
```

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "raw_recipe_data": {
      "type": "string",
      "description": "Unstructured recipe information from the conversation"
    }
  },
  "required": ["raw_recipe_data"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["saved", "error"]
    },
    "recipe_id": {
      "type": "string",
      "description": "UUID of the saved recipe"
    },
    "recipe_name": {
      "type": "string",
      "description": "Formally structured recipe name"
    },
    "image_url": {
      "type": "string",
      "nullable": true,
      "description": "GCS public URL of generated image"
    },
    "message": {
      "type": "string"
    },
    "error": {
      "type": "string",
      "description": "Error details if status is error"
    }
  }
}
```

### Subflow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    save_recipe Tool                          │
│                                                              │
│  Input: raw_recipe_data (string)                            │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Step 1: Recipe Structuring                          │    │
│  │   Prompt: prompts/recipe_structuring.txt            │    │
│  │   Output: Formal JSON recipe structure              │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Step 2: Image Prompt Generation                     │    │
│  │   Prompt: prompts/image_prompt_gen.txt              │    │
│  │   Output: Optimized image generation prompt         │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Step 3: Image Generation                            │    │
│  │   Model: Nano Banana Pro (Gemini API)               │    │
│  │   Output: PNG image bytes                           │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Step 4: GCS Upload                                  │    │
│  │   Bucket: $GCS_BUCKET_NAME/recipes/{id}.png         │    │
│  │   Output: Public URL                                │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Step 5: Database Insert                             │    │
│  │   INSERT INTO saved_recipes (...)                   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Output: {status, recipe_id, recipe_name, image_url, msg}   │
└─────────────────────────────────────────────────────────────┘
```

---

## Generative UI Message Types

### RecipeCardMessage

Custom message type for visual confirmation cards in Agent Chat UI.

```python
from models.recipe import RecipeType  # Use existing enum

class RecipeCardMessage(BaseModel):
    """
    Special message type rendered as a visual card in the UI.
    
    Returned after save_recipe to display confirmation.
    """
    type: Literal["recipe_card"] = "recipe_card"
    recipe_id: str
    recipe_name: str
    recipe_type: RecipeType  # Enum: cocktail, food, dessert
    prep_time: int | None = None  # Minutes (integer)
    servings: int | None = None
    image_url: str | None = None
    status: Literal["saved", "pending", "deleted"] = "saved"
    
    # Actions available on the card
    actions: list[str] = ["delete", "modify"]
```

---

## SQL Guardrails Contract

### Validation Rules

| Rule | Pattern | Action |
|------|---------|--------|
| No DROP | `\bDROP\s+` | Block with error |
| No TRUNCATE | `\bTRUNCATE\s+` | Block with error |
| No ALTER | `\bALTER\s+` | Block with error |
| No CREATE | `\bCREATE\s+` | Block with error |
| No GRANT | `\bGRANT\s+` | Block with error |
| **No DELETE** | `\bDELETE\s+` | Block - use soft delete UPDATE |
| UPDATE needs WHERE | `UPDATE x SET` without WHERE | Block with error |

### Soft Delete Pattern

**Instead of DELETE, use UPDATE**:
```sql
-- BLOCKED: Hard delete
DELETE FROM saved_recipes WHERE id = 'uuid-here';

-- CORRECT: Soft delete
UPDATE saved_recipes SET is_deleted = true WHERE id = 'uuid-here';

-- Restore a recipe
UPDATE saved_recipes SET is_deleted = false WHERE id = 'uuid-here';
```

### Auto-Injected Filters

All SELECT queries automatically get `is_deleted = false` filter:
```sql
-- Agent writes:
SELECT * FROM saved_recipes WHERE name ILIKE '%old%'

-- Guardrails transform to:
SELECT * FROM saved_recipes WHERE is_deleted = false AND name ILIKE '%old%'
```

### Future Enhancement: User Isolation

When multi-user support is added:
```python
def inject_user_filter(query: str, user_id: str) -> str:
    """Automatically add user_id filter to all queries."""
    # Will inject: WHERE user_id = :user_id AND is_deleted = false
    pass
```

---

*Tool contracts complete. Only 2 tools needed for full recipe storage functionality.*
