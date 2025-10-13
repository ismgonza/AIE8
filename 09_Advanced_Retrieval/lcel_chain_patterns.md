# 🔗 Different Chain Syntax Patterns

---

## 1️⃣ **SIMPLE CHAIN** (Just LLM)

```python
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Components
prompt = ChatPromptTemplate.from_template("Tell me a joke about {topic}")
llm = ChatOpenAI(model="gpt-4")
output_parser = StrOutputParser()

# Chain
simple_chain = prompt | llm | output_parser

# Usage
simple_chain.invoke({"topic": "programming"})
```

---

## 2️⃣ **RAG CHAIN** (LLM + Document Retrieval)

### Basic RAG
```python
from langchain_core.runnables import RunnablePassthrough

# Components
retriever = vectorstore.as_retriever()
prompt = ChatPromptTemplate.from_template(
    "Context: {context}\n\nQuestion: {question}\n\nAnswer:"
)
llm = ChatOpenAI()

# Chain
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# Usage
rag_chain.invoke("What is LCEL?")
```

### RAG with Dict Input
```python
from operator import itemgetter

rag_chain = (
    {"context": itemgetter("question") | retriever,
     "question": itemgetter("question")}
    | prompt
    | llm
    | StrOutputParser()
)

# Usage
rag_chain.invoke({"question": "What is LCEL?"})
```

### RAG Returning Sources
```python
rag_with_sources = (
    {"context": itemgetter("question") | retriever,
     "question": itemgetter("question")}
    | {
        "answer": prompt | llm | StrOutputParser(),
        "sources": itemgetter("context")
    }
)

# Returns: {"answer": "...", "sources": [doc1, doc2, ...]}
```

---

## 3️⃣ **CONVERSATIONAL CHAIN** (With Chat History)

```python
from langchain.memory import ConversationBufferMemory

conversational_chain = (
    {
        "context": itemgetter("question") | retriever,
        "question": itemgetter("question"),
        "chat_history": itemgetter("chat_history")
    }
    | ChatPromptTemplate.from_template(
        "Chat History: {chat_history}\n\n"
        "Context: {context}\n\n"
        "Question: {question}\n\nAnswer:"
    )
    | llm
    | StrOutputParser()
)

# Usage
conversational_chain.invoke({
    "question": "What was my previous question?",
    "chat_history": "User: Hello\nAI: Hi there!"
})
```

---

## 4️⃣ **SEQUENTIAL CHAIN** (Multi-Step Processing)

```python
# Step 1: Generate a story outline
outline_chain = (
    ChatPromptTemplate.from_template("Create a story outline about {topic}")
    | llm
    | StrOutputParser()
)

# Step 2: Write the full story
story_chain = (
    ChatPromptTemplate.from_template("Write a story based on: {outline}")
    | llm
    | StrOutputParser()
)

# Combined
sequential_chain = (
    {"topic": RunnablePassthrough()}
    | RunnablePassthrough.assign(outline=outline_chain)
    | {"story": story_chain, "outline": itemgetter("outline")}
)

# Usage
sequential_chain.invoke({"topic": "space exploration"})
# Returns: {"story": "...", "outline": "..."}
```

---

## 5️⃣ **PARALLEL CHAIN** (Multiple Operations at Once)

```python
parallel_chain = (
    {"input": RunnablePassthrough()}
    | {
        "summary": ChatPromptTemplate.from_template("Summarize: {input}") | llm,
        "sentiment": ChatPromptTemplate.from_template("Sentiment of: {input}") | llm,
        "keywords": ChatPromptTemplate.from_template("Keywords from: {input}") | llm
    }
)

# Usage
parallel_chain.invoke({"input": "Your text here..."})
# Returns: {"summary": "...", "sentiment": "...", "keywords": "..."}
```

---

## 6️⃣ **CONDITIONAL CHAIN** (Branching Logic)

```python
from langchain_core.runnables import RunnableBranch

conditional_chain = (
    {"question": RunnablePassthrough()}
    | RunnableBranch(
        # If question contains "code"
        (
            lambda x: "code" in x["question"].lower(),
            ChatPromptTemplate.from_template("Code help: {question}") | llm
        ),
        # If question contains "math"
        (
            lambda x: "math" in x["question"].lower(),
            ChatPromptTemplate.from_template("Math help: {question}") | llm
        ),
        # Default
        ChatPromptTemplate.from_template("General: {question}") | llm
    )
    | StrOutputParser()
)

# Usage
conditional_chain.invoke({"question": "How do I write a loop in Python?"})
```

