# DrugAssist — Frontend Web Application

The interactive, evidence-first web interface for the **DrugAssist Agentic RAG** system. Built with React 18, Vite, and Lucide Icons.

## 🌐 Live Application

- **Production Frontend:** https://drugassist-frontend.onrender.com
- **Production Backend API:** https://drug-assist-agentic-rag.onrender.com
- **API Documentation (Swagger):** https://drug-assist-agentic-rag.onrender.com/docs

## 🚀 Quick Start (Local Development)

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment (Optional)
By default, the frontend connects to `http://localhost:8000`. To point to a custom backend URL, create a `.env` file in the `frontend/` directory:

```env
VITE_API_URL=http://localhost:8000
```

### 3. Run Development Server
```bash
npm run dev
```

The frontend will start at `http://localhost:5173`.

### 4. Build for Production
```bash
npm run build
```
The compiled static assets will be output to `frontend/dist/`.

## 📦 Features Included

- **User Authentication:** Login, Registration, and persistent JWT session management.
- **Agentic Chat Interface:** Multi-turn conversational Q&A with evidence citation badges and reasoning breakdown.
- **Prescribing Document Uploader:** Drag-and-drop PDF ingestion with verified medical source checks.
- **Document Library & In-Browser PDF Viewer:** Real-time page preview with zoom and full-text browsing.
- **Voice Queries:** Audio input with Groq Whisper transcription and hands-free voice asking.
