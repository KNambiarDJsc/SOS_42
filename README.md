SOS 42 – Multimodal Agentic RAG System

A production-grade agentic Retrieval-Augmented Generation (RAG) system that parses PDFs containing text, tables, and images, indexes them in a vector database, and enables grounded question answering through an explicit agentic reasoning layer.

Built as part of the SOS 42 AI Intern Assignment.

🚀 Overview

This project implements an explicit agentic RAG architecture, where:

Documents are parsed into multimodal components (text, tables, images)

All components are embedded and stored in a vector database

Queries trigger deterministic retrieval

A dedicated Document Analysis Agent reasons over retrieved evidence

The agent generates a grounded answer with citations and visual references

The system is designed for accuracy, explainability, and extensibility, not just demo-level RAG.

🧠 Why Agentic RAG?

Instead of a simple “retrieve → generate” pipeline, this system uses an explicit agent to:

Assess relevance of retrieved evidence

Decide how to use text vs tables vs images

Generate answers only from retrieved context

Return citations and visual references

This mirrors how modern production RAG systems are built in 2025+.

🏗️ Architecture
High-level flow
PDF Upload
   ↓
Multimodal Parsing (text / tables / images)
   ↓
Embeddings (OpenAI)
   ↓
Vector Store (Qdrant)
   ↓
Query
   ↓
Deterministic Retrieval
   ↓
Document Analysis Agent (LLM)
   ↓
Grounded Answer + Citations + Images

📁 Project Structure
sos42-rag-system/
├── app/                        # Backend (FastAPI)
│   ├── main.py                 # API entrypoint
│   ├── models/
│   │   └── schemas.py          # Pydantic schemas
│   └── services/
│       ├── document_parser.py  # PDF parsing (text, tables, images)
│       ├── embeddings.py       # Embedding service (OpenAI)
│       ├── vector_store.py     # Qdrant integration
│       └── rag_service.py      # Agentic RAG orchestration
│
├── frontend/                   # Frontend (Next.js)
│   └── src/app/
│       ├── page.tsx            # Upload + Chat UI
│       ├── layout.tsx
│       └── globals.css
│
├── outputs/images/             # Extracted images (served statically)
├── docker-compose.yml          # Qdrant service
├── requirements.txt
├── README.md
└── SETUP.md

🔑 Key Features
✅ Multimodal PDF Parsing

Extracts:

Text blocks

Tables

Images

Preserves metadata (page number, content type)

✅ Vector Search with Qdrant

Document-scoped retrieval

Fast cosine similarity search

Production-ready storage layer

✅ Explicit Agentic Reasoning

Dedicated Document Analysis Agent

Separates:

Retrieval (deterministic)

Reasoning (probabilistic)

Improves answer grounding and reliability

✅ Grounded Answers

Responses are generated only from retrieved evidence

Citations included

Relevant images surfaced when applicable

✅ Clean API Design

/upload – upload and process PDFs

/query – ask questions scoped to a document

/health – system health check

🧪 Example Workflow

Upload a PDF

System parses and indexes all content

Ask:

“Summarize the key findings from section 3”

System:

Retrieves relevant chunks

Agent analyzes evidence

Returns a concise answer with sources and images

🛠️ Tech Stack

Backend

FastAPI

OpenAI (embeddings + LLM)

Qdrant (vector database)

Unstructured (PDF parsing)

Frontend

Next.js (App Router)

Tailwind CSS

Framer Motion

Infrastructure

Docker (Qdrant)

Async Python (production-safe patterns)