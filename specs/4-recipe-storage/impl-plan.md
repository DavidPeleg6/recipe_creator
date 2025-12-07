# Implementation Plan: Recipe Storage

**Feature**: 4-recipe-storage  
**Date**: December 2, 2025  
**Status**: Ready for Implementation  

---

## Overview

Add persistent storage for generated recipes with intelligent save workflow. When users express satisfaction, the agent offers to save recipes. On confirmation, recipes are stored with auto-generated images and displayed via visual confirmation cards.

---

## Technical Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.11+ |
| Database | SQLite → PostgreSQL (SQLAlchemy ORM) | 2.0+ |
| Image Generation | Google Nano Banana Pro (Gemini API) | Latest |
| Image Storage | Google Cloud Storage (GCS) | Latest |
| Agent Framework | LangChain + LangGraph | 1.0+ |
| Image Processing | Pillow | Latest |

**Migration Path**: SQLite for MVP → PostgreSQL for multi-user (change connection string only)

---

## Project Structure Changes

```
recipe_creator/
├── main.py                     # CLI entry point (unchanged)
├── agent.py                    # Agent factory (MODIFIED: add 2 new tools)
├── config.py                   # Configuration (MODIFIED: add GCS + Google AI keys)
├── langgraph.json              # LangGraph config (unchanged)
├── models/
│   ├── __init__.py
│   └── recipe.py               # MODIFIED: Add persistence fields (id, image_url, tags, etc.)
├── tools/
│   ├── __init__.py             # MODIFIED: export new tools
│   ├── web_search.py           # Existing
│   ├── youtube.py              # Existing
│   ├── execute_sql.py          # NEW: SQL execution with guardrails
│   └── save_recipe.py          # NEW: Save flow (structure + image gen + insert)
├── storage/
│   ├── __init__.py             # NEW: Storage module
│   ├── database.py             # NEW: SQLAlchemy setup (SQLite/PostgreSQL)
│   └── sql_guardrails.py       # NEW: SQL validation & guardrails
├── services/
│   ├── __init__.py             # NEW: Services module
│   ├── image_generation.py     # NEW: Nano Banana Pro integration
│   └── cloud_storage.py        # NEW: GCS upload for images
├── prompts/
│   ├── default_prompt.txt      # MODIFIED: Add SQL schema + memory instructions
│   ├── recipe_structuring.txt  # NEW: Prompt for formal recipe structure
│   ├── image_prompt_gen.txt    # NEW: Prompt for image generation prompts
│   └── healthy.txt             # Existing
├── recipes.db                  # SQLite database (gitignored, MVP only)
├── requirements.txt            # MODIFIED: Add new dependencies
└── .env.example                # MODIFIED: Add GCS + Google AI keys
```

**New Files**: 11  
**Modified Files**: 4

**Key Architecture Changes**:
- Only 2 tools for agent: `execute_recipe_sql` + `save_recipe`
- Agent writes own SQL queries (with guardrails)
- `save_recipe` triggers dedicated subflow with separate prompts
- Images stored in GCS bucket, not local filesystem  

---

## Implementation Tasks

### Phase 1: Storage Foundation

#### Task 1.1: Add Dependencies

Update `requirements.txt`:

```
# Existing dependencies...

# New for recipe storage
sqlalchemy>=2.0.0
google-generativeai>=0.3.0
Pillow>=10.0.0
```

Update `.env.example`:

```bash
# Existing...

# Google AI for image generation (Nano Banana Pro)
GOOGLE_AI_API_KEY=your-google-ai-api-key
```

**Effort**: 5 minutes

#### Task 1.2: Extend Existing Recipe Model

**File**: `models/recipe.py` (MODIFY existing)

Add persistence fields to the existing `Recipe` class:

