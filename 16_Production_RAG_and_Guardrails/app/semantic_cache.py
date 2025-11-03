"""Semantic LLM caching using Qdrant vector database."""

import hashlib
from typing import Optional
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from langchain_openai import OpenAIEmbeddings


class SemanticCache:
    """Semantic cache for LLM responses using vector similarity."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "llm_semantic_cache",
        similarity_threshold: float = 0.85,
        embedding_model: str = "text-embedding-3-small"
    ):
        """Initialize semantic cache.
        
        Args:
            host: Qdrant host
            port: Qdrant port
            collection_name: Name of the cache collection
            similarity_threshold: Minimum similarity score for cache hit (0-1)
            embedding_model: OpenAI embedding model to use
        """
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        self.similarity_threshold = similarity_threshold
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        collection_names = [col.name for col in collections]
        
        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=1536,  # OpenAI embedding size
                    distance=Distance.COSINE
                )
            )
    
    def _generate_id(self, prompt: str, model: str) -> str:
        """Generate unique ID for cache entry."""
        key = f"{prompt}:{model}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, prompt: str, model: str) -> Optional[str]:
        """Get cached response if similar prompt exists.
        
        Args:
            prompt: Input prompt
            model: Model name
            
        Returns:
            Cached response if found, None otherwise
        """
        try:
            # Get embedding for the prompt
            query_vector = self.embeddings.embed_query(prompt)
            
            # Search for similar prompts
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=1,
                score_threshold=self.similarity_threshold,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="model",
                            match=MatchValue(value=model)
                        )
                    ]
                )
            )
            
            if results and len(results) > 0:
                hit = results[0]
                print(f"✓ Cache hit! Similarity: {hit.score:.4f}")
                return hit.payload["response"]
            
            print("✗ Cache miss")
            return None
            
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, prompt: str, response: str, model: str):
        """Store prompt-response pair in cache.
        
        Args:
            prompt: Input prompt
            response: LLM response
            model: Model name
        """
        try:
            # Get embedding for the prompt
            vector = self.embeddings.embed_query(prompt)
            
            # Generate unique ID
            point_id = self._generate_id(prompt, model)
            
            # Create point
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "prompt": prompt,
                    "response": response,
                    "model": model,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            
            # Upsert point (update if exists, insert if not)
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            print(f"✓ Cached new response")
            
        except Exception as e:
            print(f"Cache set error: {e}")
    
    def clear(self):
        """Clear all cache entries."""
        try:
            self.client.delete_collection(self.collection_name)
            self._ensure_collection()
            print("✓ Cache cleared")
        except Exception as e:
            print(f"Cache clear error: {e}")
    
    def stats(self) -> dict:
        """Get cache statistics."""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "total_entries": collection_info.points_count,
                "collection_name": self.collection_name,
                "similarity_threshold": self.similarity_threshold
            }
        except Exception as e:
            return {"error": str(e)}

