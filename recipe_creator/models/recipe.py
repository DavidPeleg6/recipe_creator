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

    name: str = Field(..., min_length=1, max_length=100, description="Ingredient name")
    quantity: str = Field(..., min_length=1, description="Amount (e.g., '2', '1/2')")
    unit: Optional[str] = Field(default=None, description="Measurement unit (e.g., 'oz', 'cups', 'grams', 'ml')")
    notes: Optional[str] = Field(default=None, description="Preparation notes (e.g., 'diced', 'chilled')")


class Recipe(BaseModel):
    """Recipe model - used for both generation and persistence.
    
    Consolidated from original Recipe + persistence fields.
    Changes from original:
    - prep_time/cook_time: timedelta → int (minutes)
    - Added: id, image_url, tags, is_deleted, created_at, last_accessed_at
    """

    # Core recipe fields
    name: str = Field(..., min_length=1, max_length=200, description="Recipe name")
    recipe_type: RecipeType = Field(..., description="Type of recipe")
    ingredients: list[Ingredient] = Field(..., min_length=1, description="List of ingredients")
    instructions: list[str] = Field(..., min_length=1, description="Ordered preparation steps")
    prep_time: Optional[int] = Field(default=None, ge=0, description="Preparation time in minutes")
    cook_time: Optional[int] = Field(default=None, ge=0, description="Cooking time in minutes (for food)")
    servings: Optional[int] = Field(default=None, gt=0, description="Number of servings")
    source_references: list[str] = Field(default_factory=list, description="Source URLs")
    notes: Optional[str] = Field(default=None, description="Tips or variations")

    # Persistence fields (NEW)
    id: UUID = Field(default_factory=uuid4, description="Unique recipe identifier")
    image_url: Optional[str] = Field(default=None, description="GCS URL for generated image")
    tags: list[str] = Field(default_factory=list, description="User-defined and auto-generated tags")
    is_deleted: bool = Field(default=False, description="Soft delete flag")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When recipe was saved")
    last_accessed_at: datetime = Field(default_factory=datetime.utcnow, description="Last retrieval time")

    class Config:
        from_attributes = True

