"""
Vector store service using Qdrant.
Handles embedding storage, retrieval, and document-level filtering.
"""
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)
from typing import List, Dict, Any, Optional
import numpy as np


class VectorStore:
    def __init__(
        self, 
        collection_name: str = "documents",
        host: str = "localhost",
        port: int = 6333
    ):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name

    def create_collection(self, vector_size: int):
        """
        Create or recreate the collection.
        """
        # Check if collection exists
        collections = self.client.get_collections().collections
        collection_exists = any(c.name == self.collection_name for c in collections)
        
        if collection_exists:
            self.client.delete_collection(self.collection_name)
        
        # Create collection
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )

    def add_documents(
        self, 
        chunks: List[Dict[str, Any]], 
        embeddings: np.ndarray
    ):
        """
        Add document chunks with embeddings to Qdrant.
        Uses chunk_id to prevent ID collisions.
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Mismatch: {len(chunks)} chunks but {len(embeddings)} embeddings"
            )
        
        points = []
        
        for chunk, embedding in zip(chunks, embeddings):
            # Validate content_type
            content_type = chunk.get("content_type", "text")
            if content_type not in ["text", "table", "image"]:
                print(f"Warning: Invalid content_type '{content_type}', defaulting to 'text'")
                content_type = "text"
            
            # Validate embedding dimension
            if embedding.shape[0] == 0 or np.all(embedding == 0):
                print(f"Warning: Zero embedding for chunk {chunk['chunk_id']}, skipping")
                continue
            
            # Build payload (NO table_html)
            payload = {
                "document_id": chunk["document_id"],
                "content": chunk["content"],
                "content_type": content_type,
                "page_number": chunk.get("page_number", 1),
                "metadata": chunk.get("metadata", {})
            }
            
            # Add image_path only if it exists
            if "image_path" in chunk and chunk["image_path"]:
                payload["image_path"] = chunk["image_path"]
            
            # Use chunk_id as point ID to prevent collisions
            point = PointStruct(
                id=chunk["chunk_id"],
                vector=embedding.tolist(),
                payload=payload
            )
            points.append(point)
        
        # Upload to Qdrant
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

    def search(
        self, 
        query_embedding: np.ndarray, 
        limit: int = 5,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks.
        Supports optional document-level filtering.
        """
        # Validate embedding dimension
        if query_embedding.shape[0] == 0 or np.all(query_embedding == 0):
            print("Warning: Zero query embedding, returning empty results")
            return []
        
        # Build filter for document_id if provided
        query_filter = None
        if document_id:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        
        # Search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            limit=limit,
            query_filter=query_filter
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result.id,
                "score": result.score,
                "content": result.payload.get("content", ""),
                "content_type": result.payload.get("content_type", "text"),
                "page_number": result.payload.get("page_number", 1),
                "image_path": result.payload.get("image_path"),
                "document_id": result.payload.get("document_id"),
                "metadata": result.payload.get("metadata", {})
            })
        
        return formatted_results

    def delete_document(self, document_id: str):
        """
        Delete all chunks for a specific document.
        """
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get collection information.
        """
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            return {"error": str(e)}