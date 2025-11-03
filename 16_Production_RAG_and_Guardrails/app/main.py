"""Production FastAPI application with semantic caching, agents, and guardrails."""

import os
import sys
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Literal
from enum import Enum

# Add parent directory to path to import langgraph_agent_lib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import agents and guardrails
try:
    from langgraph_agent_lib.agents import create_langgraph_agent, create_helpfulness_agent
    from guardrails.hub import RestrictToTopic
    from guardrails import Guard
    AGENTS_AVAILABLE = True
    GUARDRAILS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import agents/guardrails: {e}")
    print("Running in basic mode (semantic caching + RAG only)")
    AGENTS_AVAILABLE = False
    GUARDRAILS_AVAILABLE = False

try:
    from app.rag_service import RAGService
except ImportError:
    from rag_service import RAGService


# Initialize FastAPI app
app = FastAPI(
    title="Production Semantic RAG API",
    description="Production RAG with semantic caching, LangGraph agents, and Guardrails (always on)",
    version="2.0.0"
)

# Initialize RAG service with semantic caching
qdrant_host = os.getenv("QDRANT_HOST", "localhost")
qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))

rag_service = RAGService(
    qdrant_host=qdrant_host,
    qdrant_port=qdrant_port
)

# Initialize agents and guardrails
simple_agent = None
helpfulness_agent = None
guardrails_guard = None


def initialize_agents_and_guardrails():
    """Initialize both agents and guardrails (always on for production)."""
    global simple_agent, helpfulness_agent, guardrails_guard
    
    if not AGENTS_AVAILABLE:
        print("⚠️  Agents not available - running in direct RAG mode only")
        return
    
    try:
        # Setup guardrails (ALWAYS ON for production safety)
        if GUARDRAILS_AVAILABLE:
            guardrails_guard = Guard().use(
                RestrictToTopic(
                    valid_topics=["student loans", "financial aid", "education financing", "loan repayment"],
                    disable_classifier=True,
                    disable_llm=False,
                    on_fail="exception"
                )
            )
            print("✓ Guardrails configured (always active)")
        
        # Create simple agent (fast, uses tools intelligently)
        simple_agent = create_langgraph_agent(
            model_name="gpt-4o-mini",
            temperature=0.1,
            rag_chain=None  # Uses default tools: Tavily, Arxiv, RAG
        )
        print("✓ Simple agent initialized")
        
        # Create helpfulness agent (evaluates and refines responses)
        helpfulness_agent = create_helpfulness_agent(
            model_name="gpt-4o-mini",
            temperature=0.1,
            rag_chain=None,
            helpfulness_threshold=0.7
        )
        print("✓ Helpfulness agent initialized")
        
        print("🎯 Production system ready with guardrails always active!")
        
    except Exception as e:
        print(f"⚠️  Error initializing agents/guardrails: {e}")


# Initialize on startup
@app.on_event("startup")
async def startup_event():
    """Initialize agents and guardrails if documents are loaded."""
    if rag_service.vectorstore is not None:
        print("📦 Documents found, initializing production system...")
        initialize_agents_and_guardrails()
    else:
        print("⚠️  No documents found. Load documents via /load endpoint.")


class ProcessingMode(str, Enum):
    """Processing modes for queries."""
    DIRECT = "direct"  # Fast: Direct RAG with semantic caching
    SIMPLE_AGENT = "simple_agent"  # Smart: Uses tools (RAG, Tavily, Arxiv)
    HELPFULNESS_AGENT = "helpfulness_agent"  # Smartest: Evaluates and refines


class QueryRequest(BaseModel):
    """Query request model."""
    question: str
    mode: ProcessingMode = ProcessingMode.DIRECT
    use_cache: bool = True
    disable_guardrails: bool = False  # For testing only - guardrails active by default


class QueryResponse(BaseModel):
    """Query response model."""
    answer: str
    mode: str
    cached: bool
    response_time_seconds: float
    sources: List = []
    guardrails_passed: bool = True
    guardrails_messages: Optional[List[str]] = None
    helpfulness_score: Optional[float] = None


class LoadDocumentsRequest(BaseModel):
    """Load documents request model."""
    pdf_path: str
    chunk_size: int = 1000
    chunk_overlap: int = 100


