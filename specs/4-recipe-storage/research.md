# Research Documentation: Recipe Storage

**Feature**: 4-recipe-storage  
**Date**: December 2, 2025  

---

## Research Areas

### 1. Image Generation Service

**Decision**: Google Nano Banana Pro via Google AI Studio / Gemini API

**Rationale**:
- Nano Banana Pro is Google's latest image generation model built on Gemini 3 Pro architecture
- Accessible through Google AI Studio and Gemini API (Python SDK available)
- High-quality food/drink image generation capabilities
- Integrates well with existing Google Cloud ecosystem

**Alternatives Considered**:
- DALL-E 3 (OpenAI): Good quality but separate API/billing
- Stable Diffusion: Requires self-hosting or third-party API
- fal.ai FLUX: Fast but less established

**Implementation Notes**:
- Use `google-generativeai` Python SDK
- Access via Gemini API with `imagen-3.0-generate-001` or Nano Banana Pro model ID
- Free tier: 2 images/day (consider paid tier for production)
- API Key: Use existing Google AI API key or create dedicated one

**Code Pattern**:
```python
import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_AI_API_KEY"))

def generate_recipe_image(recipe_name: str, description: str) -> str:
    """Generate an image for a recipe using Nano Banana Pro."""
    prompt = f"A professional food photography style image of {recipe_name}. {description}"
    
    response = genai.ImageGenerationModel("imagen-3.0-generate-001").generate_images(
        prompt=prompt,
        number_of_images=1,
    )
    
    # Save and return URL/path
    return save_image(response.images[0])
```

---

### 2. Persistent Storage

**Decision**: SQLite initially → PostgreSQL-ready with SQLAlchemy ORM

**Rationale**:
- SQLAlchemy ORM provides database-agnostic abstraction layer
- Start with SQLite for zero-config local development
- **Future: Tens of users** → PostgreSQL with connection pooling
- Same models work with both databases

**PostgreSQL Migration Complexity**: **LOW** ✅
- SQLAlchemy abstracts database differences
- Migration steps:
  1. Change `DATABASE_URL` env var from `sqlite:///recipes.db` to `postgresql://user:pass@host/db`
  2. Run schema migration (Alembic or manual)
  3. One-time data export/import script
- **Estimated effort: 1-2 hours**

**Alternatives Considered**:
- PostgreSQL from start: Overkill for MVP, adds deployment complexity
- JSON file: No query capabilities, no ACID
- MongoDB: Different paradigm, SQL better for structured recipes

**Schema Design** (PostgreSQL-compatible):
```sql
CREATE TABLE saved_recipes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    recipe_type VARCHAR(20) NOT NULL CHECK (recipe_type IN ('cocktail', 'food', 'dessert')),
    ingredients JSONB NOT NULL,      -- JSONB for efficient querying
    instructions JSONB NOT NULL,
    prep_time INTEGER,              -- Minutes
    cook_time INTEGER,              -- Minutes
    servings INTEGER CHECK (servings > 0),
    source_references JSONB,
    notes TEXT,
    image_url VARCHAR(500),          -- Cloud storage URL (GCS bucket)
    tags JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_recipe_name ON saved_recipes(name);
CREATE INDEX idx_recipe_type ON saved_recipes(recipe_type);
-- PostgreSQL only: GIN index for JSONB ingredient search
-- CREATE INDEX idx_recipe_ingredients ON saved_recipes USING GIN (ingredients);
```

**Future Multi-User Extension** (when scaling):
```sql
ALTER TABLE saved_recipes ADD COLUMN user_id UUID REFERENCES users(id);
CREATE INDEX idx_recipe_user ON saved_recipes(user_id);
```

---

### 2b. Image Storage

**Decision**: Google Cloud Storage (GCS) bucket

**Rationale**:
- Hundreds of images would overwhelm local pod storage
- GCS integrates naturally with Google AI (Nano Banana Pro)
- Scalable, durable, globally accessible
- Simple public URL for image_url field

**Alternatives Considered**:
- Local filesystem: Not scalable, lost on pod restart
- AWS S3: Good but adds another cloud provider
- Cloudflare R2: Cheaper but less Google integration

**Implementation**:
```python
from google.cloud import storage

def upload_recipe_image(image_data: bytes, recipe_id: str) -> str:
    """Upload image to GCS and return public URL."""
    client = storage.Client()
    bucket = client.bucket(os.getenv("GCS_BUCKET_NAME"))
    
    blob = bucket.blob(f"recipes/{recipe_id}.png")
    blob.upload_from_string(image_data, content_type="image/png")
    blob.make_public()
    
    return blob.public_url
```

