# Research: Save Recipes Feature

**Feature**: 1-save-recipes  
**Date**: December 7, 2025  

## Executive Summary

This document captures research findings for implementing the Save Recipes feature, focusing on LangGraph generative UI patterns, subagent workflows, and human-in-the-loop approval flows.

---

## 1. Generative UI in LangGraph (REFERENCE ONLY)

### Reference Video
- **Title**: Build a Generative UI App in LangGraph
- **URL**: https://www.youtube.com/watch?v=sCqN01R8nIQ
- **Duration**: 24 minutes 6 seconds
- **Channel**: LangChain
- **Views**: 40,461+ (as of Dec 2024)

### Decision: **USE BUILT-IN INTERRUPT FLOW** (No Custom UI Required)

**IMPORTANT UPDATE**: After researching LangChain 1.0 documentation, we discovered that `HumanInTheLoopMiddleware` provides a **built-in approval workflow** that the hosted Agent Chat UI already supports. **No custom frontend components are required.**

**Key Discovery**: The Agent Chat UI at https://agentchat.vercel.app already handles interrupt-based approval flows when:
1. Agent uses `HumanInTheLoopMiddleware`
2. A tool call triggers an interrupt
3. User is prompted to approve/edit/reject

**Video Reference (For Future Enhancement)**:

The generative UI video remains useful if you want to:
- Create custom-styled approval cards (beyond the default)
- Add rich recipe formatting in the approval UI
- Build a self-hosted frontend with custom components

**Concepts from Video (for future custom UI work)**:

1. **Custom Message Types**: LangGraph allows defining custom message types that carry UI component data.

2. **Frontend Rendering**: The frontend receives streamed messages and renders appropriate UI components.

3. **Tool-Based UI Generation**: Tools can return structured data interpreted as UI components.

**Deferred to Future Ticket**:

Custom frontend UI work should be a **separate ticket** if the built-in interrupt flow doesn't meet UX requirements. The base implementation can use `HumanInTheLoopMiddleware` without frontend changes.

**Alternatives Considered**:
- Custom generative UI components → Requires frontend work, defer to separate ticket
- Plain text confirmation → Less intuitive but works with no changes
- Built-in interrupt flow → **SELECTED** - Works with hosted Agent Chat UI

---

## 2. LangChain 1.0 Agent Architecture (UPDATED)

### Reference Documentation
- **URL**: https://reference.langchain.com/python/langchain/agents/
- **URL**: https://reference.langchain.com/python/langchain/middleware/
- **Purpose**: Updated LangChain 1.0 patterns for agents with human-in-the-loop

### Decision: Use `create_agent` with `HumanInTheLoopMiddleware`

**Rationale**: LangChain 1.0's `create_agent` now has built-in support for human-in-the-loop via middleware. **No separate LangGraph interrupt code required!**

**Key Discovery**: The `create_agent` function in LangChain 1.0 includes:
- `interrupt_before`: List of node names to interrupt before
- `interrupt_after`: List of node names to interrupt after
- `middleware`: Sequence of middleware including `HumanInTheLoopMiddleware`
- `checkpointer`: For state persistence across interrupts

**Key API Patterns**:

```python
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware

# HumanInTheLoopMiddleware provides approval workflow out of the box
hitl_middleware = HumanInTheLoopMiddleware(
    interrupt_on={
        "save_recipe_tool": True,  # Require approval for this tool
    },
    description_prefix="Recipe save requires approval"
)

agent = create_agent(
    model="anthropic:claude-sonnet-4-5-20250929",
    tools=[web_search, get_youtube_transcript, save_recipe_tool],
    system_prompt=system_prompt,
    middleware=[hitl_middleware],
    checkpointer=MemorySaver(),  # For state persistence
)
```

**HumanInTheLoopMiddleware Features**:
- `interrupt_on`: Mapping of tool name → allowed actions (approve, edit, reject)
- `description_prefix`: Context message for approval requests
- Automatic interruption when specified tools are called
- Standard interrupt/resume pattern compatible with Agent Chat UI

**Key Benefits**:
- **No custom frontend code needed** - Agent Chat UI already handles interrupt flows
- Built-in approve/edit/reject actions
- Works with existing deployed Agent Chat UI
- Cleaner than custom LangGraph interrupt nodes

