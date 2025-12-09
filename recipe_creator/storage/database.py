"""Database engine and session setup.

Schema reference (saved_recipes):
- id (UUID text) PK
- name (text, indexed)
- recipe_type (text: cocktail|food|dessert, indexed)
- ingredients, instructions (JSON)
- prep_time_minutes, cook_time_minutes, servings (ints)
- source_references, notes, user_notes, tags (JSON/text)
- saved_at (datetime, indexed)
- conversation_id (text)
- is_deleted (bool/int, indexed)
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config import config
from models.db import Base

engine = create_async_engine(config.database_url, echo=False)
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db() -> None:
    """Create database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