```python
"""Recipe data models for the Recipe Agent."""

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
    name: str = Field(..., description="Ingredient name")
    quantity: str = Field(..., description="Amount (e.g., '2', '1/2')")
    unit: Optional[str] = Field(default=None, description="Measurement unit")
    notes: Optional[str] = Field(default=None, description="Preparation notes")


class Recipe(BaseModel):
    """Recipe model - used for both generation and persistence."""
    
    # Core recipe fields (existing)
    name: str = Field(..., min_length=1, max_length=200)
    recipe_type: RecipeType
    ingredients: list[Ingredient] = Field(..., min_length=1)
    instructions: list[str] = Field(..., min_length=1)
    prep_time: Optional[int] = Field(default=None, ge=0, description="Minutes")
    cook_time: Optional[int] = Field(default=None, ge=0, description="Minutes")
    servings: Optional[int] = Field(default=None, gt=0)
    source_references: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
    
    # NEW: Persistence fields
    id: UUID = Field(default_factory=uuid4)
    image_url: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
```

**Changes from existing**:
- `prep_time`/`cook_time`: `timedelta` → `int` (minutes)
- Added: `id`, `image_url`, `tags`, `is_deleted`, `created_at`, `last_accessed_at`

**Effort**: 10 minutes

#### Task 1.3: Create Database Module

**File**: `storage/database.py`

```python
"""SQLite database setup and session management."""

import os
from pathlib import Path

from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

# Default database path (in recipe_creator directory)
DEFAULT_DB_PATH = Path(__file__).parent.parent / "recipes.db"


class SavedRecipeTable(Base):
    """SQLAlchemy model for saved_recipes table."""
    
    __tablename__ = "saved_recipes"
    
    id = Column(String, primary_key=True)
    name = Column(String(200), nullable=False, index=True)
    recipe_type = Column(String(20), nullable=False, index=True)
    ingredients_json = Column(Text, nullable=False)
    instructions_json = Column(Text, nullable=False)
    prep_time = Column(Integer)  # Minutes
    cook_time = Column(Integer)  # Minutes
    servings = Column(Integer)
    source_references_json = Column(Text)
    notes = Column(Text)
    image_url = Column(String(500))
    tags_json = Column(Text)
    created_at = Column(DateTime, nullable=False)
    last_accessed_at = Column(DateTime, nullable=False)


def get_engine(db_path: str | Path | None = None):
    """Create SQLAlchemy engine."""
    path = db_path or os.getenv("RECIPE_DB_PATH", DEFAULT_DB_PATH)
    return create_engine(f"sqlite:///{path}", echo=False)


def init_database(db_path: str | Path | None = None):
    """Initialize database and create tables."""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine=None):
    """Get a new database session."""
    if engine is None:
        engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
```

**Effort**: 20 minutes

#### ~~Task 1.4: Create Repository Module~~ **REMOVED**

**No repository needed!** With the simplified architecture:
- `save_recipe` tool uses direct SQL INSERT
- `execute_recipe_sql` tool gives agent direct SQL access
- No intermediate CRUD layer required

**Effort**: 0 minutes (removed)

---

### Phase 2: Image Generation

#### Task 2.1: Create Image Generation Service

**File**: `services/image_generation.py`

```python
"""Recipe image generation using Google Nano Banana Pro."""

import os
from pathlib import Path
from uuid import uuid4

import google.generativeai as genai

# Images directory
IMAGES_DIR = Path(__file__).parent.parent / "images"
IMAGES_DIR.mkdir(exist_ok=True)


def configure_genai():
    """Configure Google Generative AI client."""
    api_key = os.getenv("GOOGLE_AI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_AI_API_KEY environment variable not set")
    genai.configure(api_key=api_key)


def generate_recipe_image(
    recipe_name: str,
    recipe_type: str,
    description: str | None = None,
) -> str | None:
    """
    Generate an image for a recipe using Nano Banana Pro.
    
    Args:
        recipe_name: Name of the recipe
        recipe_type: Type (cocktail, food, dessert)
        description: Optional additional description
        
    Returns:
        Path to saved image file, or None if generation failed
    """
    try:
        configure_genai()
        
        # Craft prompt based on recipe type
        if recipe_type == "cocktail":
            style = "professional bar photography, crystal clear glass, garnishes visible"
        elif recipe_type == "dessert":
            style = "professional food photography, appetizing presentation, soft lighting"
        else:
            style = "professional food photography, appetizing plating, natural lighting"
        
        prompt = f"A {style} image of {recipe_name}."
        if description:
            prompt += f" {description}"
        
        # Generate image using Imagen/Nano Banana Pro
        model = genai.ImageGenerationModel("imagen-3.0-generate-001")
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
        )
        
        if response.images:
            # Save image
            image_id = str(uuid4())[:8]
            filename = f"{recipe_name.lower().replace(' ', '_')}_{image_id}.png"
            filepath = IMAGES_DIR / filename
            
            # Save the image data
            response.images[0].save(filepath)
            
            return str(filepath)
        
        return None
        
    except Exception as e:
        print(f"Image generation failed: {e}")
        return None
```

