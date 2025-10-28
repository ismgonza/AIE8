"""Simple MCP server using FastMCP with webzio news search."""
from fastmcp import FastMCP
from webzio import Webzio

# Create MCP server
mcp = FastMCP("webzio-news-server")


@mcp.tool()
def get_news(query: str, sentiment: str = "neutral", language: str = "english") -> str:
    """Get news articles for a given query with optional sentiment and language filters.
    
    Args:
        query: The search query for news articles (e.g., "climate change", "AI technology")
        sentiment: The sentiment filter - must be one of: positive, negative, or neutral
        language: The language of news articles (default: english)
    
    Returns:
        A formatted string containing news articles matching the search criteria
    """
    try:
        webzio_client = Webzio(query=query, sentiment=sentiment, language=language)
        return str(webzio_client)
    except Exception as e:
        return f"Error fetching news: {str(e)}"


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()