**Required Setup**:
- GCS bucket with public read access
- Service account with Storage Object Admin role
- Environment: `GCS_BUCKET_NAME`, `GOOGLE_APPLICATION_CREDENTIALS`

---

### 3. Generative UI Pattern

**Decision**: LangGraph custom message types with Agent Chat UI rendering

**Rationale**:
- LangGraph supports custom message types that can be rendered specially in Agent Chat UI
- Reference tutorial: https://www.youtube.com/watch?v=sCqN01R8nIQ
- Allows visual confirmation cards without custom frontend development

**Implementation Pattern**:
- Define custom `RecipeCard` message type
- Return from agent as special tool output
- Agent Chat UI renders based on message type

**Code Pattern**:
```python
from typing import Literal
from pydantic import BaseModel
from models.recipe import RecipeType  # Use existing enum

class RecipeCardMessage(BaseModel):
    """Custom message type for visual recipe confirmation card."""
    type: Literal["recipe_card"] = "recipe_card"
    recipe_id: str
    recipe_name: str
    recipe_type: RecipeType  # Enum: cocktail, food, dessert
    prep_time: int | None    # Minutes (integer)
    servings: int | None
    image_url: str | None
    status: Literal["saved", "pending", "deleted"]
```

---

### 4. Agent Architecture

**Decision**: Minimal tools + SQL execution + Save Recipe subflow

**Rationale**:
- Too many tools overwhelm the agent and increase confusion
- Single SQL tool gives agent flexibility to write its own queries
- Save recipe is a complex flow → separate subagent with dedicated prompts
- Guardrails prevent destructive operations

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                     Main Recipe Agent                        │
│  Tools:                                                      │
│    - web_search (existing)                                   │
│    - get_youtube_transcript (existing)                       │
│    - execute_recipe_sql (NEW - read/write with guardrails)  │
│    - save_recipe (NEW - triggers subflow)                   │
├─────────────────────────────────────────────────────────────┤
│                    Save Recipe Subflow                       │
│  Triggered by: save_recipe tool                             │
│  Steps:                                                      │
│    1. Recipe Structuring Agent (dedicated prompt)           │
│    2. Image Generation Agent (dedicated prompt)             │
│    3. Database Insert + Return confirmation                 │
└─────────────────────────────────────────────────────────────┘
```

**New Tools (Only 2)**:

1. **`execute_recipe_sql`** - Direct SQL access with guardrails
   - Agent writes its own SELECT, INSERT, UPDATE queries
   - System prompt includes table schema
   - **Guardrails**:
     - No DROP, TRUNCATE, or ALTER statements
     - No DELETE statements (use soft delete via UPDATE)
     - UPDATE must include WHERE clause (single row)
     - No multi-table operations
     - Auto-inject `WHERE is_deleted = false` for SELECT queries
   - Future: Add user_id filter for multi-user

2. **`save_recipe`** - Triggers save subflow
   - Input: Raw recipe data from conversation
   - Kicks off Recipe Structuring Agent
   - Then Image Generation Agent
   - Returns confirmation with image URL

**Soft Delete Pattern**:
- `is_deleted` column (BOOLEAN, default false)
- "Delete" = `UPDATE saved_recipes SET is_deleted = true WHERE id = '...'`
- All SELECTs auto-filter `WHERE is_deleted = false`
- Benefits: Data recovery, audit trails, no orphaned GCS images

**Guardrail Implementation**:
```python
import re

FORBIDDEN_PATTERNS = [
    (r'\bDROP\b', "DROP statements not allowed"),
    (r'\bTRUNCATE\b', "TRUNCATE statements not allowed"),
    (r'\bALTER\b', "ALTER statements not allowed"),
    (r'\bDELETE\b', "DELETE not allowed - use UPDATE SET is_deleted = true"),
]

def validate_sql(query: str) -> tuple[bool, str]:
    """Validate SQL query against guardrails."""
    query_upper = query.upper()
    
    for pattern, error_msg in FORBIDDEN_PATTERNS:
        if re.search(pattern, query_upper):
            return False, error_msg
    
    # UPDATE must have WHERE
    if 'UPDATE' in query_upper and 'WHERE' not in query_upper:
        return False, "UPDATE requires WHERE clause"
    
    return True, ""

def inject_soft_delete_filter(query: str) -> str:
    """Auto-inject is_deleted = false for SELECT queries."""
    if query.strip().upper().startswith('SELECT'):
        if 'WHERE' in query.upper():
            # Add to existing WHERE
            return re.sub(r'\bWHERE\b', 'WHERE is_deleted = false AND ', query, flags=re.IGNORECASE)
        else:
            # Add WHERE clause before ORDER BY, LIMIT, or end
            return re.sub(r'(ORDER BY|LIMIT|$)', r'WHERE is_deleted = false \1', query, count=1, flags=re.IGNORECASE)
    return query
