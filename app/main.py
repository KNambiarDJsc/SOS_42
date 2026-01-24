"""
FastAPI application for multimodal agentic RAG system.
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import uuid
from pathlib import Path

# Import services
from app.services.document_parser import DocumentParser
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.rag_service import RAGService

# Import schemas (no duplicates)
from app.models.schemas import (
    UploadResponse,
    QueryRequest,
    QueryResponse,
    Citation,
    HealthResponse,
    ErrorResponse
)


# Global service instances
parser = None
embedding_service = None
vector_store = None
rag_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown.
    """
    # Startup
    global parser, embedding_service, vector_store, rag_service
    
    print("🚀 Initializing services...")
    
    # Initialize services
    parser = DocumentParser(output_dir="outputs/images")
    embedding_service = EmbeddingService()
    vector_store = VectorStore(
        collection_name="documents",
        host=os.getenv("QDRANT_HOST", "localhost"),
        port=int(os.getenv("QDRANT_PORT", 6333))
    )
    
    # Create collection
    vector_store.create_collection(vector_size=embedding_service.embedding_dim)
    
    # Initialize RAG service
    rag_service = RAGService(
        vector_store=vector_store,
        embedding_service=embedding_service,
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    print("✅ Services initialized successfully")
    
    yield
    
    # Shutdown
    print("👋 Shutting down services...")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Multimodal Agentic RAG API",
    description="Production-grade RAG system with PDF parsing, embeddings, and retrieval",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for image serving
outputs_dir = Path("outputs")
outputs_dir.mkdir(exist_ok=True)
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Multimodal Agentic RAG API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    try:
        vector_info = vector_store.get_collection_info()
        return HealthResponse(
            status="healthy",
            vector_store=vector_info
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/upload", response_model=UploadResponse, tags=["Documents"])
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a PDF document.
    Extracts text, tables, and images, then stores embeddings.
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Generate document ID
        document_id = f"doc_{uuid.uuid4().hex[:12]}"
        
        # Save uploaded file temporarily
        temp_path = f"/tmp/{document_id}.pdf"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Parse PDF synchronously (not async)
        parsed_doc = parser.parse_pdf(temp_path, document_id)
        
        # Extract chunks
        chunks = parsed_doc["chunks"]
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No content extracted from PDF")
        
        # Embed chunks
        texts = [chunk["content"] for chunk in chunks]
        embeddings = embedding_service.embed_documents(texts)
        
        # Store in vector database
        vector_store.add_documents(chunks, embeddings)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return UploadResponse(
            document_id=document_id,
            total_chunks=parsed_doc["total_chunks"],
            message=f"Document processed successfully with {len(chunks)} chunks"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def query_document(request: QueryRequest):
    """
    Query a document with document_id scoping.
    Returns answer, citations, and images.
    """
    try:
        # Validate inputs
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if not request.document_id.strip():
            raise HTTPException(status_code=400, detail="document_id is required")
        
        # Process query with document_id scoping
        result = rag_service.query(
            query=request.query,
            document_id=request.document_id,
            top_k=request.top_k
        )
        
        # Convert citations to Pydantic models
        citations = [Citation(**cite) for cite in result["citations"]]
        
        return QueryResponse(
            answer=result["answer"],
            citations=citations,
            images=result["images"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{document_id}", tags=["Documents"])
async def delete_document(document_id: str):
    """
    Delete a document and all its chunks from the vector store.
    """
    try:
        vector_store.delete_document(document_id)
        return {"message": f"Document {document_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )