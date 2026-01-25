"""
RAG service with explicit agentic behavior.
Handles retrieval and delegates analysis to Document Analysis Agent.
"""
from typing import List, Dict, Any, Optional
import os
from app.agents import DocumentAnalysisAgent


class RAGService:
    def __init__(
        self,
        vector_store,
        embedding_service,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None
    ):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.model = model
        
        # Initialize Document Analysis Agent
        self.agent = DocumentAnalysisAgent(
            model=model,
            api_key=api_key or os.getenv("OPENAI_API_KEY")
        )

    def query(
        self, 
        query: str, 
        document_id: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Process query with explicit agentic RAG.
        
        Flow:
        1. Deterministic retrieval (vector search)
        2. Agent analyzes evidence and makes decisions
        3. Agent generates grounded answer
        """
        # Embed query (deterministic)
        query_embedding = self.embedding_service.embed_query(query)
        
        # Retrieve relevant chunks (deterministic, document-scoped)
        retrieved_evidence = self.vector_store.search(
            query_embedding=query_embedding,
            limit=top_k,
            document_id=document_id
        )
        
        if not retrieved_evidence:
            return {
                "answer": "No relevant information found in the document.",
                "citations": [],
                "images": [],
                "agent_reasoning": "No evidence retrieved from vector store"
            }
        
        # Agent analyzes evidence and generates response (probabilistic)
        agent_result = self.agent.analyze(
            query=query,
            retrieved_evidence=retrieved_evidence
        )
        
        return {
            "answer": agent_result["final_answer"],
            "citations": agent_result["citations"],
            "images": agent_result["images"],
            "agent_reasoning": agent_result.get("agent_reasoning", ""),
            "evidence_sufficient": agent_result.get("evidence_sufficient", True),
            "confidence": agent_result.get("confidence", "unknown")
        }