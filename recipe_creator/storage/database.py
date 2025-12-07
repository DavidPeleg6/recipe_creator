"""SQLite database setup and session management."""

import os
from pathlib import Path

from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, Boolean, Index, JSON
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
    ingredients = Column(JSON, nullable=False)  # Array of {name, quantity, unit, notes}
    instructions = Column(JSON, nullable=False)  # Array of step strings
    prep_time = Column(Integer)  # Minutes
    cook_time = Column(Integer)  # Minutes
    servings = Column(Integer)
    source_references = Column(JSON)  # Array of URLs
    notes = Column(Text)
    image_url = Column(String(500))
    tags = Column(JSON)  # Array of tag strings
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False)
    last_accessed_at = Column(DateTime, nullable=False)

    # Composite index for common query pattern (active recipes)
    __table_args__ = (
        Index("idx_recipe_active", "is_deleted", "name"),
    )


def get_engine(db_path: str | Path | None = None):
    """Create SQLAlchemy engine.
    
    Args:
        db_path: Path to SQLite database file. Defaults to RECIPE_DB_PATH env var
                 or recipes.db in recipe_creator directory.
                 
    Returns:
        SQLAlchemy Engine instance
    """
    path = db_path or os.getenv("RECIPE_DB_PATH", DEFAULT_DB_PATH)
    return create_engine(f"sqlite:///{path}", echo=False)


def init_database(db_path: str | Path | None = None):
    """Initialize database and create tables.
    
    Args:
        db_path: Path to SQLite database file. Defaults to RECIPE_DB_PATH env var
                 or recipes.db in recipe_creator directory.
                 
    Returns:
        SQLAlchemy Engine instance
    """
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine=None):
    """Get a new database session.
    
    Args:
        engine: SQLAlchemy Engine. If None, creates new engine with default path.
        
    Returns:
        SQLAlchemy Session instance
    """
    if engine is None:
        engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
