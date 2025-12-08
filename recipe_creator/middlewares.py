"""Middleware helpers for the Recipe Agent."""

from langchain.agents.middleware import (
    HumanInTheLoopMiddleware,
    InterruptOnConfig,
)


hitl_middleware = HumanInTheLoopMiddleware(
    interrupt_on={
        "save_recipe": InterruptOnConfig(
            allowed_decisions=["approve", "edit", "reject"],
            description="Review the recipe details before saving.",
            args_schema={
                "type": "object",
                "required": ["name", "recipe_type", "ingredients", "instructions"],
                "properties": {
                    "name": {"type": "string", "title": "Name"},
                    "recipe_type": {
                        "type": "string",
                        "enum": ["cocktail", "food", "dessert"],
                        "title": "Recipe Type",
                    },
                    "ingredients": {
                        "type": "array",
                        "title": "Ingredients",
                        "items": {
                            "type": "object",
                            "required": ["name", "quantity"],
                            "properties": {
                                "name": {"type": "string", "title": "Name"},
                                "quantity": {"type": "string", "title": "Quantity"},
                                "unit": {"type": "string", "title": "Unit"},
                            },
                        },
                    },
                    "instructions": {
                        "type": "array",
                        "title": "Instructions (steps)",
                        "items": {
                            "type": "string",
                            "title": "Step",
                            "format": "textarea",
                        },
                        "minItems": 1,
                    },
                    "prep_time_minutes": {"type": "integer", "title": "Prep Time (min)"},
                    "cook_time_minutes": {"type": "integer", "title": "Cook Time (min)"},
                    "servings": {"type": "integer", "title": "Servings"},
                    "notes": {"type": "string", "title": "Notes"},
                    "user_notes": {"type": "string", "title": "User Notes"},
                    "tags": {
                        "type": "array",
                        "title": "Tags",
                        "items": {"type": "string"},
                    },
                    "source_references": {
                        "type": "array",
                        "title": "Source References",
                        "items": {"type": "string"},
                    },
                    "conversation_id": {"type": "string", "title": "Conversation ID"},
                },
            },
        )
    }
)


__all__ = [
    "hitl_middleware",
]

