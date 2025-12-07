# Implementation Plan: Save Recipes

**Feature**: 1-save-recipes  
**Date**: December 7, 2025  
**Status**: Ready for Implementation  

---

## Overview

Implement persistent recipe storage with an interactive approval workflow. Users can save recipes they enjoy, with the agent detecting satisfaction and offering to save.

**Simplified Design**: 3 tools, direct SQLAlchemy, no repository pattern.

---

## Technical Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| Database | SQLite | Local persistence |
| ORM | SQLAlchemy 2.0+ | Async, direct queries |
| HITL | HumanInTheLoopMiddleware | Built-in approval UI |
| Frontend | Agent Chat UI (hosted) | **No changes needed** |

---

## Project Structure Updates

```
recipe_creator/
├── agent.py                    # MODIFY: Add tools + HITL middleware
├── config.py                   # MODIFY: Add database config
├── requirements.txt            # MODIFY: Add SQLAlchemy, aiosqlite
├── data/
│   └── recipes.db             # NEW: SQLite database (auto-created)
├── models/
│   ├── __init__.py
│   ├── recipe.py              # EXISTING
│   └── saved_recipe.py        # NEW: SavedRecipe + DB model
├── storage/
│   └── database.py            # NEW: Engine setup + table creation
└── tools/
    ├── __init__.py
    └── recipe_storage.py      # NEW: 2 tools (save_recipe, explore_recipes_db)
```

---

## Implementation Phases

### Phase 1: Database Layer

#### Task 1.1: Add Dependencies

**File**: `requirements.txt`

```diff
+ sqlalchemy>=2.0
+ aiosqlite
```

#### Task 1.2: Create Database Configuration

**File**: `config.py` (additions)

```python
database_path: Path = Field(
    default_factory=lambda: Path(os.getenv("RECIPE_DB_PATH", "data/recipes.db"))
)

@property
def database_url(self) -> str:
    return f"sqlite+aiosqlite:///{self.database_path}"
```

#### Task 1.3: Create SavedRecipe Model

**File**: `models/saved_recipe.py`

```python
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class SavedRecipeDB(Base):
    """SQLAlchemy model - single source of truth."""
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
    saved_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    conversation_id = Column(String(100))
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
```

#### Task 1.4: Create Database Engine

**File**: `storage/database.py`

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import config
from models.saved_recipe import Base

engine = create_async_engine(config.database_url, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    """Create database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

---

### Phase 2: Storage Tools (2 Tools Only)

**File**: `tools/recipe_storage.py`

```python
import re
from datetime import datetime
from uuid import uuid4
from sqlalchemy import text, update
from storage.database import AsyncSessionLocal
from models.saved_recipe import SavedRecipeDB

# =============================================================================
# TOOL 1: save_recipe (requires HITL approval)
# =============================================================================

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
        ingredients: List of {"name": str, "quantity": str, "unit": str | None}
        instructions: List of preparation steps
        prep_time_minutes: Prep time in minutes
        cook_time_minutes: Cook time in minutes
        servings: Number of servings
        notes: Optional tips or variations
    
    Returns:
        Confirmation message with recipe ID
    """
    if not name:
        return "❌ Recipe name is required"
    if recipe_type not in ('cocktail', 'food', 'dessert'):
        return "❌ Invalid recipe_type. Must be: cocktail, food, or dessert"
    
    recipe_id = str(uuid4())
    
    try:
        async with AsyncSessionLocal() as session:
            db_recipe = SavedRecipeDB(
                id=recipe_id,
                name=name,
                recipe_type=recipe_type,
                ingredients=ingredients,
                instructions=instructions,
                prep_time_minutes=prep_time_minutes,
                cook_time_minutes=cook_time_minutes,
                servings=servings,
                notes=notes,
                saved_at=datetime.utcnow(),
                is_deleted=False
            )
            session.add(db_recipe)
            await session.commit()
        
        return f"✓ Saved '{name}' to your collection!"
    except Exception as e:
        return f"❌ Database error: {e}"

# =============================================================================
# TOOL 2: explore_recipes_db (SELECT + UPDATE, no hard DELETE)
# =============================================================================

BLOCKED_SQL = [
    r'\bDELETE\b', r'\bDROP\b', r'\bTRUNCATE\b',
    r'\bCREATE\s+TABLE\b', r'\bALTER\b', r'\bINSERT\b'
]

async def explore_recipes_db(sql_query: str) -> str:
    """
    Run a SELECT or UPDATE query on the saved recipes database.
    
    Use this to explore, search, analyze, and modify saved recipes.
    Hard DELETE is blocked - use UPDATE with is_deleted = 1 instead.
    
    Args:
        sql_query: A SELECT or UPDATE query against saved_recipes table
    
    Available columns:
        id, name, recipe_type, ingredients (JSON), instructions (JSON),
        prep_time_minutes, cook_time_minutes, servings, tags (JSON),
        notes, user_notes, saved_at, is_deleted (boolean: 0=false, 1=true)
    
    Example SELECT:
        - "SELECT name, recipe_type FROM saved_recipes WHERE is_deleted = 0"
        - "SELECT name FROM saved_recipes WHERE ingredients LIKE '%bourbon%'"
    
    Example UPDATE (soft delete, notes, etc.):
        - "UPDATE saved_recipes SET is_deleted = 1 WHERE name = 'Old Fashioned'"
        - "UPDATE saved_recipes SET user_notes = 'Favorite!' WHERE name = 'Mojito'"
    
    Returns:
        Query results (SELECT) or row count (UPDATE)
    """
    query_upper = sql_query.upper().strip()
    
    # Must be SELECT or UPDATE
    if not (query_upper.startswith('SELECT') or query_upper.startswith('UPDATE')):
        return "❌ Only SELECT and UPDATE queries allowed"
    
    # Check for blocked operations
    for pattern in BLOCKED_SQL:
        if re.search(pattern, query_upper):
            return f"❌ Blocked: {pattern.replace(chr(92), '')} operations not allowed"
    
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text(sql_query))
            
            # Handle UPDATE
            if query_upper.startswith('UPDATE'):
                await session.commit()
                return f"✓ Updated {result.rowcount} row(s)"
            
            # Handle SELECT
            rows = result.fetchall()
            if not rows:
                return "No results found."
            
            cols = result.keys()
            lines = [" | ".join(str(c) for c in cols)]
            lines.append("-" * 40)
            for row in rows[:50]:
                lines.append(" | ".join(str(v) for v in row))
            
            if len(rows) > 50:
                lines.append(f"... +{len(rows) - 50} more rows")
            
            return "\n".join(lines)
    except Exception as e:
        return f"❌ Query error: {e}"
```

---

### Phase 3: Agent Integration

#### Task 3.1: Update System Prompt

**File**: `prompts/default_prompt.txt` (additions)

```text
## Recipe Saving

You can help users save recipes they enjoy. Watch for signals of satisfaction:
- Explicit praise: "This is great!", "Perfect!", "Love it"
- Intent to use: "I'm making this tonight", "Can't wait to try"
- Engagement questions: "What wine pairs with this?", "Can I substitute X?"

When you detect satisfaction, naturally offer to save:
"I'm glad you like it! Would you like me to save this recipe to your collection?"

If they agree, use the save_recipe tool with all the recipe details.

For browsing saved recipes, use explore_recipes_db to run SQL queries:
- "SELECT name, recipe_type FROM saved_recipes WHERE is_deleted = 0"
- "SELECT * FROM saved_recipes WHERE name = 'Old Fashioned' AND is_deleted = 0"
- "SELECT name FROM saved_recipes WHERE ingredients LIKE '%bourbon%' AND is_deleted = 0"
```

#### Task 3.2: Update Agent Factory with HITL Middleware

**File**: `agent.py` (updated)

```python
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import MemorySaver

from config import config
from tools.web_search import web_search
from tools.youtube import get_youtube_transcript
from tools.recipe_storage import save_recipe, explore_recipes_db

# Human-in-the-loop: require approval before saving
hitl_middleware = HumanInTheLoopMiddleware(
    interrupt_on={"save_recipe": True},
    description_prefix="Save this recipe to your collection?"
)

def create_recipe_agent(model: str | None = None, system_prompt: str | None = None):
    """Create recipe agent with save capability."""
    return create_agent(
        model=model or config.model,
        tools=[
            web_search,
            get_youtube_transcript,
            save_recipe,          # HITL approval required
            explore_recipes_db,   # SELECT + UPDATE (no hard DELETE)
        ],
        system_prompt=system_prompt or config.system_prompt,
        middleware=[hitl_middleware],
        checkpointer=MemorySaver(),
    )

graph = create_recipe_agent()
```

---

## Frontend: NO CHANGES REQUIRED ✓

The hosted Agent Chat UI supports HITL interrupt flows:
1. User says "save this recipe"
2. Agent calls `save_recipe` tool with recipe data
3. `HumanInTheLoopMiddleware` triggers interrupt
4. Agent Chat UI shows tool call + Approve/Reject buttons
5. User approves → recipe saved

---

## Acceptance Criteria Mapping

| Requirement | Implementation |
|-------------|----------------|
| FR-1: Satisfaction Detection | System prompt instructions |
| FR-2: User-Initiated Save | `save_recipe` tool |
| FR-3: Recipe Persistence | SQLite + direct SQLAlchemy |
| FR-4: Save Workflow | `HumanInTheLoopMiddleware` |
| FR-5: Approval Card | Built-in Agent Chat UI |
| FR-6: Recipe Retrieval | `explore_recipes_db` SQL queries |
| FR-7: Search/Filter | `explore_recipes_db` with WHERE clauses |

---

## Testing Strategy

### Manual Testing

1. **Save**: Ask for recipe → "Save this" → Approve → Verify in DB
2. **Decline**: Save prompt → Reject → Verify not saved
3. **List**: Save recipes → "What recipes do I have saved?" → Agent uses SQL
4. **Search**: "Any bourbon cocktails?" → Agent uses SQL with LIKE
5. **Delete**: "Delete the mojito" → Verify `is_deleted = 1`
6. **Explore**: "How many recipes by type?" → Agent uses GROUP BY

---

## References

- **Generative UI Tutorial**: https://www.youtube.com/watch?v=sCqN01R8nIQ
- **LangGraph Documentation**: https://reference.langchain.com/python/langgraph/
- **Agent Chat UI**: https://github.com/langchain-ai/agent-chat-ui

---

*Implementation plan complete. Ready for task breakdown.*