```

**Save Recipe Subflow Implementation**:

1. **Recipe Structuring** - Use LangChain `with_structured_output`:
```python
from langchain.chat_models import init_chat_model
from models.recipe import Recipe

# LangChain 1.0 structured output - validates against Pydantic schema
llm = init_chat_model(config.model)
structured_llm = llm.with_structured_output(Recipe)

# Returns validated Recipe instance, not raw JSON
recipe = structured_llm.invoke(
    "Structure this recipe: " + raw_recipe_data
)
```
**Benefits**: Auto-validation, type safety, no manual JSON parsing, retries on invalid output.

2. **Image Generation Prompt** - Pass full recipe context:
```text
You are creating a prompt for professional food photography image generation.

Given the following recipe details, create an optimized image generation prompt:

Recipe Name: {recipe.name}
Type: {recipe.recipe_type}
Key Ingredients: {', '.join([i.name for i in recipe.ingredients[:5]])}
Description: {recipe.notes or 'A delicious ' + recipe.recipe_type}

Create a detailed image prompt that:
- Specifies professional food/drink photography style
- For cocktails: crystal glassware, ice details, garnishes, bar lighting
- For food: appetizing plating, natural lighting, styled props
- For desserts: elegant presentation, soft lighting, appealing textures
- Describes colors based on the actual ingredients
- Keeps prompt under 200 words

Output ONLY the image generation prompt text.
```

---

### 5. System Prompt Updates

**Decision**: Extend default prompt with recipe memory instructions (schema in tool docstring)

**Changes Required**:
1. ~~Add table schema description~~ → **Not needed!** LangChain auto-injects tool docstrings
2. Add instruction to search recipe memory FIRST before web/YouTube
3. Add satisfaction detection patterns
4. Add save offer behavior guidelines

**Note**: Table schema and SQL rules are in the `execute_recipe_sql` tool docstring.
LangChain automatically includes tool descriptions in the agent context.

**Updated Prompt Additions**:
```text
## Recipe Memory Priority

ALWAYS check saved recipes FIRST before searching the web or YouTube.

When a user asks for a recipe:
1. First, query saved_recipes: SELECT * FROM saved_recipes WHERE name ILIKE '%query%' OR ingredients::text ILIKE '%query%'
2. If matches found, present them before offering external search
3. If no matches, then use web_search or get_youtube_transcript

## Saving Recipes

When you detect the user is pleased with a recipe (expressions like "perfect!", "I love this", "exactly what I wanted"):
- Offer to save the recipe to their collection
- If they confirm, use save_recipe tool with the recipe details
- The save flow will structure the recipe and generate an image
- A visual confirmation card will appear

If user rejects after seeing the confirmation:
- DELETE FROM saved_recipes WHERE id = 'recipe_id'

If user requests changes:
- UPDATE saved_recipes SET field = 'value' WHERE id = 'recipe_id'
```

---

## Dependencies

| Dependency | Purpose | Version |
|------------|---------|---------|
| google-generativeai | Nano Banana Pro image generation | Latest |
| google-cloud-storage | GCS bucket for image storage | Latest |
| sqlalchemy | Database ORM (SQLite → PostgreSQL ready) | 2.0+ |
| alembic | Database migrations (optional for MVP) | Latest |
| Pillow | Image processing before upload | Latest |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Image generation rate limits | Medium | Low | Graceful degradation, save recipe without image |
| SQL injection via agent | Medium | High | Guardrails + parameterized queries |
| Agent writes destructive SQL | Medium | High | Block DROP/TRUNCATE/ALTER, require WHERE |
| GCS bucket misconfiguration | Low | Medium | Terraform/IaC for consistent setup |
| PostgreSQL migration issues | Low | Low | SQLAlchemy abstraction, test migrations |

---

## Open Questions (Resolved)

1. ~~Which image generation service?~~ → Nano Banana Pro via Google AI
2. ~~What database for storage?~~ → SQLite initially, PostgreSQL-ready via SQLAlchemy
3. ~~How hard to migrate to PostgreSQL?~~ → **LOW** - just change connection string
4. ~~Where to store images?~~ → Google Cloud Storage bucket
5. ~~How many tools for agent?~~ → **2 only**: `execute_recipe_sql` + `save_recipe`
6. ~~How to prevent destructive SQL?~~ → Guardrails blocking DROP/TRUNCATE/ALTER, require WHERE
7. ~~How to render visual cards?~~ → LangGraph custom message types

---

*Research complete. Ready for implementation planning.*

