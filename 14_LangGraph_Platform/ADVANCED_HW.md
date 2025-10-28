# Advanced Build Assignment - MCP Integration

## 🎯 Objective

Create and deploy a locally hosted MCP server with FastMCP and extend the LangGraph tools to consume news search capabilities.

## 📦 What Was Implemented

### Files Created

1. **`webzio.py`** - Webzio news API client
   - Handles API communication with webz.io News API
   - Supports filtering by sentiment (positive/negative/neutral) and language
   - Returns formatted news results with titles and URLs

2. **`mcp_server.py`** - FastMCP server (optional standalone use)
   - Exposes `get_news` tool via MCP protocol
   - Can be used with MCP clients like Claude Desktop
   - Runs as standalone server when needed

3. **`test_mcp.py`** - Test script to verify integration
   - Tests Webzio client directly
   - Tests the `get_news` tool wrapper
   - Validates full toolbelt integration

### Files Modified

1. **`app/tools.py`** - Extended with news search capability
   - Added `get_news` tool using `@tool` decorator
   - Integrated Webzio functionality as a LangChain tool
   - Added tool to the agent's toolbelt

2. **`pyproject.toml`** - Added dependencies
   - `fastmcp>=0.2.4` - For MCP server functionality
   - `requests>=2.32.0` - For HTTP API calls

3. **`README.md`** - Marked advanced build as complete

## 🏗️ Implementation Approach

### Simple Tool Wrapper (Chosen Approach)

We implemented a **direct tool wrapper** approach rather than a complex MCP client-server architecture:

```python
@tool
def get_news(query: str, sentiment: str = "neutral", language: str = "english") -> str:
    """Get news articles with sentiment and language filters."""
    from webzio import Webzio
    webzio_client = Webzio(query=query, sentiment=sentiment, language=language)
    return str(webzio_client)
```

**Why this approach?**
- ✅ Simple and maintainable
- ✅ Direct integration with LangChain tools
- ✅ No complex subprocess management
- ✅ Works immediately without additional server setup
- ✅ Still provides `mcp_server.py` for standalone MCP protocol use

### Alternative: Full MCP Protocol (Available)

The `mcp_server.py` file implements a full MCP server using FastMCP that can be used standalone:

```bash
uv run mcp_server.py
```

This allows the tool to be consumed by other MCP clients (like Claude Desktop) if needed.

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
uv sync
```

This installs:
- `fastmcp` - For MCP server capabilities
- `requests` - For Webzio API calls
- All existing LangGraph dependencies

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Webzio API Token (get from https://webz.io/)
WEBZIO_API_TOKEN=your_webzio_api_token_here
```

Keep your existing environment variables:
```bash
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
LANGSMITH_API_KEY=your_langsmith_api_key_here  # optional
```

### 3. Test the Integration

Run the test script:

```bash
uv run test_mcp.py
```

Expected output:
```
Testing Webzio News Tool Integration
==================================================

1. Testing Webzio client directly...
✅ Webzio client works!

2. Testing get_news tool...
✅ get_news tool works!

3. Testing full toolbelt...
✅ Total tools available: 4
   - tavily_search_results_json
   - arxiv
   - retrieve_information
   - get_news
```

### 4. Run Your LangGraph with News Tool

Start the LangGraph server:

```bash
uv run langgraph dev
```

The `get_news` tool is now automatically available to your agents!

## 🎮 Using the get_news Tool

### Tool Parameters

- **query** (required): Search query for news articles
  - Example: `"artificial intelligence"`, `"climate change"`, `"cryptocurrency"`

- **sentiment** (optional, default: "neutral"): Sentiment filter
  - Options: `"positive"`, `"negative"`, `"neutral"`

- **language** (optional, default: "english"): Language of articles
  - Example: `"english"`, `"spanish"`, `"french"`

### Example Queries

Your agent can now handle queries like:

1. **"Find positive news about artificial intelligence"**
   - Uses: `get_news(query="artificial intelligence", sentiment="positive")`

2. **"Get neutral news about climate change"**
   - Uses: `get_news(query="climate change", sentiment="neutral")`

3. **"Search for negative sentiment news about cryptocurrency"**
   - Uses: `get_news(query="cryptocurrency", sentiment="negative")`

4. **"What's the latest news on space exploration?"**
   - Uses: `get_news(query="space exploration", sentiment="neutral")`

## 🔍 How It Works

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    LangGraph Agent                      │
│  (simple_agent.py / agent_with_helpfulness.py)          │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ get_tool_belt()
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   app/tools.py                          │
│  ┌────────────┬──────────┬──────────────┬────────────┐ │
│  │  Tavily    │  Arxiv   │  RAG         │  get_news  │ │
│  │  Search    │  Search  │  (Local)     │  (NEW)     │ │
│  └────────────┴──────────┴──────────────┴──────┬─────┘ │
└──────────────────────────────────────────────────┼───────┘
                                                   │
                                                   │ @tool wrapper
                                                   ▼