**Effort**: 30 minutes

---

### Phase 3: Agent Tools (Minimal - Only 2 Tools)

#### Task 3.1: Create SQL Guardrails Module

**File**: `storage/sql_guardrails.py`

```python
"""SQL validation and guardrails for agent-written queries."""

import re
from typing import Tuple

# Patterns that are FORBIDDEN (including DELETE - use soft delete instead)
FORBIDDEN_PATTERNS = [
    (r'\bDROP\s+', "DROP statements are not allowed"),
    (r'\bTRUNCATE\s+', "TRUNCATE statements are not allowed"),
    (r'\bALTER\s+', "ALTER statements are not allowed"),
    (r'\bCREATE\s+', "CREATE statements are not allowed"),
    (r'\bGRANT\s+', "GRANT statements are not allowed"),
    (r'\bREVOKE\s+', "REVOKE statements are not allowed"),
    (r'\bDELETE\s+', "DELETE not allowed - use UPDATE SET is_deleted = true"),
]


def validate_sql(query: str) -> Tuple[bool, str]:
    """
    Validate SQL query against guardrails.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    query_upper = query.upper().strip()
    
    # Check forbidden patterns
    for pattern, error_msg in FORBIDDEN_PATTERNS:
        if re.search(pattern, query_upper, re.IGNORECASE):
            return False, error_msg
    
    # UPDATE must have WHERE clause
    if 'UPDATE' in query_upper and 'WHERE' not in query_upper:
        return False, "UPDATE statements must include a WHERE clause"
    
    return True, ""


def inject_soft_delete_filter(query: str) -> str:
    """
    Auto-inject is_deleted = false filter for SELECT queries.
    
    Transforms:
        SELECT * FROM saved_recipes WHERE name ILIKE '%x%'
    To:
        SELECT * FROM saved_recipes WHERE is_deleted = false AND name ILIKE '%x%'
    """
    if not query.strip().upper().startswith('SELECT'):
        return query
    
    query_upper = query.upper()
    
    if 'WHERE' in query_upper:
        # Insert after WHERE
        return re.sub(
            r'\bWHERE\b',
            'WHERE is_deleted = false AND ',
            query,
            count=1,
            flags=re.IGNORECASE
        )
    else:
        # Insert WHERE before ORDER BY, LIMIT, GROUP BY, or at end
        patterns = [r'\bORDER\s+BY\b', r'\bLIMIT\b', r'\bGROUP\s+BY\b', r'$']
        for pattern in patterns:
            if re.search(pattern, query_upper):
                return re.sub(
                    pattern,
                    f' WHERE is_deleted = false \\g<0>',
                    query,
                    count=1,
                    flags=re.IGNORECASE
                ).strip()
    
    return query + ' WHERE is_deleted = false'


def is_read_only(query: str) -> bool:
    """Check if query is read-only (SELECT)."""
    return query.strip().upper().startswith('SELECT')
```

**Effort**: 30 minutes

#### Task 3.2: Create SQL Execution Tool

**File**: `tools/execute_sql.py`

