# Quickstart: Save Recipes Feature

**Feature**: 1-save-recipes  
**Date**: December 7, 2025  

---

## Prerequisites

- Existing Recipe Agent Backend running
- Python 3.11+
- Agent Chat UI access (hosted at https://agentchat.vercel.app)

---

## Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
cd recipe_creator

# Add to requirements.txt
echo "sqlalchemy>=2.0" >> requirements.txt
echo "aiosqlite" >> requirements.txt

# Install
pip install -r requirements.txt
```

### 2. Database auto-creates on first run

```bash
# Create data directory
mkdir -p data

# Database will be auto-created at: ./data/recipes.db
```

### 3. Optional: Custom Database Path

```bash
# Add to .env if desired
echo "RECIPE_DB_PATH=./data/recipes.db" >> .env
```

---

## File Changes (Simple!)

### New Files to Create

```
recipe_creator/
├── storage/
│   └── database.py           # SQLAlchemy engine setup only
├── models/
│   └── saved_recipe.py       # SavedRecipeDB model
└── tools/
    └── recipe_storage.py     # 2 tools: save_recipe, explore_recipes_db
```

### Files to Modify

```
recipe_creator/
├── agent.py                  # Add 2 tools + HITL middleware
├── config.py                 # Add database_path and database_url
├── requirements.txt          # Add sqlalchemy, aiosqlite
└── prompts/default_prompt.txt # Add recipe saving instructions
```

### Frontend: NO CHANGES NEEDED ✓

The hosted Agent Chat UI already supports HITL interrupts!

---

## Implementation (3 Phases)

### Phase 1: Database Layer (~10 min)

**File**: `models/saved_recipe.py`

```python
from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime
from uuid import uuid4

Base = declarative_base()

class SavedRecipeDB(Base):
    __tablename__ = "saved_recipes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False, index=True)
    recipe_type = Column(String(20), nullable=False, index=True)
    ingredients = Column(JSON, nullable=False)
    instructions = Column(JSON, nullable=False)
    prep_time_minutes = Column(Integer)
    cook_time_minutes = Column(Integer)
    servings = Column(Integer)
    notes = Column(String(2000))
    user_notes = Column(String(2000))
    tags = Column(JSON, default=list)
    saved_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False, nullable=False)
```

**File**: `storage/database.py`

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import config
from models.saved_recipe import Base

engine = create_async_engine(config.database_url, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

### Phase 2: Tools (~15 min)

**File**: `tools/recipe_storage.py`

```python
import re
from datetime import datetime
from uuid import uuid4
from sqlalchemy import text
from storage.database import AsyncSessionLocal
from models.saved_recipe import SavedRecipeDB

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
    """Save a recipe (requires HITL approval)."""
    if recipe_type not in ('cocktail', 'food', 'dessert'):
        return "❌ Invalid recipe_type"
    
    async with AsyncSessionLocal() as session:
        db_recipe = SavedRecipeDB(
            id=str(uuid4()),
            name=name,
            recipe_type=recipe_type,
            ingredients=ingredients,
            instructions=instructions,
            prep_time_minutes=prep_time_minutes,
            cook_time_minutes=cook_time_minutes,
            servings=servings,
            notes=notes
        )
        session.add(db_recipe)
        await session.commit()
    
    return f"✓ Saved '{name}' to your collection!"

BLOCKED_SQL = [r'\bDELETE\b', r'\bDROP\b', r'\bTRUNCATE\b', 
               r'\bCREATE\s+TABLE\b', r'\bALTER\b', r'\bINSERT\b']

async def explore_recipes_db(sql_query: str) -> str:
    """Run SELECT or UPDATE queries (no hard DELETE)."""
    query_upper = sql_query.upper().strip()
    
    if not (query_upper.startswith('SELECT') or query_upper.startswith('UPDATE')):
        return "❌ Only SELECT and UPDATE allowed"
    
    for pattern in BLOCKED_SQL:
        if re.search(pattern, query_upper):
            return f"❌ Blocked: {pattern} not allowed"
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(text(sql_query))
        
        if query_upper.startswith('UPDATE'):
            await session.commit()
            return f"✓ Updated {result.rowcount} row(s)"
        
        rows = result.fetchall()
        if not rows:
            return "No results found."
        
        cols = result.keys()
        lines = [" | ".join(str(c) for c in cols), "-" * 40]
        for row in rows[:50]:
            lines.append(" | ".join(str(v) for v in row))
        
        return "\n".join(lines)
