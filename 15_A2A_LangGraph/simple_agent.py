#!/usr/bin/env python3
"""Simple LangGraph Agent that uses A2A protocol to interact with the Agent Node.

This is a CLI-based agent that accepts user queries and makes API calls through A2A.
"""
import asyncio
import logging
from typing import TypedDict, Annotated
from uuid import uuid4

import httpx
from langgraph.graph import StateGraph, END
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest
import warnings

# Suppress the A2AClient deprecation warning for now
warnings.filterwarnings('ignore', message='.*A2AClient is deprecated.*')

# Reduce verbosity of httpx and a2a logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger(__name__).setLevel(logging.INFO)
logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """Simple state to track the conversation."""
    query: str
    response: str
    context_id: str
    task_id: str


async def a2a_call_node(state: AgentState) -> AgentState:
    """Node that makes A2A API call to the agent server."""
    query = state.get("query", "")
    
    logger.info(f"\n🤖 Sending to A2A Agent: {query}")
    
    # Set up A2A client
    base_url = 'http://localhost:10000'
    timeout = httpx.Timeout(60.0)
    
    async with httpx.AsyncClient(timeout=timeout) as httpx_client:
        # Get agent card
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
        agent_card = await resolver.get_agent_card()
        
        # Beautified agent card display
        logger.info(f"📋 Connected to: {agent_card.name}")
        logger.info(f"   Description: {agent_card.description}")
        if agent_card.skills:
            logger.info(f"   Available skills: {', '.join([s.name for s in agent_card.skills[:3]])}")
        
        # Create A2A client
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
        
        # Build message payload (each query is independent - no multi-turn for simplicity)
        message_payload = {
            'message': {
                'role': 'user',
                'parts': [{'kind': 'text', 'text': query}],
                'message_id': uuid4().hex,
            }
        }
        
        # Send message
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(**message_payload)
        )
        
        response = await client.send_message(request)
        
        # Check if response is an error
        if hasattr(response, 'error') and response.error:
            error_msg = f"Error from agent: {response.error}"
            logger.error(f"\n❌ {error_msg}\n")
            return {
                "query": query,
                "response": error_msg,
                "context_id": "",
                "task_id": ""
            }
        
        # Handle different response types
        result = None
        if hasattr(response, 'root'):
            if hasattr(response.root, 'result'):
                result = response.root.result
            elif hasattr(response.root, 'error'):
                # JSONRPC error response
                error_msg = f"Agent error: {response.root.error}"
                logger.error(f"\n❌ {error_msg}\n")
                return {
                    "query": query,
                    "response": error_msg,
                    "context_id": "",
                    "task_id": ""
                }
        
        if not result:
            error_msg = "No result returned from agent"
            logger.error(f"\n❌ {error_msg}\n")
            return {
                "query": query,
                "response": error_msg,
                "context_id": "",
                "task_id": ""
            }
        
        # Get the artifact text if available
        response_text = ""
        if result.artifacts and len(result.artifacts) > 0:
            artifact = result.artifacts[0]
            if artifact.parts and len(artifact.parts) > 0:
                part = artifact.parts[0]
                if hasattr(part.root, 'text'):
                    response_text = part.root.text
        
        # Fallback to messages if no artifact
        if not response_text and result.messages:
            last_message = result.messages[-1]
            if last_message.parts:
                for part in last_message.parts:
                    if hasattr(part, 'text'):
                        response_text = part.text
                        break
        
        logger.info(f"\n✅ Response received\n")
        
        return {
            "query": query,
            "response": response_text,
            "context_id": result.context_id,
            "task_id": result.id
        }


def build_simple_graph():
    """Build a simple LangGraph with just one A2A call node."""
    graph = StateGraph(AgentState)
    
    # Add the A2A call node
    graph.add_node("a2a_call", a2a_call_node)
    
    # Simple flow: start -> a2a_call -> end
    graph.set_entry_point("a2a_call")
    graph.add_edge("a2a_call", END)
    
    return graph.compile()


async def run_cli():
    """Run the CLI interface for the simple agent."""
    print("\n" + "="*60)
    print("🚀 Simple A2A Agent CLI")
    print("="*60)
    print("\nThis agent uses LangGraph to call your A2A agent server.")
    print("Type your questions below. Type 'quit' or 'exit' to stop.\n")
    
    graph = build_simple_graph()
    
    while True:
        try:
            # Get user input
            user_input = input("\n💬 You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!\n")
                break
            
            # Run the graph (each query is independent)
            state = {
                "query": user_input,
                "response": "",
                "context_id": "",
                "task_id": ""
            }
            
            result = await graph.ainvoke(state)
            
            # Display response
            response = result.get("response", "No response received")
            print(f"\n🤖 Agent: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            logger.error(f"\n❌ Error: {e}")
            print(f"\n❌ An error occurred. Please try again.")


def main():
    """Main entry point."""
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!\n")


if __name__ == "__main__":
    main()