```python
"""SQL execution tool with guardrails for agent use."""

from storage.database import get_session
from storage.sql_guardrails import validate_sql, inject_soft_delete_filter
from sqlalchemy import text


def execute_recipe_sql(query: str) -> dict:
    """
    Execute a SQL query against the recipe database.
    
    The agent writes SQL queries directly. SELECT queries auto-filter is_deleted = false.
    
    GUARDRAILS:
    - No DROP, TRUNCATE, ALTER, CREATE, GRANT, REVOKE
    - No DELETE (use UPDATE SET is_deleted = true for soft delete)
    - UPDATE MUST include WHERE clause
    - SELECT auto-filters WHERE is_deleted = false
    
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
    - image_url (VARCHAR 500): GCS URL
    - tags (JSONB): Array of strings
    - is_deleted (BOOLEAN): Soft delete flag (default: false)
    - created_at, last_accessed_at (TIMESTAMP)
    
    SOFT DELETE: To "delete" a recipe, use:
        UPDATE saved_recipes SET is_deleted = true WHERE id = 'uuid'
    
    Args:
        query: SQL query to execute
        
    Returns:
        Query results or error message
    """
    # Validate query against guardrails
    is_valid, error_msg = validate_sql(query)
    if not is_valid:
        return {
            "status": "error",
            "error": f"Query blocked: {error_msg}",
            "query": query,
        }
    
    # Auto-inject is_deleted filter for SELECT queries
    processed_query = inject_soft_delete_filter(query)
    
    try:
        session = get_session()
        result = session.execute(text(processed_query))
        
        # Handle SELECT queries
        if processed_query.strip().upper().startswith('SELECT'):
            rows = result.fetchall()
            columns = result.keys() if rows else []
            return {
                "status": "success",
                "rows": [dict(zip(columns, row)) for row in rows],
                "count": len(rows),
            }
        
        # Handle INSERT/UPDATE/DELETE
        session.commit()
        return {
            "status": "success",
            "rows_affected": result.rowcount,
            "message": f"Query executed successfully. {result.rowcount} row(s) affected.",
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "query": query,
        }
```

**Effort**: 30 minutes

#### Task 3.3: Create Save Recipe Tool

**File**: `tools/save_recipe.py`

