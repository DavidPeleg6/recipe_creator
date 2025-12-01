"""Web search tool using Tavily API."""

from langchain.tools import tool
from tavily import TavilyClient

from config import config


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for recipe information, ingredients, cooking techniques, or cocktail recipes.

    Use this tool when you need to find recipes, look up cooking methods,
    research ingredients, or discover new recipe ideas.

    Args:
        query: Search query about recipes, cooking, or cocktails
        max_results: Maximum number of search results to return

    Returns:
        Formatted search results with titles, snippets, and source URLs
    """
    if not config.tavily_api_key:
        return "Error: TAVILY_API_KEY not configured"

    client = TavilyClient(api_key=config.tavily_api_key)
    response = client.search(query, max_results=max_results)

    results = []
    for item in response.get("results", []):
        results.append(f"**{item['title']}**\n{item['content']}\nSource: {item['url']}\n")

    return "\n---\n".join(results) if results else "No results found."

