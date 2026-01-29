# SOS 42 – Multimodal Agentic RAG System

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95%2B-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-13%2B-black?logo=next.js&logoColor=white)
![Qdrant](https://img.shields.io/badge/Vector_DB-Qdrant-red?logo=qdrant&logoColor=white)
![OpenAI](https://img.shields.io/badge/AI-OpenAI-412991?logo=openai&logoColor=white)

> **A production-grade agentic Retrieval-Augmented Generation (RAG) system that parses PDFs containing text, tables, and images, indexes them in a vector database, and enables grounded question answering through an explicit agentic reasoning layer.**

*Built as part of the SOS 42 AI Intern Assignment.*

---

## 🚀 Overview

This project implements an **Explicit Agentic RAG** architecture designed for high-accuracy document analysis. Unlike standard RAG pipelines that blindly retrieve and generate, this system employs a dedicated reasoning agent to analyze multimodal evidence before formulating an answer.

The system is designed for **accuracy**, **explainability**, and **extensibility**. It parses complex PDF structures (text, tables, and images), embeds them into a vector store, and uses an LLM-based agent to synthesize grounded responses with citations.

### 🧠 Why Agentic RAG?
Instead of a simple linear `retrieve → generate` pipeline, this system uses an explicit agent to:
1.  **Assess Relevance:** Critically evaluate if the retrieved chunks actually answer the user query.
2.  **Multimodal Synthesis:** Intelligently combine insights from text, tabular data, and visual charts.
3.  **Strict Grounding:** Generate answers *only* from retrieved context to eliminate hallucinations.
4.  **Evidence Citation:** Return explicit citations and visual references for verification.

---

## 🏗️ Architecture

The system follows a modular microservices pattern with a clean separation of concerns between parsing, indexing, retrieval, and reasoning.

```mermaid
graph TD
    subgraph "Ingestion Pipeline"
    A[PDF Upload] --> B{Parser Engine}
    B -->|Text| C[Chunking]
    B -->|Tables| D[HTML/Markdown Conv]
    B -->|Images| E[Image Description/OCR]
    C & D & E --> F[OpenAI Embeddings]
    F --> G[(Qdrant Vector Store)]
    end

    subgraph "Agentic Inference"
    H[User Query] --> I[Deterministic Retrieval]
    I -->|Top Context| J[Document Analysis Agent]
    G <--> I
    J -->|Reasoning| K{Relevance Check}
    K -->|Evidence Found| L[Generate Grounded Answer]
    K -->|Insufficient Data| M[Fallback Protocol]
    L --> N[Final Response + Citations + Images]
    end