```python
"""Save recipe tool - structures recipe, generates image, and inserts to DB."""

import json
from uuid import uuid4

from langchain.chat_models import init_chat_model
from google.cloud import storage
import google.generativeai as genai

from config import config
from storage.database import get_session
from sqlalchemy import text
from models.recipe import Recipe  # Pydantic schema for validation


# Load dedicated prompts
IMAGE_PROMPT_TEMPLATE = """You are creating a prompt for professional food photography image generation.

Given the following recipe details, create an optimized image generation prompt:

Recipe Name: {name}
Type: {recipe_type}
Key Ingredients: {key_ingredients}
Description: {description}

Create a detailed image prompt that:
- Specifies professional food/drink photography style
- For cocktails: crystal glassware, ice details, garnishes, bar lighting
- For food: appetizing plating, natural lighting, styled props
- For desserts: elegant presentation, soft lighting, appealing textures
- Describes colors based on the actual ingredients
- Keeps prompt under 200 words

Output ONLY the image generation prompt text."""


def save_recipe(raw_recipe_data: str) -> dict:
    """
    Save a recipe to the user's personal collection with auto-generated image.
    
    WHEN TO USE:
    - User explicitly says "save this", "keep this recipe", "add to favorites"
    - User confirms after you offer to save (e.g., "yes, save it")
    - Do NOT use just because user likes a recipe - always ask first!
    
    WHAT TO INCLUDE in raw_recipe_data:
    - Recipe name, ingredients with quantities, step-by-step instructions
    - Prep time and cook time (in minutes), servings
    - Recipe type: "cocktail", "food", or "dessert"
    - Source URLs (if any), tips or variations
    
    Args:
        raw_recipe_data: Complete recipe information as a string
        
    Returns:
        dict with status, recipe_id, recipe_name, image_url, message
    
    After save, show user the image_url. If they reject, use execute_recipe_sql
    to soft-delete: UPDATE saved_recipes SET is_deleted = true WHERE id = '...'
    """
    try:
        # Step 1: Structure the recipe using LangChain with_structured_output
        # This auto-validates against Pydantic schema - no manual JSON parsing!
        llm = init_chat_model(config.model)
        structured_llm = llm.with_structured_output(Recipe)
        
        recipe = structured_llm.invoke(
            f"Structure this recipe into the required format:\n\n{raw_recipe_data}"
        )
        recipe_id = str(recipe.id)
        
        # Step 2: Generate image prompt with FULL recipe context
        key_ingredients = ', '.join([i.name for i in recipe.ingredients[:5]])
        description = recipe.notes or f"A delicious {recipe.recipe_type.value}"
        
        image_prompt_request = IMAGE_PROMPT_TEMPLATE.format(
            name=recipe.name,
            recipe_type=recipe.recipe_type.value,
            key_ingredients=key_ingredients,
            description=description,
        )
        
        image_prompt_response = llm.invoke(image_prompt_request)
        
        image_prompt = image_prompt_response.content
        
        # Step 3: Generate image with Nano Banana Pro
        genai.configure(api_key=config.google_ai_api_key)
        image_model = genai.ImageGenerationModel("imagen-3.0-generate-001")
        image_response = image_model.generate_images(
            prompt=image_prompt,
            number_of_images=1,
        )
        
        # Step 4: Upload to GCS
        image_url = None
        if image_response.images:
            gcs_client = storage.Client()
            bucket = gcs_client.bucket(config.gcs_bucket_name)
            blob = bucket.blob(f"recipes/{recipe_id}.png")
            blob.upload_from_string(image_response.images[0]._image_bytes, content_type="image/png")
            blob.make_public()
            image_url = blob.public_url
        
        # Step 5: Insert into database using validated Pydantic model
        session = get_session()
        insert_query = text("""
            INSERT INTO saved_recipes (id, name, recipe_type, ingredients, instructions,
                prep_time, cook_time, servings, source_references, notes, image_url, tags,
                is_deleted, created_at, last_accessed_at)
            VALUES (:id, :name, :recipe_type, :ingredients, :instructions,
                :prep_time, :cook_time, :servings, :source_references, :notes, :image_url, :tags,
                false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """)
        
        # recipe is already a validated Recipe Pydantic model
        session.execute(insert_query, {
            "id": recipe_id,
            "name": recipe.name,
            "recipe_type": recipe.recipe_type.value,
            "ingredients": json.dumps([i.model_dump() for i in recipe.ingredients]),
            "instructions": json.dumps(recipe.instructions),
            "prep_time": recipe.prep_time,  # Integer (minutes)
            "cook_time": recipe.cook_time,  # Integer (minutes)
            "servings": recipe.servings,
            "source_references": json.dumps(recipe.source_references),
            "notes": recipe.notes,
            "image_url": image_url,
            "tags": json.dumps(recipe.tags),
        })
        session.commit()
        
        return {
            "status": "saved",
            "recipe_id": recipe_id,
            "recipe_name": recipe.name,
            "image_url": image_url,
            "message": f"Recipe '{recipe.name}' saved successfully!",
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to save recipe: {str(e)}",
        }
```

**Effort**: 60 minutes

#### Task 3.4: Create GCS Upload Service

**File**: `services/cloud_storage.py`

```python
"""Google Cloud Storage service for recipe images."""

import os
from google.cloud import storage


def get_gcs_client():
    """Get authenticated GCS client."""
    return storage.Client()


def upload_image(image_data: bytes, recipe_id: str) -> str:
    """
    Upload image to GCS and return public URL.
    
    Args:
        image_data: Raw image bytes
        recipe_id: Recipe UUID for filename
        
    Returns:
        Public URL of uploaded image
    """
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(f"recipes/{recipe_id}.png")
    
    blob.upload_from_string(image_data, content_type="image/png")
    blob.make_public()
    
    return blob.public_url


def delete_image(recipe_id: str) -> bool:
    """Delete image from GCS."""
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    
    try:
        client = get_gcs_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(f"recipes/{recipe_id}.png")
        blob.delete()
        return True
    except Exception:
        return False
```

**Effort**: 15 minutes

---

### Phase 4: Agent Integration

#### Task 4.1: Update System Prompt with SQL Schema

**File**: `prompts/default_prompt.txt` (append to existing)

