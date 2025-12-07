"""Save recipe tool - structures recipe, generates image, and inserts to DB."""

import asyncio
import json
from pathlib import Path
from typing import Optional

from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langsmith import traceable
from loguru import logger
from sqlalchemy import text

from config import config
from storage.database import init_database, get_session
from services.image_generation import generate_recipe_image
from services.cloud_storage import upload_image
from models.recipe import Recipe


# Load image prompt template at module level
IMAGE_PROMPT_TEMPLATE = (
    Path(__file__).parent.parent / "prompts" / "image_prompt_gen.txt"
).read_text().strip()


@traceable(name="structure_recipe_and_prompt")
async def _structure_recipe_and_prompt(raw_recipe_data: str) -> tuple[Recipe, str]:
    """Structure raw recipe text and generate image prompt (async)."""
    from uuid import uuid4
    
    llm = init_chat_model(config.model)
    
    # Structure the recipe using async invoke
    recipe = await llm.with_structured_output(Recipe).ainvoke(
        f"Structure this recipe into the required format:\n\n{raw_recipe_data}"
    )
    
    # Generate a real UUID - LLM often outputs placeholder zeros
    recipe.id = uuid4()
    
    # Generate image prompt
    key_ingredients = ', '.join([i.name for i in recipe.ingredients[:5]])
    description = recipe.notes or f"A delicious {recipe.recipe_type.value}"
    
    image_prompt_response = await llm.ainvoke(
        IMAGE_PROMPT_TEMPLATE.format(
            name=recipe.name,
            recipe_type=recipe.recipe_type.value,
            key_ingredients=key_ingredients,
            description=description,
        )
    )
    
    return recipe, image_prompt_response.content


@traceable(name="create_recipe_image")
def _create_recipe_image_sync(recipe: Recipe, image_prompt: str) -> Optional[str]:
    """Generate image and upload (sync - uses requests). Returns storage_url."""
    if not config.google_ai_api_key:
        logger.warning("Image generation skipped: missing GOOGLE_AI_API_KEY")
        return None
    
    try:
        image_bytes = generate_recipe_image(
            image_prompt=image_prompt,
            recipe_name=recipe.name,
        )
        if not image_bytes:
            return None
        
        # Upload to storage (GCS or local fallback)
        try:
            return upload_image(
                image_data=image_bytes,
                recipe_id=str(recipe.id),
                bucket_name=config.gcs_bucket_name,
            )
        except Exception as e:
            logger.warning(f"Storage upload failed: {e}")
            return None
        
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return None


@traceable(name="insert_recipe_to_db")
def _insert_recipe_sync(recipe: Recipe, image_url: Optional[str]) -> None:
    """Insert recipe into database (sync)."""
    session = get_session()
    try:
        session.execute(
            text("""
                INSERT INTO saved_recipes (
                    id, name, recipe_type, ingredients, instructions,
                    prep_time, cook_time, servings, source_references, notes, 
                    image_url, tags, is_deleted, created_at, last_accessed_at
                ) VALUES (
                    :id, :name, :recipe_type, :ingredients, :instructions,
                    :prep_time, :cook_time, :servings, :source_references, :notes, 
                    :image_url, :tags, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            """),
            {
                "id": str(recipe.id),
                "name": recipe.name,
                "recipe_type": recipe.recipe_type.value,
                "ingredients": json.dumps([i.model_dump() for i in recipe.ingredients]),
                "instructions": json.dumps(recipe.instructions),
                "prep_time": recipe.prep_time,
                "cook_time": recipe.cook_time,
                "servings": recipe.servings,
                "source_references": json.dumps(recipe.source_references),
                "notes": recipe.notes,
                "image_url": image_url,
                "tags": json.dumps(recipe.tags),
            }
        )
        session.commit()
    finally:
        session.close()


@tool
async def save_recipe(raw_recipe_data: str) -> dict:
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
        # Init DB in thread (blocking)
        await asyncio.to_thread(init_database)
        
        # LLM calls are async via LangChain
        recipe, image_prompt = await _structure_recipe_and_prompt(raw_recipe_data)
        
        # Image generation uses requests (blocking) - run in thread
        storage_url = await asyncio.to_thread(
            _create_recipe_image_sync, recipe, image_prompt
        )
        
        # DB insert is blocking - run in thread
        await asyncio.to_thread(_insert_recipe_sync, recipe, storage_url)
        
        # NOTE: Don't return data_url to LLM - base64 images are huge and blow up context
        # The frontend can fetch the image separately using storage_url or recipe_id
        
        return {
            "status": "saved",
            "recipe_id": str(recipe.id),
            "recipe_name": recipe.name,
            "image_url": storage_url,  # URL only, no base64 data
            "message": f"Recipe '{recipe.name}' saved successfully!" + (
                "" if storage_url else " (Image generation unavailable)"
            ),
        }
        
    except Exception as e:
        logger.error(f"Save recipe failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to save recipe: {str(e)}",
        }
