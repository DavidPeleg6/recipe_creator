"""Database models package."""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import models after Base definition to avoid circular imports
from models.db.saved_recipe import SavedRecipeDB  # noqa: E402,F401

__all__ = ["Base", "SavedRecipeDB"]