```text
## Recipe Memory Priority

NOTE: Table schema, SQL rules, and soft delete instructions are in the 
execute_recipe_sql tool docstring. LangChain auto-injects tool descriptions.

ALWAYS check saved recipes FIRST before searching the web or YouTube.

When a user asks for a recipe:
1. First, query saved_recipes: 
   SELECT id, name, recipe_type, tags FROM saved_recipes 
   WHERE name ILIKE '%query%' OR ingredients::text ILIKE '%query%'
   (is_deleted = false is auto-added)
2. If matches found, present them before offering external search
3. If no matches, then use web_search or get_youtube_transcript

## Saving Recipes

When you detect the user is pleased with a recipe (expressions like "perfect!", "I love this", "exactly what I wanted"):
- Offer to save the recipe to their collection
- If they confirm, use save_recipe tool with the raw recipe details
- The save flow will structure the recipe and generate an image automatically
- A visual confirmation card will appear

If user rejects after seeing the confirmation (SOFT DELETE):
- UPDATE saved_recipes SET is_deleted = true WHERE id = 'recipe_id'

If user requests changes:
- UPDATE saved_recipes SET field = 'value' WHERE id = 'recipe_id'

When listing recipes (headers only):
- SELECT id, name, recipe_type, tags FROM saved_recipes

When retrieving full recipe:
- SELECT * FROM saved_recipes WHERE id = 'recipe_id' OR name ILIKE '%name%'
```

**Effort**: 20 minutes

#### Task 4.2: Recipe Structuring with `with_structured_output`

**No separate prompt file needed** - LangChain's `with_structured_output` uses the Pydantic model schema directly.

```python
from langchain.chat_models import init_chat_model
from models.recipe import Recipe

# LangChain 1.0 with_structured_output - auto-validates against Pydantic schema
llm = init_chat_model(config.model)
structured_llm = llm.with_structured_output(Recipe)

# Returns a validated Recipe instance, not raw JSON
# LangChain handles: schema extraction, validation, retries on invalid output
recipe = structured_llm.invoke(
    f"Structure this recipe into the required format:\n\n{raw_recipe_data}"
)
```

**Benefits over manual JSON parsing**:
- ✅ Auto-validation against Pydantic schema
- ✅ Type safety (returns `Recipe`, not `dict`)
- ✅ Auto-retry on validation failures
- ✅ No manual `json.loads()` or error handling

**File**: `prompts/image_prompt_gen.txt`

```text
You are creating a prompt for professional food photography image generation.

Given the following recipe details, create an optimized image generation prompt:

Recipe Name: {name}
Type: {recipe_type}
Key Ingredients: {key_ingredients}
Description: {description}

Create a detailed image prompt that:
- Specifies professional food/drink photography style
- For cocktails: crystal glassware, ice details, garnishes, bar lighting
- For food: appetizing plating, natural lighting, styled props
- For desserts: elegant presentation, soft lighting, appealing textures
- Describes colors based on the ACTUAL ingredients listed above
- Keeps prompt under 200 words

Output ONLY the image generation prompt text.
```

**Effort**: 10 minutes

#### Task 4.3: Update Agent Factory (Only 2 New Tools)

**File**: `agent.py` (modify existing)

```python
"""Agent factory for Recipe Agent."""

from langchain.agents import create_agent

from config import config
from tools.web_search import web_search
from tools.youtube import get_youtube_transcript
from tools.execute_sql import execute_recipe_sql
from tools.save_recipe import save_recipe


def create_recipe_agent(model: str | None = None, system_prompt: str | None = None):
    """Create and return a configured recipe agent.

    Args:
        model: Model identifier (default from config)
        system_prompt: Custom system prompt (default loaded from prompt file)

    Returns:
        Configured LangChain agent (CompiledStateGraph)
    """
    return create_agent(
        model=model or config.model,
        tools=[
            # Existing tools
            web_search,
            get_youtube_transcript,
            # Recipe storage (ONLY 2 new tools)
            execute_recipe_sql,  # Agent writes own SQL with guardrails
            save_recipe,         # Triggers subflow for structuring + image gen
        ],
        system_prompt=system_prompt or config.system_prompt,
    )


# Pre-compiled graph instance for LangGraph server
graph = create_recipe_agent()
```

**Effort**: 10 minutes

#### Task 4.4: Update Configuration

**File**: `config.py` (add GCS + Google AI keys)

