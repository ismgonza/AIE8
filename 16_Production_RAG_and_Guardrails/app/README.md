# Production Semantic RAG with Intelligent Caching

## What It Does

**Production-ready RAG system** with semantic caching, LangGraph agents, and always-on guardrails.

**Core Features (Always Active):**
- ✨ **Semantic LLM caching** (0.85 similarity threshold) - 5-20x faster
- 🛡️ **Guardrails AI** (always on) - blocks off-topic, PII, jailbreaks
- 💾 **Persistent Qdrant storage** - survives restarts
- ⚡ **3 Processing modes** - choose speed vs intelligence

**Three Processing Modes:**
1. 🚀 **Direct Mode** (~1-2s) - Fast RAG with semantic caching
2. 🤖 **Simple Agent** (~6-8s) - Smart tool usage (RAG, Tavily, Arxiv)
3. 🧠 **Helpfulness Agent** (~10s) - Evaluates quality, refines if needed

## How to Run

### Quick Start (Recommended)

**1. Start Qdrant (vector database in Docker)**
```bash
cd app
./start_qdrant.sh
```

**2. Run the app locally (in another terminal)**
```bash
cd app
./run_app.sh
```

Wait ~10 seconds for startup.

**3. Test the full system**
```bash
./test_system.sh
```

Or open http://localhost:8000/docs in your browser.

**Why this setup?**
- Qdrant in Docker: Persistent storage survives restarts
- App locally: Fast development, instant reload, all dependencies available
- Best of both worlds!

## API Endpoints

### Query with Mode Selection
```bash
# Direct mode (fastest, cached)
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is a Pell Grant?",
    "mode": "direct"
  }'

# Simple agent (smart, uses tools)
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the latest student loan forgiveness developments?",
    "mode": "simple_agent"
  }'

# Helpfulness agent (evaluates quality)
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the Direct Loan Program?",
    "mode": "helpfulness_agent"
  }'
```

**Parameters:**
- `question`: Your query (string, required)
- `mode`: Processing mode (default: "direct")
  - `"direct"` - Fast RAG with caching (~1-2s)
  - `"simple_agent"` - Smart tool selection (~6-8s)
  - `"helpfulness_agent"` - Quality evaluation (~10s)
- `use_cache`: Enable semantic caching (default: true)
- `disable_guardrails`: Disable guardrails for testing (default: false)

**Note:** Guardrails are **always active by default** (production-safe). The `disable_guardrails` flag is **only for testing** edge cases and helpfulness evaluation with extremely vague queries.

### Load Documents
```bash
curl -X POST "http://localhost:8000/load" \
  -H "Content-Type: application/json" \
  -d '{"pdf_path": "../data/The_Federal_Pell_Grant_Program.pdf"}'
```

### Other Endpoints
- `GET /` - System info and available modes
- `GET /health` - Health check with system status
- `GET /cache/stats` - View cache statistics
- `POST /cache/clear` - Clear semantic cache

## How It Works

### Architecture

```
User Query
    ↓
🛡️ Guardrails (ALWAYS ON)
    ├─ Topic validation
    ├─ Jailbreak detection
    └─ PII protection
    ↓
🔍 Semantic Cache Check (0.85 threshold)
    ├─ Cache Hit → Return cached (0.3-2s) ⚡
    └─ Cache Miss ↓
        ├─ Direct Mode: RAG (~2-4s)
        ├─ Simple Agent: Use tools (~6-8s)
        └─ Helpfulness Agent: Evaluate + refine (~10s)
```

### 1. Semantic Caching (Always Active ✓)
- Converts queries to embeddings
- Finds similar cached queries (similarity > 0.85)
- Returns cached response if match found
- **5-20x faster, 70-99% cost savings on cache hits**

### 2. Guardrails (Always Active ✓)
**Production-safe by default!**
- ✅ Topic restriction (student loans, financial aid only)
- ✅ Jailbreak detection (blocks adversarial prompts)
- ✅ PII protection (detects SSN, credit cards, etc.)
- ✅ Input validation (before processing)
- ⚠️ Can be disabled with `disable_guardrails: true` (testing only!)

### 3. Direct Mode (Default)
- Fast RAG with semantic caching
- Best for: Simple factual questions
- Speed: ~1-2s cached, ~2-4s uncached

### 4. Simple Agent Mode
- Uses tools intelligently:
  - **RAG tool** - Searches loaded documents
  - **Tavily search** - Web search for current info
  - **Arxiv** - Academic research papers
- Best for: Questions requiring multiple sources
- Speed: ~6-8s

### 5. Helpfulness Agent Mode
- Evaluates response quality (0.0-1.0 score)
- Auto-refines if helpfulness < 0.7
- Uses all tools + quality assessment
- Best for: Critical queries requiring high-quality answers
- Speed: ~10s

## Examples

### Example 1: Fast Factual Query (Direct Mode)
```bash
curl -X POST "http://localhost:8000/query" \
  -d '{"question": "What is a Pell Grant?", "mode": "direct"}'
```
**Response:** ~1s (cached) or ~3s (not cached)

### Example 2: Current Events (Simple Agent)
```bash
curl -X POST "http://localhost:8000/query" \
  -d '{"question": "What are the latest student loan forgiveness programs?", "mode": "simple_agent"}'
```
**Response:** ~7s (uses Tavily web search)

