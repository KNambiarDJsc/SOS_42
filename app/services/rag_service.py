"""
RAG service with implicit agentic behavior.
Handles retrieval and generation with single LLM call.
"""
from typing import List, Dict, Any, Optional
import openai
import os


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
        
        # Set OpenAI API key
        if api_key:
            openai.api_key = api_key
        else:
            openai.api_key = os.getenv("OPENAI_API_KEY")

    def query(
        self, 
        query: str, 
        document_id: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Process query with implicit agentic RAG.
        Single LLM call with explicit agent role.
        """
        # Embed query
        query_embedding = self.embedding_service.embed_query(query)
        
        # Retrieve relevant chunks (document-scoped)
        results = self.vector_store.search(
            query_embedding=query_embedding,
            limit=top_k,
            document_id=document_id
        )
        
        if not results:
            return {
                "answer": "No relevant information found in the document.",
                "citations": [],
                "images": []
            }
        
        # Build context from retrieved chunks
        context = self._build_context(results)
        
        # Generate answer with implicit agentic prompt
        answer = self._generate_answer(query, context, results)
        
        # Extract citations and images
        citations = self._extract_citations(results)
        images = self._extract_images(results)
        
        return {
            "answer": answer,
            "citations": citations,
            "images": images
        }

    def _build_context(self, results: List[Dict[str, Any]]) -> str:
        """
        Build context string from retrieved chunks.
        Ensures image descriptions always exist.
        """
        context_parts = []
        
        for idx, result in enumerate(results, 1):
            content_type = result.get("content_type", "text")
            content = result.get("content", "")
            page = result.get("page_number", 1)
            
            # Ensure image descriptions exist
            if content_type == "image":
                if not content or content.strip() == "":
                    content = f"Image on page {page}"
            
            context_parts.append(
                f"[Source {idx}] (Page {page}, Type: {content_type})\n{content}"
            )
        
        return "\n\n".join(context_parts)

    def _generate_answer(
        self, 
        query: str, 
        context: str, 
        results: List[Dict[str, Any]]
    ) -> str:
        """
        Generate answer using single LLM call with explicit agent role.
        No planner/searcher/refiner loops - implicit agentic RAG.
        """
        system_prompt = """You are an expert research assistant analyzing documents.

Your role:
- Analyze the provided context carefully
- Answer the user's question accurately and concisely
- Ground your answer in the provided sources
- Cite sources using [Source N] notation
- If information is insufficient, acknowledge limitations
- Maintain a professional, helpful tone

Important:
- Only use information from the provided context
- Do not speculate or add external knowledge
- Be precise and factual"""

        user_prompt = f"""Context from document:

{context}

Question: {query}

Provide a clear, grounded answer based on the context above. Cite sources using [Source N] notation."""

        # Single LLM call
        response = openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        return response.choices[0].message.content

    def _extract_citations(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract citations from results with simplified logic.
        Uses dict/set internally, outputs list.
        """
        # Use dict to avoid duplicates by page number
        citations_dict = {}
        
        for result in results:
            page = result.get("page_number", 1)
            content_type = result.get("content_type", "text")
            
            # Use page as key to deduplicate
            if page not in citations_dict:
                citations_dict[page] = {
                    "page": page,
                    "content_type": content_type,
                    "score": result.get("score", 0.0)
                }
        
        # Convert to list sorted by page number
        citations = list(citations_dict.values())
        citations.sort(key=lambda x: x["page"])
        
        return citations

    def _extract_images(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        Extract image paths from results.
        """
        images = []
        seen = set()
        
        for result in results:
            if result.get("content_type") == "image":
                image_path = result.get("image_path")
                if image_path and image_path not in seen:
                    images.append(image_path)
                    seen.add(image_path)
        
        return images