"""Simple test script to verify webzio news tool integration."""
from dotenv import load_dotenv
load_dotenv()

print("Testing Webzio News Tool Integration\n" + "="*50)

# Test 1: Import and test webzio directly
print("\n1. Testing Webzio client directly...")
try:
    from webzio import Webzio
    client = Webzio("AI technology", sentiment="positive", language="english")
    result = str(client)
    print("✅ Webzio client works!")
    print(f"Sample output (first 200 chars): {result[:200]}...")
except Exception as e:
    print(f"❌ Webzio client failed: {e}")

# Test 2: Test the get_news tool
print("\n2. Testing get_news tool...")
try:
    from app.tools import get_news
    result = get_news.invoke({"query": "artificial intelligence", "sentiment": "positive"})
    print("✅ get_news tool works!")
    print(f"Sample output (first 200 chars): {result[:200]}...")
except Exception as e:
    print(f"❌ get_news tool failed: {e}")

# Test 3: Check full toolbelt
print("\n3. Testing full toolbelt...")
try:
    from app.tools import get_tool_belt
    tools = get_tool_belt()
    print(f"✅ Total tools available: {len(tools)}")
    for tool in tools:
        print(f"   - {tool.name}")
except Exception as e:
    print(f"❌ Toolbelt loading failed: {e}")

print("\n" + "="*50)
print("Test complete! If all tests passed, your setup is ready.")
print("Run 'uv run langgraph dev' to start your agent with the news tool.")