**Alternatives Considered**:
- Custom LangGraph `interrupt()` → More code, requires frontend changes
- Polling-based approach → Higher latency, more complex
- Separate API calls → Breaks conversation flow

---

## 3. Save Implementation Pattern

### Decision: Simple Tool Call (No Subagent/Subgraph Needed)

**Rationale**: With `HumanInTheLoopMiddleware`, the save operation is just a **simple tool call**. The middleware handles the approval flow automatically. No complex subgraph or deep agents pattern required.

**Implementation**:

```python
from storage.repository import SQLiteRecipeRepository
from models.saved_recipe import SavedRecipe
from models.recipe import Recipe

async def save_recipe(
    name: str,
    recipe_type: str,
    ingredients: list[dict],
    instructions: list[str],
    prep_time: str | None = None,
    cook_time: str | None = None,
    servings: int | None = None,
    notes: str | None = None
) -> str:
    """
    Save a recipe to your collection.
    
    Call this when the user wants to save a recipe they like.
    The recipe data should be extracted from the conversation.
    
    Args:
        name: Recipe name
        recipe_type: Type (cocktail, food, dessert)
        ingredients: List of ingredients with name, quantity, unit
        instructions: List of preparation steps
        prep_time: Optional prep time
        cook_time: Optional cook time
        servings: Optional serving count
        notes: Optional notes or tips
    
    Returns:
        Confirmation message with saved recipe ID
    """
    saved = SavedRecipe(
        name=name,
        recipe_type=recipe_type,
        ingredients=ingredients,
        instructions=instructions,
        prep_time=prep_time,
        cook_time=cook_time,
        servings=servings,
        notes=notes
    )
    
    repo = SQLiteRecipeRepository()
    await repo.save(saved)
    
    return f"✓ Saved '{name}' to your collection! (ID: {saved.id})"
```

**Flow**:
1. User expresses satisfaction or requests save
2. Agent extracts recipe data from conversation context
3. Agent calls `save_recipe` tool with structured data
4. `HumanInTheLoopMiddleware` intercepts → shows approval in UI
5. User approves → tool executes → recipe saved
6. User declines → tool skipped → conversation continues

**Why Not Subgraph/Deep Agents**:
- Over-engineering for a simple CRUD operation
- Middleware already handles the approval flow
- Tool receives all data needed in one call
- No multi-step orchestration required

**Alternatives Considered**:
- Subgraph pattern → Over-engineered, not needed
- Deep agents → Overkill for single save operation
- **Simple tool + middleware → SELECTED** ✓

---

## 4. Database Storage Pattern

### Decision: SQLite with SQLAlchemy for Local Persistence

**Rationale**: For personal use, SQLite provides sufficient durability without deployment complexity. SQLAlchemy provides a clean ORM layer.

**Schema Design**:

```python
from sqlalchemy import Column, String, DateTime, JSON, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class SavedRecipe(Base):
    __tablename__ = "saved_recipes"
    
    id = Column(String, primary_key=True)  # UUID
    name = Column(String, nullable=False)
    recipe_type = Column(String, nullable=False)
    ingredients = Column(JSON, nullable=False)
    instructions = Column(JSON, nullable=False)
    prep_time_minutes = Column(Integer)  # Prep time in minutes
    cook_time_minutes = Column(Integer)  # Cook time in minutes
    is_deleted = Column(Boolean, default=False, index=True)  # Soft delete
    servings = Column(Integer)
    source_references = Column(JSON)
    notes = Column(String)
    user_notes = Column(String)
    tags = Column(JSON)
    saved_at = Column(DateTime, nullable=False)
    conversation_id = Column(String)  # Optional reference
```

**File Location**: `~/.recipe_creator/recipes.db` or `./data/recipes.db`

**Alternatives Considered**:
- PostgreSQL → Overkill for personal use
- JSON file → No query capabilities
- In-memory only → No persistence

---

## 5. Integration with Agent Chat UI

### Compatibility with agent-chat-ui

The existing frontend (`specs/3-agent-chat-frontend`) uses the Agent Chat UI which streams messages from LangGraph server.