┌─────────────────────────────────────────────────────────┐
│                    webzio.py                            │
│              Webzio News API Client                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ HTTPS API Call
                     ▼
┌─────────────────────────────────────────────────────────┐
│              webz.io News API                           │
│          (External News Aggregator)                     │
└─────────────────────────────────────────────────────────┘
```

### Flow

1. **Agent** needs to search for news
2. **Tools** provides `get_news` tool to the agent
3. **get_news** wrapper instantiates Webzio client
4. **Webzio client** makes API call to webz.io
5. **Results** are formatted and returned to agent
6. **Agent** uses news information to respond to user

## 📝 Code Implementation Details

### 1. Webzio Client (`webzio.py`)

```python
class Webzio:
    def __init__(self, query: str, sentiment: str = "neutral", language: str = "english"):
        self.query = query
        self.sentiment = sentiment
        self.language = language
        self.token = os.getenv("WEBZIO_API_TOKEN")
    
    def get_news(self):
        """Fetch news from webz.io API"""
        url = "https://api.webz.io/newsApiLite"
        params = {
            "token": self.token,
            "q": f"{self.query} language:{self.language} sentiment:{self.sentiment}",
            "size": 5
        }
        response = requests.get(url, params=params)
        return response.json()
```

### 2. Tool Wrapper (`app/tools.py`)

```python
@tool
def get_news(query: str, sentiment: str = "neutral", language: str = "english") -> str:
    """Get news articles for a given query with optional sentiment and language filters."""
    try:
        from webzio import Webzio
        webzio_client = Webzio(query=query, sentiment=sentiment, language=language)
        return str(webzio_client)
    except Exception as e:
        return f"Error fetching news: {str(e)}"
```

### 3. Integration (`app/tools.py`)

```python
def get_tool_belt() -> List:
    """Return all tools available to agents"""
    tavily_tool = TavilySearchResults(max_results=5)
    return [tavily_tool, ArxivQueryRun(), retrieve_information, get_news]
```

## 🧪 Testing

### Manual Test

```bash
# Test Webzio client directly
uv run python -c "from webzio import Webzio; print(Webzio('AI', 'positive').get_news())"

# Test the tool wrapper
uv run python -c "from app.tools import get_news; print(get_news.invoke({'query': 'AI'}))"

# Test full toolbelt
uv run test_mcp.py
```

### Integration Test

1. Start LangGraph server: `uv run langgraph dev`
2. Open LangGraph Studio: http://localhost:2024
3. Send query: "Find positive news about AI technology"
4. Observe agent using `get_news` tool
5. Verify results contain news articles with sentiment filter

## 🎓 Key Learnings

1. **MCP Protocol vs Direct Integration**
   - MCP is powerful for multi-client scenarios
   - Direct tool wrappers are simpler for single-app use cases
   - FastMCP makes creating MCP servers easy

2. **LangChain Tool Integration**
   - `@tool` decorator creates tools from functions
   - Tools need clear docstrings for agent understanding
   - Tools can be easily added to existing toolbelts

3. **API Integration Best Practices**
   - Use environment variables for API keys
   - Implement error handling in tool wrappers
   - Format API responses for LLM consumption

4. **LangGraph Extensibility**
   - Adding tools doesn't require graph modifications
   - Tools are bound at model creation time
   - Multiple tools can work together seamlessly

## 🐛 Troubleshooting

### Issue: "WEBZIO_API_TOKEN environment variable not set"
**Solution:** Add `WEBZIO_API_TOKEN=your_token_here` to `.env` file

### Issue: Tool not appearing in agent
**Solution:** Restart LangGraph server (`uv run langgraph dev`)

### Issue: "Error fetching news"
**Solution:** 
- Check API token is valid
- Verify internet connectivity
- Check Webzio API quota/limits

### Issue: Import errors
**Solution:** Run `uv sync` to install all dependencies

## 📊 Verification Checklist

- [x] Created `webzio.py` with news API client
- [x] Created `mcp_server.py` with FastMCP server
- [x] Extended `app/tools.py` with `get_news` tool
- [x] Updated `pyproject.toml` with dependencies
- [x] Created test script (`test_mcp.py`)
- [x] Tested integration with LangGraph
- [x] Verified agent can use news search tool
- [x] Documented setup and usage

## 🚀 Optional: Standalone MCP Server

To use the MCP server with other MCP clients (like Claude Desktop):

1. Add to Cursor MCP config (`~/.cursor/mcp.json` or similar):
```json
{
  "mcpServers": {
    "webzio-news": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/14_LangGraph_Platform",
        "run",
        "mcp_server.py"
      ]
    }
  }
}
```

2. Restart Cursor/Claude Desktop

3. The `get_news` tool will be available in the MCP tools list

## 📚 References

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [LangChain Tools](https://python.langchain.com/docs/how_to/custom_tools/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Webz.io API](https://webz.io/documentation/)
- [MCP Protocol](https://modelcontextprotocol.io/)

---

**Assignment completed successfully!** ✅

The MCP integration demonstrates both direct tool integration (used in LangGraph) and standalone MCP server capabilities (available for other clients).

