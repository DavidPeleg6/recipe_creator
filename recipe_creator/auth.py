import os
from fastapi import Request, HTTPException, status
from langgraph_sdk import Auth

auth = Auth()

@auth.authenticate
async def authenticate(request: Request):
    """
    Authentication handler for LangGraph server.
    Validates that the request contains the correct X-Api-Key header.
    """
    expected_key = os.getenv("LANGGRAPH_API_KEY")
    
    # If no key is configured, allow access (dev mode)
    # In production, ensure LANGGRAPH_API_KEY is set.
    if not expected_key:
        return "anonymous-dev-user"
        
    request_key = request.headers.get("X-Api-Key")
    
    if not request_key or request_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )
        
    # Return a user identity on success
    return "api-user"
