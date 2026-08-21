# Single-Document RAG Assistant

**Problem Statement option:** Single-Document RAG Assistant (upload one PDF → grounded Q&A with citations and RAGAS logging)

**Live demo:** [https://single-document-rag-assistant.vercel.app](https://single-document-rag-assistant.vercel.app)

**Repository:** [https://github.com/akg78/Single-Document-RAG-Assistant](https://github.com/akg78/Single-Document-RAG-Assistant) (public)

> **Local requirements (read first):** Python **3.11+**, Node.js **20+**, and an **OpenAI-compatible API key** (`backend/.env`). First run downloads **~500 MB+** of embedding/reranker model weights. **Docker Compose is optional** (see [§ Setup → Docker](#3-docker-optional)). For free backend hosting, see [§ Hosted deploy](#hosted-deploy).

Upload one PDF, ask questions by text or voice, and get answers grounded in that document with cited source chunks (page + snippet). Every query logs faithfulness, answer relevancy, and context precision.

---

## Architecture

```text
┌─────────────┐     POST /api/upload      ┌──────────────────────────────────────┐
│  Next.js UI │ ─────────────────────────►│  FastAPI                             │
│  UploadZone │                           │  PyPDFLoader → Recursive splitter    │
│  Chat +     │◄──── chunks + citations ──│  sentence-transformers embeddings    │
│  Sources    │                           │  FAISS IndexFlatIP (persisted)       │
└─────────────┘     POST /api/query       │                                      │
                                          │  Route / decompose (LCEL)            │
                                          │  Retrieve top-k                      │
                                          │  Cross-encoder re-rank               │
                                          │  Prompt → LLM (grounded answer)      │
                                          │  RAGAS metrics → JSONL log           │
                                          └──────────────────────────────────────┘
```

**Pipeline stages (explicit):**

1. **Ingest** — PDF pages → ~700-char chunks (~14% overlap) with `filename`, `page`, `chunk_index`
2. **Embed** — `all-MiniLM-L6-v2` (local, no API key)
3. **Index** — FAISS `IndexFlatIP` on L2-normalized vectors; written under `backend/data/faiss_index/`
4. **Route** — classify `single_fact` | `multi_part` | `summarization`; decompose multi-part into sub-questions
5. **Retrieve** — `query_index(question, k)` per sub-question; merge unique chunks
6. **Re-rank** — `ms-marco-MiniLM-L-6-v2` cross-encoder; pre/post order logged
7. **Generate** — LCEL `prompt | ChatOpenAI | StrOutputParser`; refuse when not in context
8. **Evaluate** — faithfulness / answer relevancy / context precision → `ragas_metrics.jsonl`

---

## Tech stack

| Layer | Choice |
| --- | --- |
| Frontend | Next.js 14 (App Router), TypeScript |
| Backend | FastAPI, Uvicorn |
| Orchestration | LangChain LCEL |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` |
| Vector store | FAISS (`faiss-cpu`, IndexFlatIP) |
| Re-ranking | Cross-encoder `ms-marco-MiniLM-L-6-v2` |
| LLM | OpenAI-compatible chat model (`gpt-4o-mini` by default) |
| Evaluation | RAGAS (+ heuristic fallback if no API key) |
| PDF | PyPDFLoader (`pypdf`) |
| Containers | Docker Compose |

---

## Repository layout

Matches the reference monorepo:

```text
backend/
  app/
    main.py, config.py, models.py
    routes/   upload, query, suggestions, topics, tts, evaluate
    services/ document_processor, embeddings, rag_pipeline, reranker, evaluator
    utils/    retry.py
  tests/, scripts/run_eval.py, requirements.txt, Dockerfile, .env.example
frontend/
  src/app/, components/, hooks/, lib/, types/
  .env.local.example
docker-compose.yml
README.md
```

---

## Setup (local)

### Prerequisites

- Python **3.11+** (verified on 3.14 with the pinned wheels in `requirements.txt`)
- Node.js 20+
- An OpenAI API key (generation + full RAGAS). Embeddings/FAISS/re-ranking work offline.

### 1. Backend

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # or: cp .env.example .env
# Edit .env and set OPENAI_API_KEY=...
```

Start the API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Check health:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

### 2. Frontend

```bash
cd frontend
copy .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Upload a PDF and ask a question — cited sources appear under each answer.

### 3. Docker (optional)

```bash
# Ensure backend/.env has OPENAI_API_KEY
docker compose up --build
```

- API: http://localhost:8000/health  
- UI: http://localhost:3000  

---

## API reference

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Liveness — returns `{ "status": "ok" }` |
| `POST` | `/api/upload` | multipart `file` (PDF) → chunk + embed + FAISS |
| `POST` | `/api/query` | `{ "question", "document_id?" }` → answer, sources, route, rerank, ragas |
| `GET` | `/api/document` | Active document status |
| `POST` | `/api/suggestions` | Suggested follow-up questions |
| `POST` | `/api/topics` | Coarse topic list from chunks |
| `POST` | `/api/tts` | Optional server WAV TTS (501 if unavailable) |
| `POST` | `/api/evaluate` | Score a `{ question, answer, contexts }` sample |

### Example: query response shape

```json
{
  "answer": "… grounded text (p. 3) …",
  "sources": [
    { "id": "…-4", "page": 3, "chunk_index": 4, "snippet": "…", "score": 0.82 }
  ],
  "route": {
    "query_type": "multi_part",
    "sub_questions": ["What is X?", "How does X compare to Y?"]
  },
  "rerank": {
    "pre_rerank": [ /* FAISS order */ ],
    "post_rerank": [ /* cross-encoder order */ ]
  },
  "ragas": {
    "faithfulness": 0.74,
    "answer_relevancy": 0.81,
    "context_precision": 0.69
  }
}
```

---

## Re-ranking before / after

Cross-encoder scores replace FAISS order before generation. Backend logs both orderings (`PRE-RERANK` / `POST-RERANK`). The query payload also returns `rerank.pre_rerank` and `rerank.post_rerank` for screenshots.

**Example pattern (illustrative — your PDF will differ):**

| Rank | Before (FAISS) | After (cross-encoder) |
| --- | --- | --- |
| 1 | chunk-12 (p. 8) — tangential keyword hit | chunk-3 (p. 2) — direct definition |
| 2 | chunk-3 (p. 2) | chunk-7 (p. 4) |
| 3 | chunk-7 (p. 4) | chunk-12 (p. 8) |

To reproduce: upload your PDF, ask a question where lexical overlap misleads FAISS, then inspect server logs or the `rerank` field in the JSON response.

---

## RAGAS evaluation

- **Per query:** `/api/query` computes metrics and appends a line to `backend/data/eval_logs/ragas_metrics.jsonl`.
- **Batch:** after indexing a document:

```bash
cd backend
.\.venv\Scripts\Activate.ps1
python -m scripts.run_eval
```

Edit `EVAL_SET` in `scripts/run_eval.py` with 8–15 question / expected-answer pairs tailored to your demo PDF. Scores should be **plausible and varied** (not all `1.0`). With `OPENAI_API_KEY` set and RAGAS importable, full RAGAS judges run; if the RAGAS package cannot load (dependency mismatch), the same three metric names are still logged via a documented heuristic so evaluation never silently skips.

---

## Checklist (acceptance)

| Criterion | How to verify |
| --- | --- |
| Retrieval changes with questions | Same PDF, two different questions → different `sources` |
| Identical query → identical top-k | Call `query_index` twice; FAISS scores match |
| Re-rank changes order | Compare `rerank.pre_rerank[0].id` vs `post_rerank[0].id` |
| Grounded vs OOD | In-doc fact answered; “capital of Mars” → not in document |
| Multi-part routing | “What is X and how does it compare to Y?” → `multi_part` + ≥2 sub-questions |
| Citations verifiable | Open PDF to cited `page`; snippet appears on that page |
| RAGAS logged | New lines in `ragas_metrics.jsonl` after each query |
| `/health` | HTTP 200 `{ "status": "ok" }` |

---

## Hosted deploy

| Component | URL / host |
| --- | --- |
| **Frontend** | [https://single-document-rag-assistant.vercel.app](https://single-document-rag-assistant.vercel.app) (Vercel) |
| **Backend** | FastAPI + ML stack — deploy via [Oracle Cloud free VM](deploy/oracle/README.md) (recommended, $0) or Render Standard |

**Before submission:** open the live URL in an **incognito window**, upload a PDF, ask a question, and confirm cited sources appear.

### Connect frontend to backend

1. Deploy the backend and note its **HTTPS** public URL (plain `http://` is blocked by the browser from the Vercel site).
2. In [Vercel → Environment Variables](https://vercel.com/akg78s-projects/single-document-rag-assistant/settings/environment-variables), set:
   - `NEXT_PUBLIC_API_URL` = your backend HTTPS URL (no trailing slash)
3. Redeploy the frontend.
4. Set backend `CORS_ORIGINS` to include `https://single-document-rag-assistant.vercel.app`.

**Quick local demo tunnel (Windows/macOS/Linux):** while the backend runs on port 8000, use Cloudflare quick tunnel — see `deploy/oracle/tunnel.sh` or run `cloudflared tunnel --url http://127.0.0.1:8000` and paste the `https://*.trycloudflare.com` URL into Vercel.

---

## Development notes

- First upload downloads embedding + cross-encoder weights (one-time; needs network).
- Index persists under `backend/data/faiss_index/<document_id>/` and is restored on API restart.
- Without `OPENAI_API_KEY`, upload/retrieve/rerank still work; answers run in offline preview mode.
- Voice input uses the browser Web Speech API; “Read aloud” uses `speechSynthesis`.

---

## License

Course / educational project — adapt freely for your Phase-1 submission.
