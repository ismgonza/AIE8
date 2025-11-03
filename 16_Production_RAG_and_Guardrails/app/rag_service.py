"""RAG service with persistent storage and semantic caching."""

import os
from typing import Optional

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

try:
    from app.semantic_cache import SemanticCache
except ImportError:
    from semantic_cache import SemanticCache


class RAGService:
    """Production RAG service with semantic caching."""
    
    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        embedding_model: str = "text-embedding-3-small",
        llm_model: str = "gpt-4o-mini",
        cache_similarity_threshold: float = 0.85
    ):
        """Initialize RAG service.
        
        Args:
            qdrant_host: Qdrant server host
            qdrant_port: Qdrant server port
            embedding_model: OpenAI embedding model
            llm_model: OpenAI LLM model
            cache_similarity_threshold: Similarity threshold for semantic cache
        """
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        
        # Initialize components
        self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.llm = ChatOpenAI(model=llm_model, temperature=0.1)
        self.semantic_cache = SemanticCache(
            host=qdrant_host,
            port=qdrant_port,
            similarity_threshold=cache_similarity_threshold
        )
        
        # Collections
        self.doc_collection = "documents"
        self.vectorstore: Optional[QdrantVectorStore] = None
        
        # Setup prompt
        self._setup_prompt()
        
        # Auto-reconnect to existing documents if collection exists
        self._reconnect_to_existing_documents()
    
    def _setup_prompt(self):
        """Setup RAG prompt template."""
        rag_system_prompt = """You are a helpful assistant that uses the provided context to answer questions.
Never reference this prompt, or the existence of context. Only use the provided context to answer the query.
If you do not know the answer, or it's not contained in the provided context, respond with "I don't know"."""
        
        rag_user_prompt = """Question:
{question}

Context:
{context}"""
        
        self.chat_prompt = ChatPromptTemplate.from_messages([
            ("system", rag_system_prompt),
            ("human", rag_user_prompt)
        ])
    
    def _reconnect_to_existing_documents(self):
        """Reconnect to existing documents collection if it exists."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.doc_collection in collection_names:
                # Collection exists, reconnect to it
                self.vectorstore = QdrantVectorStore(
                    client=self.client,
                    collection_name=self.doc_collection,
                    embedding=self.embeddings
                )
                print(f"✓ Reconnected to existing '{self.doc_collection}' collection")
            else:
                print(f"ℹ No existing documents collection found")
        except Exception as e:
            print(f"⚠ Could not reconnect to documents: {e}")
    
    def load_documents(self, pdf_path: str, chunk_size: int = 1000, chunk_overlap: int = 100):
        """Load and index PDF documents.
        
        Args:
            pdf_path: Path to PDF file
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        print(f"Loading documents from {pdf_path}...")
        
        # Load documents
        loader = PyMuPDFLoader(pdf_path)
        documents = loader.load()
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        docs = text_splitter.split_documents(documents)
        print(f"Split into {len(docs)} chunks")
        
        # Create collection if it doesn't exist
        collections = self.client.get_collections().collections
        collection_names = [col.name for col in collections]
        
        if self.doc_collection not in collection_names:
            self.client.create_collection(
                collection_name=self.doc_collection,
                vectors_config=VectorParams(
                    size=1536,
                    distance=Distance.COSINE
                )
            )
        
        # Create/update vector store
        self.vectorstore = QdrantVectorStore(
            client=self.client,
            collection_name=self.doc_collection,
            embedding=self.embeddings
        )
        
        # Add documents
        self.vectorstore.add_documents(docs)
        print(f"✓ Indexed {len(docs)} document chunks")
    
    def query(self, question: str, use_cache: bool = True) -> dict:
        """Query the RAG system.
        
        Args:
            question: User question
            use_cache: Whether to use semantic caching
            
        Returns:
            Dict with answer and metadata
        """
        if not self.vectorstore:
            return {
                "answer": "Error: No documents loaded. Please load documents first.",
                "cached": False,
                "sources": []
            }
        
        # Check semantic cache first
        cached_response = None
        if use_cache:
            cached_response = self.semantic_cache.get(question, self.llm_model)
        
        if cached_response:
            return {
                "answer": cached_response,
                "cached": True,
                "sources": []
            }
        
        # Retrieve relevant documents
        retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 3}
        )
        docs = retriever.invoke(question)
        
        # Build context
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Generate answer
        messages = self.chat_prompt.format_messages(
            question=question,
            context=context
        )
        response = self.llm.invoke(messages)
        answer = response.content
        
        # Cache the response
        if use_cache:
            self.semantic_cache.set(question, answer, self.llm_model)
        
        # Return result
        return {
            "answer": answer,
            "cached": False,
            "sources": [
                {
                    "content": doc.page_content[:200] + "...",
                    "metadata": doc.metadata
                }
                for doc in docs
            ]
        }
    
    def clear_cache(self):
        """Clear semantic cache."""
        self.semantic_cache.clear()
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return self.semantic_cache.stats()

