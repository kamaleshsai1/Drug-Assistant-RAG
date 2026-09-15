# DrugAssist --- Agentic RAG Drug Information Assistant

> An evidence-first AI assistant for retrieving and understanding
> trusted medication information using Agentic RAG, semantic search,
> verified pharmaceutical documentation, and large language models.

[![Live
Demo](https://img.shields.io/badge/Live-Demo-success)](https://drugassist-frontend.onrender.com)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688)](https://drug-assist-agentic-rag.onrender.com)
[![API
Docs](https://img.shields.io/badge/API-Swagger-85EA2D)](https://drug-assist-agentic-rag.onrender.com/docs)
[![Frontend](https://img.shields.io/badge/Frontend-React-61DAFB)](https://react.dev/)
[![Vector
DB](https://img.shields.io/badge/Vector%20DB-Pinecone-000000)](https://www.pinecone.io/)
[![LLM](https://img.shields.io/badge/LLM-Groq-orange)](https://groq.com/)

## 🌐 Live Application

-   **Frontend:** https://drugassist-frontend.onrender.com
-   **Backend API:** https://drug-assist-agentic-rag.onrender.com
-   **Swagger / OpenAPI:**
    https://drug-assist-agentic-rag.onrender.com/docs
-   **GitHub:**
    https://github.com/kamaleshsai1/Drug-Assistant-RAG

## 📌 Overview

DrugAssist is an AI-powered drug information assistant built using an
Agentic Retrieval-Augmented Generation (RAG) architecture.

The system retrieves relevant information from trusted pharmaceutical
documents before generating responses. It combines document retrieval,
vector search, agentic routing, and LLM reasoning to provide
evidence-grounded answers.

A major focus is **document trust and provenance**. User-uploaded
medication documents are not automatically considered authoritative.
Before indexing, documents go through verification designed to prevent
arbitrary, fabricated, or modified medication documents from being
blindly accepted as trusted sources.

## 🎯 Problem Statement

Medication information is often available in lengthy
prescribing-information documents. Finding specific information manually
can be difficult because documents are long, terminology is complex,
relevant information can be distributed across sections, and users need
confidence in the source of an answer.

DrugAssist addresses this with:

**Trusted Document Verification + Semantic Search + Agentic Routing +
RAG + LLM Generation**

## 💡 Key Features

### 🔐 Authentication

-   User registration
-   User login
-   JWT-based authentication
-   Protected backend endpoints

### 📄 Trusted Medication Document Upload

The ingestion workflow is:

``` text
PDF Upload
    ↓
Document Verification
    ↓
Source / Provenance Validation
    ↓
Fingerprint Verification
    ↓
Trusted?
   ↙   ↘
 Yes    No
  ↓      ↓
Index   Reject
```

SHA-256 document fingerprints are used as part of the trust-verification
process.

### 🧠 Agentic RAG

The system uses agent-oriented routing to determine how a query should
be handled.

Possible routes include: - Vector retrieval - SQL/database operations -
Web information retrieval - General LLM reasoning

### 🔎 Semantic Vector Search

Documents are extracted, chunked, embedded, and stored in a vector
database.

``` text
User Question
      ↓
Query Embedding
      ↓
Semantic Similarity Search
      ↓
Relevant Document Chunks
      ↓
LLM
      ↓
Evidence-Grounded Answer
```

### 📚 Document Library

Users can: - View uploaded documents - Open PDF documents - Access
document information - Ask questions about documents

### 📖 Integrated PDF Viewer

Uploaded PDFs can be opened directly from the Library so users can
inspect the original source.

### 🖼️ Image Analysis

The backend supports image input and image analysis.

### 💬 Conversational Interface

The frontend provides: - Chat conversations - Chat history - File
attachments - PDF uploads - Image attachments - Voice input interface -
Document-based questions

### ☁️ Cloud Deployment

The application is deployed on Render as: - React + Vite frontend →
Render Static Site - FastAPI backend → Render Web Service - Pinecone →
vector database - Groq → LLM inference

## 🏗️ System Architecture

``` text
                         ┌───────────────────────┐
                         │         USER          │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │    React + Vite UI    │
                         │       Frontend        │
                         └───────────┬───────────┘
                                     │
                                  REST API
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │       FastAPI         │
                         │       Backend         │
                         └───────────┬───────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
       ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
       │    Auth     │        │    Agent    │        │ PDF / Image │
       │    + JWT    │        │   Router    │        │ Processing   │
       └─────────────┘        └──────┬──────┘        └─────────────┘
                                     │
                       ┌─────────────┼─────────────┐
                       ▼             ▼             ▼
                 ┌──────────┐  ┌──────────┐  ┌──────────┐
                 │ Pinecone │  │ SQL / DB │  │ Web Tool │
                 └────┬─────┘  └──────────┘  └──────────┘
                      │
                      ▼
                 ┌──────────┐
                 │ Groq LLM │
                 └────┬─────┘
                      │
                      ▼
                 ┌──────────────┐
                 │ Final Answer │
                 └──────────────┘
```

## 🔄 RAG Pipeline

``` text
Trusted Medication PDF
        ↓
Document Verification
        ↓
PDF Text Extraction
        ↓
Text Chunking
        ↓
Embedding Generation
        ↓
Pinecone Vector Database
        ↓
User Question
        ↓
Agentic Routing
        ↓
Semantic Retrieval
        ↓
Relevant Context
        ↓
Groq LLM
        ↓
Evidence-Grounded Response
```

## 🛠️ Technology Stack

### Frontend

-   React
-   Vite
-   JavaScript
-   JSX
-   CSS
-   Lucide React

### Backend

-   Python
-   FastAPI
-   Uvicorn
-   JWT Authentication

### AI / RAG

-   Retrieval-Augmented Generation (RAG)
-   Agentic Routing
-   FastEmbed
-   BGE-small-en-v1.5 embeddings
-   Groq LLM inference

### Vector Database

-   Pinecone Serverless

### Database

-   SQLite
-   Authentication database
-   Application data storage
-   Conversation / memory storage

### Document Processing

-   PDF text extraction
-   Text chunking
-   Document verification
-   SHA-256 document fingerprinting
-   Image analysis

### Development & Deployment

-   VS Code
-   Git
-   GitHub
-   REST APIs
-   Swagger / OpenAPI
-   Render

## 📁 Project Structure

``` text
Drug-Assist-Agentic-RAG/
│
├── backend/
│   ├── database/
│   │   ├── auth_db.py
│   │   ├── database.py
│   │   └── memory_db.py
│   ├── auth.py
│   ├── console.py
│   ├── debug_crohn.py
│   ├── embeddings.py
│   ├── image_analyzer.py
│   ├── inspect_pages.py
│   ├── main.py
│   ├── pdf_processor.py
│   ├── pinecone_db.py
│   ├── rag.py
│   ├── requirements.txt
│   └── test_suite.py
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   │   ├── AttachmentMenu.jsx
│   │   │   ├── AuthPage.jsx
│   │   │   ├── ChatInput.jsx
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── Composer.jsx
│   │   │   ├── ConfirmationModal.jsx
│   │   │   ├── FAQAccordion.jsx
│   │   │   ├── FeatureCards.jsx
│   │   │   ├── FeedbackModal.jsx
│   │   │   ├── Library.jsx
│   │   │   ├── Login.jsx
│   │   │   ├── Message.jsx
│   │   │   ├── PrivacyPolicy.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   └── TermsAndConditions.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.css
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
│
├── .gitignore
└── README.md
```

## ⚙️ Local Installation

### 1. Clone

``` bash
git clone https://github.com/Deekshitha-Gajjala/Drug-Assist-Agentic-RAG.git
cd Drug-Assist-Agentic-RAG
```

### 2. Backend

``` bash
cd backend
python -m venv venv
venv\Scriptsctivate
pip install -r requirements.txt
```

Create `backend/.env`:

``` env
GROQ_API_KEY=your_groq_api_key

PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=your_pinecone_index
PINECONE_NAMESPACE=your_pinecone_namespace
PINECONE_TOP_K=your_top_k
PINECONE_BATCH_SIZE=your_batch_size

DRUGASSIST_JWT_SECRET=your_jwt_secret

GROQ_MODEL=your_groq_model
GROQ_FALLBACK_MODEL=your_fallback_model
```

Run:

``` bash
uvicorn main:app --reload
```

Backend: `http://127.0.0.1:8000`

Swagger: `http://127.0.0.1:8000/docs`

### 3. Frontend

Open another terminal:

``` bash
cd frontend
npm install
```

Create `frontend/.env`:

``` env
VITE_API_URL=http://127.0.0.1:8000
```

Run:

``` bash
npm run dev
```

## ☁️ Render Deployment

### Backend --- Web Service

**Root Directory**

``` text
backend
```

**Build Command**

``` bash
pip install -r requirements.txt
```

**Start Command**

``` bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Configure the backend secrets in Render Environment Variables.

### Frontend --- Static Site

**Root Directory**

``` text
frontend
```

**Build Command**

``` bash
npm install && npm run build
```

**Publish Directory**

``` text
dist
```

**Environment Variable**

``` env
VITE_API_URL=https://drug-assist-agentic-rag.onrender.com
```

## 🔐 Security

Sensitive credentials are stored as environment variables and excluded
from Git.

The repository excludes:

``` text
.env
backend/.env
frontend/.env
backend/venv/
frontend/node_modules/
frontend/dist/
backend/uploads/
*.db
```

Never commit API keys, JWT secrets, passwords, or other credentials to
GitHub.

### Document Trust

DrugAssist does not assume every uploaded PDF is authoritative.

``` text
Uploaded Document
       ↓
Source Verification
       ↓
Fingerprint Verification
       ↓
Trusted?
    /       YES      NO
   ↓        ↓
 Index    Reject
```

## 🧪 Example User Workflow

``` text
1. Register / Login
        ↓
2. Upload trusted medication PDF
        ↓
3. Document verification
        ↓
4. PDF processing
        ↓
5. Text chunking
        ↓
6. Embedding generation
        ↓
7. Store vectors in Pinecone
        ↓
8. Ask a question
        ↓
9. Agent determines appropriate route
        ↓
10. Retrieve relevant information
        ↓
11. Generate response using Groq
        ↓
12. Inspect the original PDF
```

## 💬 Example Questions

``` text
What is this medication used for?

What are the major warnings?

What are the contraindications?

What are the common adverse reactions?

What dosage information is provided?

What monitoring information is mentioned?
```

## 📌 Why Agentic RAG?

Traditional chatbot:

``` text
Question → LLM → Answer
```

DrugAssist:

``` text
Question
   ↓
Agentic Router
   ↓
Determine Required Source
   ↓
Retrieve Information
   ↓
LLM
   ↓
Evidence-Grounded Answer
```

This makes the application more modular and allows different information
sources and tools to be incorporated into the workflow.

## 📖 Evidence-First Design

DrugAssist follows the principle:

> **Retrieve relevant evidence before generating an answer.**

Users can inspect the original document so that generated information
can be checked against the source.

This design is particularly important for medication-related
information, where incorrect or unsupported information can have serious
consequences.

## 🚀 Future Enhancements

-   Additional verified pharmaceutical sources
-   Expanded document provenance tracking
-   Advanced citation verification
-   Multi-document comparison
-   Multilingual medication information
-   Improved conversational memory
-   Advanced agent planning
-   Cloud object storage for uploaded documents
-   Production-grade database infrastructure
-   Monitoring and observability
-   Automated RAG evaluation
-   Enhanced medical information extraction

## 👥 Team Contributions

  Area                  Responsibilities
  --------------------- -----------------------------------------------
  Frontend              React UI, components, chat interface, Library
  Backend               FastAPI APIs and application logic
  RAG                   Retrieval pipeline and context generation
  Agentic AI            Query routing and tool selection
  Vector Database       Pinecone indexing and retrieval
  Authentication        Registration, login and JWT security
  Document Processing   PDF extraction and verification
  AI / Image Analysis   Image processing and analysis
  Testing               API and application testing
  Deployment            GitHub and Render cloud deployment

## ⚠️ Medical Disclaimer

**DrugAssist is an educational and information-retrieval software
system.**

It is **not a medical diagnosis system, treatment recommendation system,
or substitute for professional medical advice**.

Information obtained through DrugAssist should be verified against
current official prescribing information and appropriate healthcare
professionals.

Users should not make medication, dosage, treatment, or other clinical
decisions solely based on an AI-generated response.

## 🎓 Project Purpose

DrugAssist demonstrates the integration of:

-   Generative AI
-   Retrieval-Augmented Generation
-   Agentic AI workflows
-   Vector databases
-   Semantic search
-   Document processing
-   Document provenance and trust verification
-   Authentication
-   REST APIs
-   React frontend development
-   Cloud deployment

The project focuses on building a reliable and source-aware AI
application rather than a simple LLM chatbot.

## ⭐ Project Highlights

``` text
✓ Agentic RAG Architecture
✓ Trusted Medication Document Verification
✓ Document Provenance & Fingerprinting
✓ Semantic Vector Search
✓ Pinecone Vector Database
✓ Groq LLM Inference
✓ FastAPI Backend
✓ React + Vite Frontend
✓ JWT Authentication
✓ PDF Upload
✓ PDF Viewer
✓ Document Library
✓ Image Analysis
✓ Conversational Interface
✓ SQL / Database Integration
✓ Web Retrieval Capability
✓ REST APIs
✓ Swagger / OpenAPI Documentation
✓ GitHub Version Control
✓ Render Cloud Deployment
```

## 📜 License

This project is intended for educational and research purposes.

A suitable open-source license can be added if the project is intended
to be distributed publicly under specific licensing terms.

------------------------------------------------------------------------

### Built with

**React • Vite • FastAPI • Python • Agentic RAG • Pinecone • FastEmbed •
Groq • SQLite • JWT • Render • GitHub**