### Example 3: Academic Research (Simple Agent)
```bash
curl -X POST "http://localhost:8000/query" \
  -d '{"question": "Find recent papers about student loan debt", "mode": "simple_agent"}'
```
**Response:** ~10s (uses Arxiv)

### Example 4: High-Quality Answer (Helpfulness Agent)
```bash
curl -X POST "http://localhost:8000/query" \
  -d '{"question": "Explain the Direct Loan Program comprehensively", "mode": "helpfulness_agent"}'
```
**Response:** ~10s (evaluates quality, may refine)

### Example 5: Testing with Guardrails Disabled (Testing Only)
```bash
# For testing helpfulness with extremely vague queries
curl -X POST "http://localhost:8000/query" \
  -d '{"question": "Tell me something", "mode": "helpfulness_agent", "disable_guardrails": true}'
```
**Note:** Only use `disable_guardrails` for testing. Production systems should always keep guardrails active.

## Configuration

### Semantic Cache Threshold
Edit `semantic_cache.py` line 22:
```python
similarity_threshold: float = 0.85  # Default (balanced)
# Lower (0.80) = more cache hits, less precision
# Higher (0.90) = fewer cache hits, more precision
```

### Guardrails Topics
Edit `main.py` line 66:
```python
valid_topics=["student loans", "financial aid", "education financing", "loan repayment"]
```

### Helpfulness Threshold
Edit `langgraph_agent_lib/agents.py` line 128:
```python
helpfulness_threshold: float = 0.7  # Minimum score for acceptable response
```

## Files

**Core Application (~600 lines total):**
- `main.py` - FastAPI API with 3 modes + guardrails (~321 lines)
- `rag_service.py` - RAG with semantic caching + auto-reconnect (~218 lines)
- `semantic_cache.py` - Vector similarity caching (~157 lines)

**Scripts:**
- `run_app.sh` - Starts FastAPI app locally with .env loading
- `start_qdrant.sh` - Starts Qdrant database in Docker
- `test_system.sh` - Comprehensive test suite
- `docker-compose.yml` - Qdrant configuration

**Library:**
- `../langgraph_agent_lib/` - Agents (simple + helpfulness) and guardrails

## Stop

**Stop the app:** `Ctrl+C` in the terminal running the app

**Stop Qdrant:**
```bash
docker-compose down
```

## Troubleshooting

**"Cannot connect to Docker daemon"**
→ Start Docker Desktop first

**"Port 8000 already in use"**
→ `lsof -ti:8000 | xargs kill -9`

**"Low cache hit rate"**
→ Lower threshold in `semantic_cache.py` to 0.80

**"Agents not initialized"**
→ Load documents first with `/load` endpoint

**"Guardrails blocking valid queries"**
→ Adjust `valid_topics` in `main.py`

## Performance Comparison

| Mode | Speed | Cost | Intelligence | Use Case |
|------|-------|------|--------------|----------|
| **Direct (cached)** | 0.3-2s | $0 | Good | Repeated questions |
| **Direct (uncached)** | 2-4s | $0.002 | Good | Simple factual queries |
| **Simple Agent** | 6-8s | $0.01 | Better | Multi-source questions |
| **Helpfulness Agent** | 10s | $0.015 | Best | Critical high-quality needs |

**Recommendation:** 
- Use **direct mode** by default (fast, cached)
- Use **simple agent** for complex multi-source queries
- Use **helpfulness agent** for mission-critical responses

## Enable Optional Features (Agents & Guardrails)

The app works in basic mode immediately! To enable agents and guardrails:

```bash
# 1. Get API keys
# - Guardrails: https://hub.guardrailsai.com/keys
# - Tavily: https://tavily.com/

# 2. Add to root .env file
echo "TAVILY_API_KEY=your_key_here" >> ../.env
echo "GUARDRAILS_API_KEY=your_key_here" >> ../.env

# 3. Install guardrails hub components
cd ..
uv run guardrails hub install hub://tryolabs/restricttotopic
uv run guardrails hub install hub://guardrails/detect_jailbreak
uv run guardrails hub install hub://guardrails/profanity_free
uv run guardrails hub install hub://guardrails/guardrails_pii

# 4. Restart the app
cd app
# Stop app (Ctrl+C), then ./run_app.sh again
```

## What's New in v2.0

✅ **Guardrails always active** - Production-safe by default  
✅ **3 processing modes** - Choose speed vs intelligence  
✅ **Helpfulness agent** - Evaluates and refines responses  
✅ **Simplified API** - One `mode` parameter instead of multiple flags  
✅ **Comprehensive tests** - Tests all modes, tools, and guardrails  

**Core improvement:** Production-safe architecture with guardrails always active, semantic caching on all modes, and intelligent agent selection.

## Test Results

From `./test_system.sh`:

✅ **Semantic Caching:**
- Cache miss: 11s (first query)
- Cache hit: 1.7s (exact match) - **6x faster**
- Semantic hit: 2.2s (similar query) - **5x faster**

✅ **Guardrails (Always Active):**
- ✓ Valid queries pass
- ✓ Off-topic blocked ("weather" rejected)
- ✓ PII detected (SSN, credit cards)

✅ **Agent Modes:**
- Direct: 4.5s
- Simple Agent: 7.6s, comprehensive answer
- Helpfulness Agent: 6.4s, score: 1.0 (perfect!)

✅ **Tool Selection:**
- RAG queries: 3.4s
- Web search (Tavily): 8.3s
- Academic (Arxiv): 12.3s
- Multi-tool: 9.4s