**Key Integration Points**:

1. **Custom Message Types**: Agent Chat UI supports rendering custom components based on message metadata.

2. **Streaming**: Approval cards should stream as part of the normal message flow.

3. **User Input**: Button clicks send messages back through the same WebSocket connection.

**⚠️ NO FRONTEND CODE NEEDED FOR THIS TICKET**

The hosted Agent Chat UI already renders approval prompts for `HumanInTheLoopMiddleware` interrupts. It shows:
- Tool name and arguments (recipe data)
- Approve / Edit / Reject buttons

The TypeScript component below is **ONLY for a future enhancement ticket** if you want prettier custom cards:

<details>
<summary>Future Enhancement: Custom Recipe Card (SEPARATE TICKET)</summary>

```typescript
// FUTURE TICKET ONLY - Not needed for basic implementation
interface RecipeApprovalCardProps {
  recipe: Recipe;
  onApprove: () => void;
  onDecline: () => void;
}

const RecipeApprovalCard: React.FC<RecipeApprovalCardProps> = ({
  recipe,
  onApprove,
  onDecline
}) => (
  <Card>
    <CardHeader>{recipe.name}</CardHeader>
    <CardContent>
      <IngredientList ingredients={recipe.ingredients} />
      <InstructionList steps={recipe.instructions} />
    </CardContent>
    <CardFooter>
      <Button onClick={onApprove}>Save Recipe</Button>
      <Button variant="outline" onClick={onDecline}>Cancel</Button>
    </CardFooter>
  </Card>
);
```

</details>

---

## 6. Database Exploration Tool

### Decision: Read-Only SQL Query Tool with Guardrails

**Rationale**: Allow the agent to explore saved recipes using natural SQL queries, enabling flexible search and analysis without hardcoding every possible query pattern.

**Implementation**:

```python
import re
from storage.database import AsyncSessionLocal

# Blocked SQL patterns (case-insensitive)
BLOCKED_PATTERNS = [
    r'\bDELETE\b',
    r'\bDROP\b',
    r'\bTRUNCATE\b',
    r'\bCREATE\s+TABLE\b',
    r'\bALTER\s+TABLE\b',
    r'\bINSERT\b',
    r'\bUPDATE\b',
]

def validate_sql(query: str) -> tuple[bool, str]:
    """Check if SQL query is safe to execute."""
    query_upper = query.upper()
    
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, query_upper):
            return False, f"Blocked: {pattern.strip()} operations not allowed"
    
    # Must be a SELECT query
    if not query_upper.strip().startswith('SELECT'):
        return False, "Only SELECT queries are allowed"
    
    return True, "OK"

async def explore_recipes_db(sql_query: str) -> str:
    """
    Run a read-only SQL query on the saved recipes database.
    
    Use this to explore saved recipes with custom queries.
    Only SELECT queries are allowed - no modifications.
    
    Args:
        sql_query: A SELECT query to run against the saved_recipes table
        
    Available columns:
        - id (UUID)
        - name (text)
        - recipe_type (text: 'cocktail', 'food', 'dessert')
        - ingredients (JSON array)
        - instructions (JSON array)
        - prep_time_minutes (integer)
        - cook_time_minutes (integer)
        - servings (integer)
        - tags (JSON array)
        - saved_at (datetime)
        - is_deleted (boolean - filter with is_deleted = 0)
    
    Example queries:
        - "SELECT name, recipe_type FROM saved_recipes WHERE is_deleted = 0"
        - "SELECT * FROM saved_recipes WHERE recipe_type = 'cocktail' AND is_deleted = 0"
        - "SELECT name FROM saved_recipes WHERE ingredients LIKE '%bourbon%' AND is_deleted = 0"
        - "SELECT COUNT(*) FROM saved_recipes WHERE is_deleted = 0"
    
    Returns:
        Query results as formatted text, or error message
    """
    # Validate query
    is_valid, message = validate_sql(sql_query)
    if not is_valid:
        return f"❌ Query rejected: {message}"
    
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text(sql_query))
            rows = result.fetchall()
            
            if not rows:
                return "No results found."
            
            # Format results
            columns = result.keys()
            output = [" | ".join(str(col) for col in columns)]
            output.append("-" * len(output[0]))
            for row in rows[:50]:  # Limit to 50 rows
                output.append(" | ".join(str(val) for val in row))
            
            if len(rows) > 50:
                output.append(f"... and {len(rows) - 50} more rows")
            
            return "\n".join(output)
            
    except Exception as e:
        return f"❌ Query error: {str(e)}"
```