```python
# Add to Config class:
google_ai_api_key: str | None = Field(
    default_factory=lambda: os.getenv("GOOGLE_AI_API_KEY")
)
gcs_bucket_name: str = Field(
    default_factory=lambda: os.getenv("GCS_BUCKET_NAME", "recipe-images")
)
```

**File**: `.env.example` (add new variables)

```bash
# Google AI for image generation (Nano Banana Pro)
GOOGLE_AI_API_KEY=your-google-ai-api-key

# Google Cloud Storage for recipe images
GCS_BUCKET_NAME=your-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

**Effort**: 10 minutes

---

### Phase 5: Generative UI (Optional Enhancement)

#### Task 5.1: Implement Custom Message Type

This phase implements the visual confirmation card using LangGraph's custom message types. Reference: https://www.youtube.com/watch?v=sCqN01R8nIQ

**Note**: This requires corresponding frontend changes in Agent Chat UI. If using the hosted version, this may be limited. For full control, consider running Agent Chat UI locally.

**File**: `models/ui_messages.py` (NEW)

```python
"""Custom message types for generative UI."""

from typing import Literal
from pydantic import BaseModel


class RecipeCardMessage(BaseModel):
    """Custom message type rendered as visual card in UI."""
    
    type: Literal["recipe_card"] = "recipe_card"
    recipe_id: str
    recipe_name: str
    recipe_type: RecipeType  # Enum from models.recipe
    prep_time: int | None = None  # Minutes (integer)
    servings: int | None = None
    image_url: str | None = None
    status: Literal["saved", "pending", "deleted"] = "saved"
```

**Effort**: 30 minutes (basic), 2+ hours (full UI integration)

---

## Acceptance Criteria Mapping

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| FR-1: Satisfaction Detection | System prompt instructions | Planned |
| FR-2: Save Offer Prompt | System prompt behavior | Planned |
| FR-3: Recipe Persistence | SQLite/PostgreSQL + SQLAlchemy | Planned |
| FR-4: Image Generation | Nano Banana Pro + GCS storage | Planned |
| FR-5: Visual Confirmation | Custom message types | Planned |
| FR-6: Recipe Retrieval | Agent SQL queries | Planned |
| FR-7: Categorization | Tags + recipe_type in SQL | Planned |
| FR-8: Memory Search Priority | System prompt + SQL query | Planned |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| SQL injection via agent | Guardrails block DROP/ALTER, require WHERE |
| Agent writes destructive SQL | Validate all queries, block dangerous patterns |
| Google AI API rate limits | Graceful degradation: save without image |
| GCS bucket misconfiguration | Clear setup docs, test permissions |
| PostgreSQL migration issues | SQLAlchemy abstraction, same models work |
| Subflow prompt failures | Fallback to basic structure, log errors |

---

## Testing Strategy

Manual testing for personal use:

1. **SQL Guardrails**: Try DROP TABLE → Should be blocked
2. **Save Flow**: Generate recipe → Express satisfaction → Save → Verify image in GCS
3. **Search Memory**: Save recipe with bourbon → SQL search → Verify results
4. **List Recipes**: Agent writes SELECT for headers only
5. **Delete Flow**: Save → Reject → Agent DELETE with WHERE
6. **Update Flow**: Save → Request change → Agent UPDATE with WHERE
7. **Priority Check**: Save "Old Fashioned" → Ask for it → SQL finds saved first

---

## Effort Estimate

| Phase | Tasks | Time |
|-------|-------|------|
| Phase 1: Storage Foundation | 4 | ~1.5 hours |
| Phase 2: Image Gen + GCS | 2 | ~45 min |
| Phase 3: Agent Tools (2 only) | 4 | ~2 hours |
| Phase 4: Agent Integration | 4 | ~1 hour |
| Phase 5: Generative UI | 1 | ~30 min (basic) |
| **Total** | **15** | **~6 hours** |

---

## Next Steps

1. Run `/speckit.tasks` to generate detailed implementation tasks
2. Implement in order: storage → image gen → tools → agent → UI
3. Test each phase before proceeding

---

*Implementation plan complete. Ready for task breakdown.*

