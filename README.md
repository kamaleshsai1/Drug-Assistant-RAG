# DrugAssist — Evidence-First Prescribing Information RAG Engine

A grounded Retrieval-Augmented Generation (RAG) system engineered for high-precision queries over pharmaceutical prescribing documentation and drug monographs. DrugAssist extracts and indexes official manufacturer package inserts, parses standardized regulatory sections (Indications, Dosages, Contraindications, Boxed Warnings), and produces cited answers with verifiable page references.

---

## Live Deployments (Render Cloud)

- **Frontend Web Application**: [https://drugassist-frontend.onrender.com](https://drugassist-frontend.onrender.com)
- **Backend REST API**: [https://drugassist-backend.onrender.com](https://drugassist-backend.onrender.com)
- **API Health Check**: [https://drugassist-backend.onrender.com/health](https://drugassist-backend.onrender.com/health)

---

## Technical Overview

General-purpose language models often produce hallucinations or conflate dosages when answering clinical questions. DrugAssist mitigates this by restricting answers to retrieved document segments with deterministic citation enforcement. Every claim is mapped to verified manufacturer literature with bracketed page and section citations (`[Source 1, Page 4]`).

### Key Capabilities

- **Strict Evidence Grounding**: Answers are synthesized exclusively from indexed prescribing information chunks. When literature does not contain the answer, the model explicitly declares insufficient evidence.
- **Hierarchical Regulatory Parsing**: Ingestion pipeline automatically identifies standardized labeling structures (Sections 1 through 17: Indications & Usage, Dosage & Administration, Contraindications, Warnings & Precautions, Adverse Reactions, Drug Interactions).
- **Hybrid Real-Time Voice Input**: Dual-mode speech interface utilizing the native browser Web Speech API for zero-latency live dictation, with automated fallback to Groq Whisper (`whisper-large-v3`) via `POST /voice-ask`.
- **Active Document Targeting**: Query across the entire indexed pharmaceutical database or constrain search to an active PDF document selected from the Library.
- **Multimodal Visual Inspection**: Ingests drug packaging and label imagery to provide contextual cross-referencing alongside textual monographs.
- **Session Continuity & Memory**: Persistent conversation threads, document catalog, and user settings backed by SQLite with foreign key integrity.

---

## Architecture

```
                                  +---------------------------------------+
                                  |         React 18 + Vite Frontend      |
                                  |  (Web Speech API / Clinical CSS / UI) |
                                  +-------------------+-------------------+
                                                      |
                                           REST API / JWT Bearer
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |         FastAPI Application Server    |
                                  |           (Python 3.10+ Backend)      |
                                  +----+--------------------+--------+----+
                                       |                    |        |
             +-------------------------+                    |        +-----------------------+
             v                                              v                                v
+--------------------------+               +--------------------------+    +--------------------------+
|      FastEmbed / BAAI     |               |      Pinecone Vector DB  |    |     Groq LLM Engine      |
|    bge-small-en-v1.5     |               |  (Cosine Index / Chunks) |    | (LLaMA / GPT-OSS Models) |
| (Dense 384d Embeddings)  |               +--------------------------+    +--------------------------+
+--------------------------+                                |
             |                                              |
             +----------------------+-----------------------+
                                    v
                       +--------------------------+
                       |      SQLite Store        |
                       |  (Users, Chats, Library) |
                       +--------------------------+
```

---

## Repository Structure

```
DRUG_RAG/
├── backend/
│   ├── database/
│   │   └── database.py          # SQLite schema (users, chats, messages, documents)
│   ├── uploads/
│   │   ├── pdfs/                # Stored prescribing monographs
│   │   └── images/              # Stored label & package images
│   ├── auth.py                  # Bcrypt hashing & PyJWT token handling
│   ├── embeddings.py            # FastEmbed embedding generator
│   ├── main.py                  # FastAPI route controllers & middleware
│   ├── pdf_processor.py         # Standardized section & chunk parser
│   ├── pinecone_db.py           # Pinecone index upsert & namespace management
│   ├── rag.py                   # Retrieval pipeline, prompt synthesis, citations
│   └── requirements.txt         # Backend Python dependencies
├── frontend/
│   ├── public/
│   │   └── favicon.svg          # Clinical vector mark
│   ├── src/
│   │   ├── components/
│   │   │   ├── AuthPage.jsx            # Authentication form with password toggles
│   │   │   ├── ChatInput.jsx           # Composer with audio waveform & file attach
│   │   │   ├── ChatWindow.jsx          # Message list container
│   │   │   ├── ConfirmationModal.jsx   # Accessible confirmation dialog
│   │   │   ├── FAQAccordion.jsx        # Expandable reference FAQs
│   │   │   ├── Library.jsx             # Indexed document manager
│   │   │   ├── Message.jsx             # Answer renderer, citation chips, copy button
│   │   │   ├── PrivacyPolicy.jsx       # Privacy modal
│   │   │   ├── Sidebar.jsx             # Conversation history & document quick-access
│   │   │   └── TermsAndConditions.jsx  # Clinical disclaimer & acceptable use
│   │   ├── services/
│   │   │   └── api.js           # Client HTTP services & token injection
│   │   ├── App.css              # Design system tokens, dark mode, print rules
│   │   ├── app.jsx              # Application state coordinator
│   │   └── main.jsx             # React entry point
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## Design System & Interface Standards

The frontend follows strict clinical design standards to prioritize legibility, fast scanning, and accessible contrast:

- **Typography**: Inter / system font stack with strict mathematical type scales. Headings maintain proportional weight without decorative treatments.
- **Palette**: Slate-driven neutral backgrounds (`#0f172a`, `#1e293b`, `#f8fafc`) paired with accessible clinical cyan and teal accents (`#0284c7`, `#0ea5e9`).
- **Interactive Feedback**:
  - Live pulsing red wave (`@keyframes voicePulse`) during microphone capture.
  - One-click answer clipboard copy with transient checkmark validation.
  - 3px responsive reading progress indicator tracking chat scroll depth.
  - Print stylesheet (`@media print`) optimizing Q&A outputs for physical clinical records.
- **No Vibe-Coded Gimmicks**: Free from arbitrary purple gradients, floating emoji reactions, decorative glowing cards, or ungrounded generative slop.

---

## Getting Started

### Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher
- **Pinecone Account**: API key and active index
- **Groq Cloud Account**: API key for fast LLM inference and Whisper transcription

---

### 1. Environment Configuration

Create a `.env` file in the `backend/` directory:

```env
GROQ_API_KEY=your_groq_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=drug-information
DRUGASSIST_JWT_SECRET=your_secure_random_secret_here
YOUTUBE_API_KEY=optional_clinical_video_key
```

---

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate a virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch FastAPI server (runs on http://127.0.0.1:8000)
uvicorn main:app --port 8000 --host 127.0.0.1 --reload
```

---

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite development server (runs on http://localhost:5173)
npm run dev
```

---

## Core API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/register` | Create user account with salted bcrypt password hash |
| `POST` | `/login` | Authenticate user and issue JWT bearer token |
| `POST` | `/chat` | Send question or attach document for grounded RAG query |
| `POST` | `/voice-ask` | Submit audio recording for Groq Whisper transcription and RAG answer |
| `POST` | `/upload-pdf` | Upload and chunk official manufacturer prescribing PDF into Pinecone |
| `GET` | `/documents` | Retrieve catalog of user-indexed drug documents |
| `DELETE` | `/documents/{id}` | Purge document record and delete Pinecone vector embeddings |
| `GET` | `/chats` | List conversation threads |
| `GET` | `/chats/{id}` | Fetch chat message history with evidence cards and citation tags |
| `DELETE` | `/chats/{id}` | Delete conversation thread |
| `GET` | `/health` | Service health status check |

---

## Regulatory & Clinical Disclaimer

> **Notice**: DrugAssist is an experimental retrieval and reference software designed for educational, research, and informational lookups. It is **not** an FDA-approved medical device, diagnostic system, or software as a medical device (SaMD). It does not provide medical diagnoses or individualized patient treatment plans. Healthcare professionals must exercise independent clinical judgment and verify dosage recommendations against primary manufacturer package inserts.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
