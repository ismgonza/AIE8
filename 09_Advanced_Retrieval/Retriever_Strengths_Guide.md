# RAGAS Metrics - Retriever Strengths Guide
ref:
* (https://www.ibm.com/think/topics/rag-techniques)
* (https://medium.com/the-ai-forum/semantic-chunking-for-rag-f4733025d5f5)
## Metrics Overview

| Metric | Type | What It Measures | Best For | Why |
|--------|------|------------------|----------|-----|
| **ContextPrecision** | Retriever | How many retrieved chunks are actually relevant (low noise) | Compression Retriever, BM25 | Compression: Reranking removes irrelevant chunks<br>BM25: Keyword matching can be precise |
| **ContextRecall** | Retriever | How much of the ground truth information was retrieved (completeness) | Multi-Query, Parent Document, Ensemble | Multi-Query: Multiple query angles catch more info<br>Parent: Larger context windows<br>Ensemble: Combines multiple strategies |
| **ContextEntityRecall** | Retriever | Were the key entities/concepts from ground truth retrieved? | All retrievers (general indicator) | Parent Document expected high (larger chunks capture more entities) |
| **Faithfulness** | Generation | Is the generated response faithful to the retrieved context? | All retrievers | Shows if LLM is hallucinating or staying grounded. Should score similarly across retrievers (same LLM) |
| **FactualCorrectness** | Generation | Is the response factually correct vs. ground truth? | All retrievers | Overall quality indicator. Depends on both retrieval AND generation quality |
| **ResponseRelevancy** | Generation | Is the response relevant to the user's question? | All retrievers | Overall quality indicator. Should score similarly across retrievers (same LLM) |

---

## Expected Retriever Performance

| Retriever | Expected Strength | Key Metrics to Watch | Why Selected |
|-----------|-------------------|---------------------|--------------|
| **Naive** | Baseline | All metrics | Comparison point for all other retrievers |
| **BM25** | Keyword-heavy queries | ContextPrecision | Statistical keyword matching provides precise results for term-based queries |
| **Compression** | Low noise, high precision | ContextPrecision | Reranking step removes irrelevant chunks, improving precision |
| **Multi-Query** | Completeness | ContextRecall | Generates multiple query perspectives to catch more relevant information |
| **Parent Document** | More context | ContextRecall, ContextEntityRecall | Retrieves smaller chunks but returns larger parent documents with more complete context |
| **Ensemble** | Balanced performance | All metrics | Combines multiple retrieval strategies for well-rounded performance |
| **Semantic Chunking** | Coherent chunks | ContextPrecision, ContextEntityRecall | Meaning-based boundaries create more coherent, semantically complete chunks |

---

## Semantic Chunking Analysis

**Comparison:** Naive Retriever (fixed-size chunks) vs. Semantic Chunk Retriever (meaning-based chunks)

| Aspect | Naive (Semantic OFF) | Semantic Chunk (Semantic ON) | Expected Difference |
|--------|---------------------|------------------------------|---------------------|
| **Chunking Method** | RecursiveCharacterTextSplitter (fixed size) | SemanticChunker (meaning-based boundaries) | - |
| **ContextPrecision** | Baseline | ↑ Higher | More coherent, relevant chunks |
| **ContextEntityRecall** | Baseline | ↑ Higher | Chunks better capture complete entity information |
| **ContextRecall** | Baseline | ↓ Possibly Lower | Fewer, larger chunks might miss some details |
| **Use Case** | General purpose | When semantic coherence matters | Semantic chunking preserves meaning better |