---

## 7️⃣ **MULTI-QUERY CHAIN** (Multiple Retrieval Strategies)

```python
multi_query_chain = (
    {
        "dense_results": itemgetter("question") | dense_retriever,
        "sparse_results": itemgetter("question") | sparse_retriever,
        "question": itemgetter("question")
    }
    | RunnablePassthrough.assign(
        all_docs=lambda x: x["dense_results"] + x["sparse_results"]
    )
    | {
        "answer": ChatPromptTemplate.from_template(
            "Context: {all_docs}\n\nQuestion: {question}"
        ) | llm | StrOutputParser(),
        "sources": itemgetter("all_docs")
    }
)
```

---

## 8️⃣ **ROUTING CHAIN** (Route to Different Chains)

```python
from langchain_core.runnables import RunnableLambda

def route_question(input_data):
    question = input_data["question"].lower()
    if "technical" in question:
        return technical_chain
    elif "sales" in question:
        return sales_chain
    else:
        return general_chain

routing_chain = (
    {"question": RunnablePassthrough()}
    | RunnableLambda(route_question)
)

# Usage
routing_chain.invoke({"question": "Technical documentation help"})
```

---

## 9️⃣ **AGENT CHAIN** (With Tools)

```python
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.tools import Tool

# Define tools
tools = [
    Tool(
        name="Calculator",
        func=lambda x: eval(x),
        description="Useful for math calculations"
    ),
    Tool(
        name="Search",
        func=search_function,
        description="Search the web"
    )
]

# Create agent
agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

# Usage
agent_executor.invoke({"input": "What's 25 * 47?"})
```

---

## 🔟 **TRANSFORMATION CHAIN** (Data Processing)

```python
transformation_chain = (
    {"text": RunnablePassthrough()}
    | RunnablePassthrough.assign(
        word_count=lambda x: len(x["text"].split()),
        char_count=lambda x: len(x["text"]),
        uppercase=lambda x: x["text"].upper()
    )
    | {
        "analysis": ChatPromptTemplate.from_template(
            "Analyze this text ({word_count} words): {text}"
        ) | llm,
        "stats": lambda x: {
            "words": x["word_count"],
            "chars": x["char_count"]
        }
    }
)
```

---

## 📋 **Quick Reference Table**

| Chain Type | Has Retriever? | Has Memory? | Use Case |
|------------|----------------|-------------|----------|
| **Simple** | ❌ | ❌ | General Q&A |
| **RAG** | ✅ | ❌ | Document search |
| **Conversational** | ✅/❌ | ✅ | Chatbots |
| **Sequential** | ❌ | ❌ | Multi-step tasks |
| **Parallel** | ❌ | ❌ | Multiple analyses |
| **Conditional** | ❌ | ❌ | If/else logic |
| **Multi-Query** | ✅ | ❌ | Hybrid search |
| **Routing** | ❌ | ❌ | Dynamic chain selection |
| **Agent** | ✅/❌ | ✅/❌ | Tool usage |
| **Transformation** | ❌ | ❌ | Data processing |

---

## 🎯 **Most Common Pattern (Your Use Case)**

```python
# Simple RAG with sources - this is what you're using!
rag_chain = (
    {"context": itemgetter("question") | retriever,
     "question": itemgetter("question")}
    | {"answer": prompt | llm, "sources": itemgetter("context")}
)
```

---

## 💡 **Key Principles**

1. **Use `|` (pipe)** to chain operations left-to-right
2. **Use `{}` (dict)** to create parallel branches or structure outputs
3. **Use `itemgetter("key")`** to extract specific fields from previous step
4. **Use `RunnablePassthrough()`** to pass entire input unchanged
5. **Use `RunnablePassthrough.assign()`** to add/transform fields while keeping existing ones

---

## 🚀 **Getting Started**

Start with the **Simple Chain** or **Basic RAG Chain** and add complexity only when needed!

```python
# Start here
simple_chain = prompt | llm | StrOutputParser()

# Add retrieval when you have custom documents
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# Add memory when you need conversation history
# Add branching when you need conditional logic
# And so on...
```

Pick the pattern that matches your needs! 🎯