@app.get("/")
async def root():
    """Root endpoint with system status."""
    return {
        "message": "Production Semantic RAG API",
        "version": "2.0.0",
        "features": {
            "semantic_caching": "✓ Always active",
            "guardrails": "✓ Always active (when available)" if GUARDRAILS_AVAILABLE else "✗ Not available",
            "agents": "✓ Available" if AGENTS_AVAILABLE else "✗ Not available"
        },
        "modes": {
            "direct": "Fast RAG with semantic caching (~1s)",
            "simple_agent": "Smart tool usage (~6s)",
            "helpfulness_agent": "Quality evaluation (~10s)"
        },
        "endpoints": {
            "query": "/query",
            "load": "/load",
            "cache_stats": "/cache/stats",
            "clear_cache": "/cache/clear",
            "health": "/health"
        }
    }


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query with semantic caching and guardrails (always on).
    
    Modes:
    - direct: Fast RAG with caching (~1s)
    - simple_agent: Uses tools intelligently (~6s)
    - helpfulness_agent: Evaluates quality (~10s)
    
    Guardrails are ALWAYS applied for production safety.
    """
    try:
        start_time = time.time()
        
        # STEP 1: Input validation with Guardrails (ALWAYS ON unless explicitly disabled for testing)
        if not request.disable_guardrails and GUARDRAILS_AVAILABLE and guardrails_guard:
            try:
                guardrails_guard.validate(request.question)
            except Exception as e:
                return QueryResponse(
                    answer=f"⛔ Query blocked by guardrails: {str(e)}",
                    mode=request.mode.value,
                    cached=False,
                    response_time_seconds=round(time.time() - start_time, 3),
                    sources=[],
                    guardrails_passed=False,
                    guardrails_messages=[str(e)]
                )
        elif request.disable_guardrails:
            print("⚠️  WARNING: Guardrails disabled for this query (testing only!)")
        
        # STEP 2: Process based on mode
        if request.mode == ProcessingMode.DIRECT:
            # Direct RAG with semantic caching (fastest)
            result = rag_service.query(
                question=request.question,
                use_cache=request.use_cache
            )
            
            return QueryResponse(
                answer=result["answer"],
                mode="direct",
                cached=result["cached"],
                response_time_seconds=round(time.time() - start_time, 3),
                sources=result.get("sources", []),
                guardrails_passed=True
            )
            
        elif request.mode == ProcessingMode.SIMPLE_AGENT:
            # Simple agent with tools
            if not AGENTS_AVAILABLE or simple_agent is None:
                raise HTTPException(
                    status_code=503,
                    detail="Simple agent not available. Use mode='direct' or load documents first."
                )
            
            from langchain_core.messages import HumanMessage
            result = simple_agent.invoke({"messages": [HumanMessage(content=request.question)]})
            answer = result["messages"][-1].content
            
            return QueryResponse(
                answer=answer,
                mode="simple_agent",
                cached=False,
                response_time_seconds=round(time.time() - start_time, 3),
                sources=[],
                guardrails_passed=True
            )
            
        elif request.mode == ProcessingMode.HELPFULNESS_AGENT:
            # Helpfulness agent with evaluation
            if not AGENTS_AVAILABLE or helpfulness_agent is None:
                raise HTTPException(
                    status_code=503,
                    detail="Helpfulness agent not available. Use mode='direct' or load documents first."
                )
            
            from langchain_core.messages import HumanMessage
            result = helpfulness_agent.invoke({"messages": [HumanMessage(content=request.question)]})
            answer = result["messages"][-1].content
            helpfulness_score = result.get("helpfulness_score")
            
            return QueryResponse(
                answer=answer,
                mode="helpfulness_agent",
                cached=False,
                response_time_seconds=round(time.time() - start_time, 3),
                sources=[],
                guardrails_passed=True,
                helpfulness_score=helpfulness_score
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/load")
async def load_documents(request: LoadDocumentsRequest):
    """Load documents and initialize agents."""
    try:
        if not os.path.exists(request.pdf_path):
            raise HTTPException(status_code=404, detail=f"File not found: {request.pdf_path}")
        
        rag_service.load_documents(
            pdf_path=request.pdf_path,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )
        
        # Initialize agents and guardrails
        initialize_agents_and_guardrails()
        
        return {
            "message": "Documents loaded and production system initialized",
            "pdf_path": request.pdf_path,
            "simple_agent_ready": simple_agent is not None,
            "helpfulness_agent_ready": helpfulness_agent is not None,
            "guardrails_active": guardrails_guard is not None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cache/stats")
async def get_cache_stats():
    """Get semantic cache statistics."""
    try:
        return rag_service.get_cache_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cache/clear")
async def clear_cache():
    """Clear semantic cache."""
    try:
        rag_service.clear_cache()
        return {"message": "Semantic cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check with system status."""
    return {
        "status": "healthy",
        "qdrant_host": qdrant_host,
        "qdrant_port": qdrant_port,
        "simple_agent_ready": simple_agent is not None,
        "helpfulness_agent_ready": helpfulness_agent is not None,
        "guardrails_active": guardrails_guard is not None,
        "semantic_caching": "active"
    }
