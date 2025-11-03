"""LangGraph agent integration with production features."""

from typing import Dict, Any, List, Optional
import os

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools.arxiv.tool import ArxivQueryRun
from langchain_core.tools import tool
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages

from .models import get_openai_model
from .rag import ProductionRAGChain


class AgentState(TypedDict):
    """State schema for agent graphs."""
    messages: Annotated[List[BaseMessage], add_messages]


def create_rag_tool(rag_chain: ProductionRAGChain):
    """Create a RAG tool from a ProductionRAGChain."""
    
    @tool
    def retrieve_information(query: str) -> str:
        """Use Retrieval Augmented Generation to retrieve information from the student loan documents."""
        try:
            result = rag_chain.invoke(query)
            return result.content if hasattr(result, 'content') else str(result)
        except Exception as e:
            return f"Error retrieving information: {str(e)}"
    
    return retrieve_information


def get_default_tools(rag_chain: Optional[ProductionRAGChain] = None) -> List:
    """Get default tools for the agent.
    
    Args:
        rag_chain: Optional RAG chain to include as a tool
        
    Returns:
        List of tools
    """
    tools = []
    
    # Add Tavily search if API key is available
    if os.getenv("TAVILY_API_KEY"):
        tools.append(TavilySearchResults(max_results=5))
    
    # Add Arxiv tool
    tools.append(ArxivQueryRun())
    
    # Add RAG tool if provided
    if rag_chain:
        tools.append(create_rag_tool(rag_chain))
    
    return tools


def create_langgraph_agent(
    model_name: str = "gpt-4",
    temperature: float = 0.1,
    tools: Optional[List] = None,
    rag_chain: Optional[ProductionRAGChain] = None
):
    """Create a simple LangGraph agent.
    
    Args:
        model_name: OpenAI model name
        temperature: Model temperature
        tools: List of tools to bind to the model
        rag_chain: Optional RAG chain to include as a tool
        
    Returns:
        Compiled LangGraph agent
    """
    if tools is None:
        tools = get_default_tools(rag_chain)
    
    # Get model and bind tools
    model = get_openai_model(model_name=model_name, temperature=temperature)
    model_with_tools = model.bind_tools(tools)
    
    def call_model(state: AgentState) -> Dict[str, Any]:
        """Invoke the model with messages."""
        messages = state["messages"]
        response = model_with_tools.invoke(messages)
        return {"messages": [response]}
    
    def should_continue(state: AgentState):
        """Route to tools if the last message has tool calls."""
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "action"
        return END
    
    # Build graph
    graph = StateGraph(AgentState)
    tool_node = ToolNode(tools)
    
    graph.add_node("agent", call_model)
    graph.add_node("action", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"action": "action", END: END})
    graph.add_edge("action", "agent")
    
    return graph.compile()

##### Helpfulness Agent #####

class HelpfulnessState(TypedDict):
    """State schema for helpfulness-checking agent."""
    messages: Annotated[List[BaseMessage], add_messages]
    helpfulness_score: Optional[float]
    needs_refinement: bool


def create_helpfulness_agent(
    model_name: str = "gpt-4",
    temperature: float = 0.1,
    tools: Optional[List] = None,
    rag_chain: Optional[ProductionRAGChain] = None,
    helpfulness_threshold: float = 0.7
):
    """Create a helpfulness-checking LangGraph agent.
    
    This agent evaluates response quality and refines if needed.
    
    Args:
        model_name: OpenAI model name
        temperature: Model temperature
        tools: List of tools to bind to the model
        rag_chain: Optional RAG chain to include as a tool
        helpfulness_threshold: Minimum score to consider response helpful (0-1)
        
    Returns:
        Compiled LangGraph agent with helpfulness evaluation
    """
    if tools is None:
        tools = get_default_tools(rag_chain)
    
    # Get model and bind tools
    model = get_openai_model(model_name=model_name, temperature=temperature)
    model_with_tools = model.bind_tools(tools)
    
    # Helpfulness evaluation prompt
    helpfulness_prompt = PromptTemplate.from_template(
        """Evaluate if the following response is helpful and relevant to the user's question.
        
Question: {question}
Response: {response}

Rate the helpfulness on a scale of 0.0 to 1.0, where:
- 1.0 = Perfectly helpful, directly answers the question
- 0.7 = Adequately helpful, provides relevant information
- 0.5 = Somewhat helpful, but missing key details
- 0.3 = Minimally helpful, tangentially related
- 0.0 = Not helpful, off-topic or incorrect

Respond ONLY with a number between 0.0 and 1.0."""
    )
    
    eval_model = get_openai_model(model_name=model_name, temperature=0.0)
    helpfulness_chain = helpfulness_prompt | eval_model | StrOutputParser()
    
    def call_model(state: HelpfulnessState) -> Dict[str, Any]:
        """Invoke the model with messages."""
        messages = state["messages"]
        response = model_with_tools.invoke(messages)
        return {"messages": [response]}
    
    def should_continue(state: HelpfulnessState):
        """Route to tools if the last message has tool calls."""
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
            return "action"
        return "evaluate"
    
    def evaluate_helpfulness(state: HelpfulnessState) -> Dict[str, Any]:
        """Evaluate the helpfulness of the agent's response."""
        messages = state["messages"]
        
        # Get the user's question (first human message)
        question = next((m.content for m in messages if hasattr(m, 'content') and m.type == 'human'), "")
        
        # Get the agent's response (last AI message)
        response = messages[-1].content if messages and hasattr(messages[-1], 'content') else ""
        
        try:
            # Evaluate helpfulness
            score_str = helpfulness_chain.invoke({
                "question": question,
                "response": response
            })
            
            # Parse score
            score = float(score_str.strip())
            needs_refinement = score < helpfulness_threshold
            
            return {
                "helpfulness_score": score,
                "needs_refinement": needs_refinement
            }
        except Exception as e:
            # If evaluation fails, assume response is acceptable
            return {
                "helpfulness_score": helpfulness_threshold,
                "needs_refinement": False
            }
    
    def route_after_evaluation(state: HelpfulnessState):
        """Route based on helpfulness evaluation."""
        if state.get("needs_refinement", False):
            # Add a refinement request
            return "refine"
        return END
    
    def refine_response(state: HelpfulnessState) -> Dict[str, Any]:
        """Request the agent to refine its response."""
        refinement_msg = AIMessage(
            content="The previous response may not be fully helpful. Let me provide a more complete answer using additional tools if needed."
        )
        return {"messages": [refinement_msg], "needs_refinement": False}
    
    # Build graph
    graph = StateGraph(HelpfulnessState)
    tool_node = ToolNode(tools)
    
    graph.add_node("agent", call_model)
    graph.add_node("action", tool_node)
    graph.add_node("evaluate", evaluate_helpfulness)
    graph.add_node("refine", refine_response)
    
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"action": "action", "evaluate": "evaluate"})
    graph.add_edge("action", "agent")
    graph.add_conditional_edges("evaluate", route_after_evaluation, {"refine": "refine", END: END})
    graph.add_edge("refine", "agent")
    
    return graph.compile()
