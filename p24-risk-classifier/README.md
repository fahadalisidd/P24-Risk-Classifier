# P24: Risk Rubric, Classifier & RAG AI Knowledge Advisor

A production-quality risk governance platform featuring **Deterministic Mathematical Classification**, **RAG (Retrieval-Augmented Generation) Policy Knowledge Base**, **AI Risk Advisor (Grok / Ollama / Local NLP)**, and a **Modern Web UI Dashboard**.

---

## 🌟 Key System Capabilities

1. **🎨 Modern Web UI Dashboard (`http://localhost:8000/`)**:
   - **Risk Evaluator Studio**: Interactive dimension selectors, real-time formula calculator ($4 \times 4 \times 4 = 64$), and instant risk assessment card.
   - **RAG Policy Knowledge Base Explorer**: Live semantic search across enterprise standards, SOPs, and historical incident postmortems.
   - **2-Engineer Peer Review Simulator**: Independent scoring with live `AGREEMENT` / `DISAGREEMENT` conflict note logging.
   - **Policy Pins & Overdue Monitor**: Live audit report highlighting pins requiring review.
2. **📚 RAG (Retrieval-Augmented Generation) Knowledge Base**:
   - Dense semantic vector store with cosine similarity retrieval.
   - Automatically retrieves governing policies (`POL-101`, `POL-102`, `POL-103`, `POL-104`, `INC-2025-08`) based on operation context.
   - Grounded AI assessment with explicit policy citations and similarity matching scores.
3. **📐 Deterministic Mathematical Rubric**:
   - $\text{Risk Score} = \text{Scope} \times \text{Reversibility} \times \text{Persistence}$
   - Dynamic payload rules (e.g. `PRODUCTION_IRREVERSIBLE_DELETE` $\rightarrow$ sets min Category 4).
   - Policy Overrides & Pin Registry.
4. **🤖 Multi-Model AI Advisor**:
   - **xAI Grok API** (`GROK_API_KEY`) support.
   - **Local Ollama LLM** (`llama3.2`, `mistral`, `deepseek-r1`) support.
   - **Embedded Semantic NLP Engine** (100% offline, zero external dependencies).

---

## 🚀 How to Run the Project

### 1. Start the Backend & Web Dashboard:
```powershell
cd C:\Users\Admin\.gemini\antigravity\scratch\p24-risk-classifier
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Open the Web UI Dashboard in Browser:
👉 **[http://localhost:8000](http://localhost:8000)** (or `http://localhost:8000/dashboard`)

### 3. Open Interactive Swagger API Docs:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

### 4. Run the Full 54-Test Automated Suite:
```powershell
python -m pytest -v
```

---

## 📡 API Endpoints Overview

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/` or `/dashboard` | **Interactive Web Frontend UI Dashboard** |
| `POST` | `/api/v1/rag/evaluate` | **Full RAG-Augmented Risk Classification & Citation Engine** |
| `POST` | `/api/v1/rag/query` | **Semantic Search in Policy & Postmortem Knowledge Base** |
| `GET` | `/api/v1/rag/documents` | List all indexed policy documents |
| `POST` | `/api/v1/rag/documents` | Ingest new policy or incident runbook into Vector Store |
| `POST` | `/api/v1/risk/evaluate` | Core deterministic classification & obligations check |
| `POST` | `/api/v1/ai/analyze` | AI Model text & justification quality analysis |
| `POST` | `/api/v1/reviews` | Submit independent engineer review score |
| `GET` | `/api/v1/reviews/{operation_id}` | Check 2-engineer agreement/disagreement consensus |
| `GET` | `/api/v1/policies/pins/review-report` | Overdue policy pin audit report |
| `GET` | `/docs` | OpenAPI / Swagger Documentation |
