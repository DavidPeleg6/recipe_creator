"""Execute SQL tool with guardrails for recipe database queries."""

from langchain_core.tools import tool
from langsmith import traceable
from loguru import logger

from storage.database import get_session, init_database
from storage.sql_guardrails import validate_sql, inject_soft_delete_filter, is_read_only
from sqlalchemy import text


@tool
@traceable(name="execute_recipe_sql")
def execute_recipe_sql(query: str) -> dict:
    """
    Execute SQL queries against the saved_recipes database with guardrails.
    
    USE THIS TOOL TO:
    - Search saved recipes: SELECT * FROM saved_recipes WHERE name LIKE '%pasta%'
    - Get recipe details: SELECT * FROM saved_recipes WHERE id = 'uuid-here'
    - List all recipes: SELECT name, recipe_type, created_at FROM saved_recipes ORDER BY created_at DESC
    - Update recipes: UPDATE saved_recipes SET notes = 'new notes' WHERE id = 'uuid-here'
    - Soft delete: UPDATE saved_recipes SET is_deleted = true WHERE id = 'uuid-here'
    - Restore deleted: UPDATE saved_recipes SET is_deleted = false WHERE id = 'uuid-here'
    - Search by tags: SELECT * FROM saved_recipes WHERE tags LIKE '%vegetarian%'
    
    TABLE SCHEMA - saved_recipes:
        id (TEXT PRIMARY KEY) - UUID
        name (TEXT) - Recipe name
        recipe_type (TEXT) - 'cocktail', 'food', or 'dessert'
        ingredients (TEXT) - JSON array of {name, quantity, unit, notes}
        instructions (TEXT) - JSON array of steps
        prep_time (INTEGER) - Minutes, nullable
        cook_time (INTEGER) - Minutes, nullable
        servings (INTEGER) - Number of servings, nullable
        source_references (TEXT) - JSON array of URLs
        notes (TEXT) - Tips and variations, nullable
        image_url (TEXT) - Image URL or file path, nullable
        tags (TEXT) - JSON array of tags
        is_deleted (BOOLEAN) - Soft delete flag (auto-filtered on SELECT)
        created_at (TIMESTAMP) - When saved
        last_accessed_at (TIMESTAMP) - Last accessed
    
    GUARDRAILS:
    - DROP, TRUNCATE, ALTER, CREATE, GRANT, REVOKE: BLOCKED
    - DELETE: BLOCKED (use UPDATE SET is_deleted = true instead)
    - UPDATE: Must include WHERE clause
    - SELECT: Auto-filters is_deleted = false unless explicitly querying deleted
    
    Args:
        query: SQL query to execute (SELECT or UPDATE only)
        
    Returns:
        dict with:
        - success: bool
        - data: list of rows (for SELECT) or affected_rows count (for UPDATE)
        - message: human-readable result
        - error: error message if failed
    """
    # Initialize database if needed
    init_database()
    
    # Validate query against guardrails
    is_valid, error_msg = validate_sql(query)
    if not is_valid:
        logger.warning(f"SQL blocked by guardrails: {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "message": f"Query blocked: {error_msg}",
        }
    
    # For SELECT queries, inject soft delete filter
    if is_read_only(query):
        query = inject_soft_delete_filter(query)
    
    session = get_session()
    try:
        result = session.execute(text(query))
        
        if is_read_only(query):
            # SELECT query - return rows
            rows = result.fetchall()
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in rows]
            
            logger.info(f"SQL SELECT returned {len(data)} rows")
            return {
                "success": True,
                "data": data,
                "row_count": len(data),
                "message": f"Found {len(data)} recipe(s)",
            }
        else:
            # UPDATE query - commit and return affected rows
            session.commit()
            affected = result.rowcount
            
            logger.info(f"SQL UPDATE affected {affected} rows")
            return {
                "success": True,
                "affected_rows": affected,
                "message": f"Updated {affected} row(s)",
            }
            
    except Exception as e:
        session.rollback()
        logger.error(f"SQL execution failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Query failed: {str(e)}",
        }
    finally:
        session.close()