**Guardrails**:

| Blocked Operation | Reason |
|-------------------|--------|
| DELETE | Prevents data loss (use soft delete via is_deleted) |
| DROP | Prevents table destruction |
| TRUNCATE | Prevents mass data loss |
| CREATE TABLE | Prevents schema pollution |
| ALTER TABLE | Prevents schema changes |
| INSERT | Use `save_recipe` tool instead |
| UPDATE | Use dedicated update tool if needed |

**Use Cases**:
- "How many cocktail recipes do I have saved?"
- "Show me recipes that take less than 30 minutes"
- "Find recipes with chicken in the ingredients"
- "What recipes did I save this week?"

**Security Notes**:
- Query runs with read-only intent
- Results capped at 50 rows
- Only `saved_recipes` table accessible
- Soft-deleted records visible but agent should filter with `is_deleted = 0`

---

## 7. Satisfaction Detection Strategy

### Decision: Prompt-Based Detection with Explicit Triggers

**Rationale**: Rather than complex NLP sentiment analysis, leverage the LLM's understanding through system prompt instructions.

**Implementation**:

```text
# System prompt addition for satisfaction detection

When providing a recipe, watch for signals that the user is satisfied:
- Explicit praise: "This is great!", "Perfect!", "Love it"
- Intent to use: "I'm making this tonight", "Can't wait to try"
- Engagement questions: "What wine pairs with this?", "Can I substitute X?"

When you detect satisfaction, offer to save the recipe naturally:
"I'm glad you like it! Would you like me to save this recipe to your collection?"

If they agree, invoke the save_recipe_workflow tool.
```

**Tool Definition**:

```python
def save_recipe_workflow(recipe_context: str) -> str:
    """
    Initiate the save recipe workflow after user agrees to save.
    
    Args:
        recipe_context: Description of which recipe to save
        
    Returns:
        Confirmation message or approval card
    """
    # Triggers the save subgraph
    pass
```

**Alternatives Considered**:
- Separate sentiment classifier → Over-engineered
- Always offer to save → Annoying UX
- Never auto-detect → Misses opportunity

---

## 8. Project Structure Update

### Additional Files for Save Feature

```
recipe_creator/
├── ... (existing files)
├── storage/
│   └── database.py        # SQLAlchemy setup (no repository needed)
├── models/
│   ├── ... (existing)
│   └── saved_recipe.py    # SavedRecipeDB model
└── tools/
    └── recipe_storage.py  # 3 tools: save_recipe, delete_saved_recipe, explore_recipes_db
```

---

## Dependencies Summary

### New Dependencies

```
sqlalchemy>=2.0
aiosqlite          # For async SQLite support
```

### Updated Dependencies

```
langgraph>=0.2.0   # For interrupt and subgraph support
```

---

## Open Questions (Resolved)

| Question | Resolution |
|----------|------------|
| How to implement approval cards? | `HumanInTheLoopMiddleware` - built-in UI support |
| Where to store recipes? | SQLite with SQLAlchemy ORM |
| How to detect satisfaction? | Prompt-based with explicit triggers |
| Subagent or inline workflow? | Simple tool call + middleware (no subgraph) |
| Frontend integration? | No changes needed - hosted Agent Chat UI works |
| How to explore saved recipes? | `explore_recipes_db` tool with read-only SQL |

---

## References

1. **LangGraph Generative UI Tutorial**: https://www.youtube.com/watch?v=sCqN01R8nIQ
2. **LangGraph Documentation**: https://reference.langchain.com/python/langgraph/
3. **Deep Agents Reference**: https://reference.langchain.com/python/deepagents/
4. **Agent Chat UI Repository**: https://github.com/langchain-ai/agent-chat-ui

---

*Research complete. Ready for implementation planning.*

