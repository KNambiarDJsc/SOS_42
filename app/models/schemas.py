"""
Pydantic schemas for API request/response models.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class UploadResponse(BaseModel):
    """Response for document upload."""
    document_id: str
    total_chunks: int
    message: str


class QueryRequest(BaseModel):
    """Request model for querying documents."""
    query: str = Field(..., description="The question to ask about the document")
    document_id: str = Field(..., description="The ID of the document to query")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")


class Citation(BaseModel):
    """Citation information."""
    page: int
    content_type: str
    score: float


class QueryResponse(BaseModel):
    """Response for document queries."""
    answer: str
    citations: List[Citation]
    images: List[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    vector_store: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None