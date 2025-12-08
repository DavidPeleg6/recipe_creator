"""Persistent saved recipe model."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SavedRecipeDB(Base):
    """SQLAlchemy model for saved recipes."""

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
    saved_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    conversation_id = Column(String(100))
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)


