"""
FastAPI application for multimodal agentic RAG system.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
import os
import uuid
import tempfile
import time


from app.services.document_parser import DocumentParser
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.rag_service import RAGService


from app.models.schemas import (
    UploadResponse,
    QueryRequest,
    QueryResponse,
    Citation,
    HealthResponse,
)

from dotenv import load_dotenv
load_dotenv()


# Global service instances
parser: DocumentParser | None = None
embedding_service: EmbeddingService | None = None
vector_store: VectorStore | None = None
rag_service: RAGService | None = None



@asynccontextmanager
async def lifespan(app: FastAPI):
    global parser, embedding_service, vector_store, rag_service

    print("🚀 Initializing services...")

    parser = DocumentParser(output_dir=Path("outputs/images"))

    embedding_service = EmbeddingService()

    vector_store = VectorStore(
        collection_name="documents",
        host=os.getenv("QDRANT_HOST", "localhost"),
        port=int(os.getenv("QDRANT_PORT", 6333)),
    )

    vector_store.create_collection(
        vector_size=embedding_service.embedding_dim
    )

    rag_service = RAGService(
        vector_store=vector_store,
        embedding_service=embedding_service,
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    print("✅ Services initialized")
    yield
    print("👋 Shutting down services...")



app = FastAPI(
    title="Multimodal Agentic RAG API",
    description="Production-grade multimodal agentic RAG system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path("outputs/images").mkdir(parents=True, exist_ok=True)
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")




@app.get("/")
async def root():
    return {
        "message": "Multimodal Agentic RAG API",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        info = vector_store.get_collection_info()
        return HealthResponse(
            status="healthy",
            collection_info=info,
            services={
                "parser": True,
                "embeddings": True,
                "vector_store": True,
                "rag": True,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    start = time.time()

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files supported")

    document_id = f"doc_{uuid.uuid4().hex[:12]}"

    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)

    temp_path = temp_dir / f"{document_id}.pdf"

    with open(temp_path, "wb") as f:
        f.write(await file.read())

    try:

        parsed = parser.parse_pdf(
            file_path=str(temp_path),
            document_id=document_id,
        )

        chunks = (
            parsed["text_chunks"]
            + parsed["tables"]
            + parsed["images"]
        )

        if not chunks:
            raise HTTPException(status_code=400, detail="No content extracted")

        texts = [c["content"] for c in chunks]

        embeddings = await embedding_service.embed_documents(texts)

        vector_store.add_documents(chunks, embeddings)

        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            text_chunks=len(parsed["text_chunks"]),
            tables=len(parsed["tables"]),
            images=len(parsed["images"]),
            processing_time_ms=int((time.time() - start) * 1000),
            message="Document processed successfully",
        )

    finally:

        temp_path.unlink(missing_ok=True)



@app.post("/query", response_model=QueryResponse)
async def query_document(request: QueryRequest):
    result = await rag_service.query(
        query=request.query,
        document_id=request.document_id,
        top_k=request.top_k,
    )

    citations = [Citation(**c) for c in result["citations"]]

    return QueryResponse(
        answer=result["answer"],
        citations=citations,
        images=result["images"],
        sources_used=result.get("sources_used", {}),
        processing_time_ms=0,
    )


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    vector_store.delete_document(document_id)
    return {"message": f"{document_id} deleted"}