```

### Phase 3: Agent Integration (~10 min)

**File**: `agent.py`

```python
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import MemorySaver
from tools.recipe_storage import save_recipe, explore_recipes_db

hitl_middleware = HumanInTheLoopMiddleware(
    interrupt_on={"save_recipe": True},
    description_prefix="Save this recipe?"
)

def create_recipe_agent(...):
    return create_agent(
        model=config.model,
        tools=[
            web_search,
            get_youtube_transcript,
            save_recipe,          # HITL approval
            explore_recipes_db,   # SQL queries
        ],
        system_prompt=config.system_prompt,
        middleware=[hitl_middleware],
        checkpointer=MemorySaver(),
    )
```

**File**: `prompts/default_prompt.txt` (add this section)

```text
## Recipe Saving

Watch for satisfaction signals (praise, intent to use, engagement).
When detected, offer: "Would you like me to save this recipe?"

If they agree, use save_recipe with full recipe data.

For browsing saved recipes, use explore_recipes_db with SQL:
- List: "SELECT name, recipe_type FROM saved_recipes WHERE is_deleted = 0"
- Delete: "UPDATE saved_recipes SET is_deleted = 1 WHERE name = 'Mojito'"
- Search: "SELECT name FROM saved_recipes WHERE ingredients LIKE '%bourbon%'"
```

---

## Test It!

### 1. Start the agent

```bash
langgraph dev --no-browser --port 2024
```

### 2. Connect Agent Chat UI

- Go to https://agentchat.vercel.app
- Connect to `http://localhost:2024`

### 3. Test Save Flow

**User**: "How do I make an Old Fashioned?"  
**Agent**: *generates recipe*  
**User**: "This looks perfect!"  
**Agent**: "Would you like me to save this recipe?"  
**User**: "Yes please"  
**Agent**: *calls save_recipe tool*  
**UI**: Shows approval prompt with recipe data + Approve/Reject buttons  
**User**: *clicks Approve*  
**Agent**: "✓ Saved 'Old Fashioned' to your collection!"

### 4. Test List/Search

**User**: "What recipes do I have saved?"  
**Agent**: *uses `explore_recipes_db("SELECT name FROM saved_recipes WHERE is_deleted = 0")`*  
**Agent**: Shows list

**User**: "Delete the Old Fashioned"  
**Agent**: *uses `explore_recipes_db("UPDATE saved_recipes SET is_deleted = 1 WHERE name = 'Old Fashioned'")`*  
**Agent**: "✓ Updated 1 row(s)"

---

## Verify Database

```bash
sqlite3 data/recipes.db "SELECT name, recipe_type, is_deleted FROM saved_recipes;"
```

---

## Testing Checklist

- [ ] Save a cocktail (agent offers after satisfaction signal)
- [ ] Approve in UI → recipe saved
- [ ] Reject in UI → recipe not saved
- [ ] List saved recipes via SQL
- [ ] Search by ingredient via SQL WHERE clause
- [ ] Soft delete via UPDATE
- [ ] Handle missing optional fields

---

## Troubleshooting

### "Approval UI not showing"

✓ The hosted Agent Chat UI auto-handles HITL interrupts. No setup needed.

### "Database not found"

```bash
mkdir -p data
python -c "from storage.database import init_db; import asyncio; asyncio.run(init_db())"
```

### "SQL syntax error"

Agent needs proper column names. Check `available columns` in tool docstring.

---

## Next Steps

After basic implementation works:

1. Add recipe editing via UPDATE queries
2. Implement tags/categories
3. Add fuzzy search
4. Consider cloud backup

---

*Quickstart complete - just 3 files to create, 3 to modify, 0 frontend changes!*
