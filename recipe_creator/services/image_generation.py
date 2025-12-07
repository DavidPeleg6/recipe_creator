"""Recipe image generation using Google Imagen via Vertex AI."""

import os
import base64
import requests
from typing import Optional

from loguru import logger
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree


def _log_to_langsmith(message: str, level: str = "info") -> None:
    """Log message to both loguru and LangSmith trace metadata."""
    # Log to loguru
    getattr(logger, level)(message)
    
    # Add to LangSmith trace if we're in a traced context
    try:
        run_tree = get_current_run_tree()
        if run_tree:
            # Add log to the run's metadata
            if not run_tree.extra:
                run_tree.extra = {}
            if "logs" not in run_tree.extra:
                run_tree.extra["logs"] = []
            run_tree.extra["logs"].append({"level": level, "message": message})
    except Exception:
        pass  # Not in a traced context, that's fine


@traceable(name="generate_recipe_image")
def generate_recipe_image(
    image_prompt: str,
    recipe_name: str,
) -> Optional[bytes]:
    """
    Generate an image for a recipe using Gemini 2.0 Flash.
    
    Note: Imagen 3 requires Vertex AI (GCP project), not available via AI Studio API key.
    Gemini 2.0 Flash experimental supports image generation and works with AI Studio keys.
    
    Args:
        image_prompt: The optimized prompt for image generation
        recipe_name: Name of the recipe (for logging)
        
    Returns:
        Raw image bytes if successful, None if generation failed
    """
    api_key = os.getenv("GOOGLE_AI_API_KEY")
    if not api_key:
        _log_to_langsmith(
            f"Image generation skipped for '{recipe_name}': GOOGLE_AI_API_KEY not set",
            "warning"
        )
        return None
    
    try:
        # Use Gemini 2.0 Flash experimental - supports image generation with AI Studio API key
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": f"Generate an image: {image_prompt}"}]
            }],
            "generationConfig": {
                "responseModalities": ["image", "text"],
            }
        }
        
        _log_to_langsmith(f"Generating image with Gemini 2.0 for '{recipe_name}'", "info")
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            candidates = result.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                for part in parts:
                    if "inlineData" in part:
                        image_b64 = part["inlineData"].get("data")
                        if image_b64:
                            _log_to_langsmith(f"Image generation succeeded for '{recipe_name}'", "success")
                            return base64.b64decode(image_b64)
        
        _log_to_langsmith(
            f"Image generation failed for '{recipe_name}': HTTP {response.status_code}",
            "error"
        )
        return None
        
    except Exception as e:
        _log_to_langsmith(f"Image generation failed for '{recipe_name}': {e}", "error")
        return None


