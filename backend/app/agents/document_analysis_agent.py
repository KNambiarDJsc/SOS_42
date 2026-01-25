"""
Document Analysis Agent
A role-constrained LLM agent that analyzes retrieved evidence and generates grounded answers.

This agent:
1. Evaluates evidence sufficiency
2. Determines relevant modalities (text/table/image)
3. Generates grounded answers
4. Self-verifies each claim
5. Refuses to answer if evidence is insufficient
"""
import openai
import os
from typing import List, Dict, Any, Optional
import json


class DocumentAnalysisAgent:
    """
    Single autonomous agent for document analysis.
    Operates only on retrieved evidence, makes decisions about sufficiency and relevance.
    """
    
    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        self.model = model
        self.agent_name = "Document Analysis Agent"
        
        if api_key:
            openai.api_key = api_key
        else:
            openai.api_key = os.getenv("OPENAI_API_KEY")
    
    def analyze(
        self, 
        query: str, 
        retrieved_evidence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Main agent entry point.
        Analyzes retrieved evidence and generates a grounded response.
        
        Args:
            query: User's question
            retrieved_evidence: List of retrieved chunks with metadata
            
        Returns:
            {
                "final_answer": str,
                "citations": List[Dict],
                "images": List[str],
                "agent_reasoning": str,
                "evidence_sufficient": bool
            }
        """
        # Build structured evidence for agent
        evidence = self._structure_evidence(retrieved_evidence)
        
        # Get agent's analysis and response
        agent_response = self._run_agent(query, evidence)
        
        # Extract structured output
        result = self._parse_agent_response(agent_response, retrieved_evidence)
        
        return result
    
    def _structure_evidence(self, retrieved_evidence: List[Dict[str, Any]]) -> str:
        """
        Structure retrieved evidence for agent analysis.
        """
        evidence_parts = []
        
        for idx, chunk in enumerate(retrieved_evidence, 1):
            content_type = chunk.get("content_type", "text")
            content = chunk.get("content", "")
            page = chunk.get("page_number", "unknown")
            score = chunk.get("score", 0.0)
            
            evidence_entry = f"""
[Evidence {idx}]
Type: {content_type}
Page: {page}
Relevance Score: {score:.2f}
Content: {content}
"""
            
            if content_type == "image" and chunk.get("image_path"):
                evidence_entry += f"Image Available: Yes (path: {chunk.get('image_path')})\n"
            
            evidence_parts.append(evidence_entry)
        
        return "\n".join(evidence_parts)
    
    def _run_agent(self, query: str, evidence: str) -> str:
        """
        Run the Document Analysis Agent with role-constrained prompting.
        """
        system_prompt = f"""You are the {self.agent_name}, an autonomous AI agent responsible for analyzing document evidence and generating grounded answers.

YOUR ROLE AND RESPONSIBILITIES:
1. EVIDENCE EVALUATION: Assess whether the provided evidence is sufficient to answer the query
2. MODALITY ANALYSIS: Determine which modalities (text/table/image) are relevant
3. ANSWER GENERATION: Generate accurate, grounded answers using only the evidence
4. SELF-VERIFICATION: Verify each claim is directly supported by evidence
5. HONEST REFUSAL: Refuse to answer if evidence is insufficient or irrelevant

DECISION-MAKING PROTOCOL:
Step 1: Analyze the query and identify what information is needed
Step 2: Evaluate each piece of evidence for relevance and sufficiency
Step 3: Determine which modalities contain the answer:
   - Text evidence for prose, explanations, narratives
   - Table evidence for structured data, statistics, comparisons
   - Image evidence for visual information, diagrams, charts
Step 4: Construct answer using ONLY supported claims
Step 5: Self-verify: Can you cite a specific evidence number for each claim?
Step 6: If verification fails or evidence is insufficient → refuse to answer

OUTPUT REQUIREMENTS:
You must respond in this exact JSON format:
{{
    "evidence_sufficient": true/false,
    "relevant_modalities": ["text", "table", "image"],
    "reasoning": "Your step-by-step analysis of the evidence",
    "answer": "Your grounded answer OR explanation of why you cannot answer",
    "cited_evidence_ids": [1, 2, 3],
    "confidence": "high/medium/low"
}}

CRITICAL RULES:
- NEVER invent information not in the evidence
- ALWAYS cite specific evidence numbers
- If evidence is insufficient, say so explicitly
- If evidence contradicts itself, note the contradiction
- Prioritize accuracy over helpfulness
- Be concise but complete"""

        user_prompt = f"""QUERY: {query}

RETRIEVED EVIDENCE:
{evidence}

Analyze this evidence and generate a response following your decision-making protocol.
Return your response as valid JSON."""

        # Single LLM call with agent role
        response = openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Low temperature for deterministic reasoning
            max_tokens=1500,
            response_format={"type": "json_object"}  # Ensure JSON output
        )
        
        return response.choices[0].message.content
    
    def _parse_agent_response(
        self, 
        agent_response: str, 
        retrieved_evidence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Parse agent's JSON response and extract structured output.
        """
        try:
            parsed = json.loads(agent_response)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "final_answer": "I encountered an error analyzing the evidence. Please try again.",
                "citations": [],
                "images": [],
                "agent_reasoning": "JSON parsing failed",
                "evidence_sufficient": False
            }
        
        # Extract agent decisions
        evidence_sufficient = parsed.get("evidence_sufficient", False)
        cited_ids = parsed.get("cited_evidence_ids", [])
        relevant_modalities = parsed.get("relevant_modalities", [])
        
        # Build citations from cited evidence
        citations = self._extract_citations(retrieved_evidence, cited_ids)
        
        # Extract images if agent determined they're relevant
        images = self._extract_images(
            retrieved_evidence, 
            cited_ids, 
            relevant_modalities
        )
        
        return {
            "final_answer": parsed.get("answer", "No answer generated."),
            "citations": citations,
            "images": images,
            "agent_reasoning": parsed.get("reasoning", ""),
            "evidence_sufficient": evidence_sufficient,
            "confidence": parsed.get("confidence", "unknown")
        }
    
    def _extract_citations(
        self, 
        retrieved_evidence: List[Dict[str, Any]], 
        cited_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """
        Extract citations for evidence IDs cited by the agent.
        """
        citations = []
        seen_pages = set()
        
        for idx in cited_ids:
            if 0 < idx <= len(retrieved_evidence):
                chunk = retrieved_evidence[idx - 1]  # Convert to 0-indexed
                page = chunk.get("page_number", 1)
                
                # Deduplicate by page
                if page not in seen_pages:
                    citations.append({
                        "page": page,
                        "content_type": chunk.get("content_type", "text"),
                        "score": chunk.get("score", 0.0)
                    })
                    seen_pages.add(page)
        
        # Sort by page number
        citations.sort(key=lambda x: x["page"])
        return citations
    
    def _extract_images(
        self, 
        retrieved_evidence: List[Dict[str, Any]], 
        cited_ids: List[int],
        relevant_modalities: List[str]
    ) -> List[str]:
        """
        Extract image paths if agent determined images are relevant.
        """
        # Only return images if agent decided they're relevant
        if "image" not in relevant_modalities:
            return []
        
        images = []
        seen_images = set()
        
        for idx in cited_ids:
            if 0 < idx <= len(retrieved_evidence):
                chunk = retrieved_evidence[idx - 1]
                
                if chunk.get("content_type") == "image":
                    image_path = chunk.get("image_path")
                    if image_path and image_path not in seen_images:
                        images.append(image_path)
                        seen_images.add(image_path)
        
        return images