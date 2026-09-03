
## Pages

- **Landing (`/`)** — hero pitch, a worked "no evidence found" example
  shown up front (not hidden away), a 3-step "how an answer gets made"
  (retrieve → rerank → answer with sources), link into the Dashboard.
- **Dashboard (`/dashboard`)** — live per-service health strip (quiet dots,
  a banner only if `status: "degraded"`), quick links into the other four
  tools.
- **AI Assistant (`/assistant`)** — the core feature. Chat over
  `POST /chat`; every assistant turn renders as either a normal answer
  card with a clickable source list, or — when `evidence_available:
  false` — a visually distinct dashed amber "No evidence found" card, so
  the honesty the backend enforces can't get smoothed into a generic chat
  bubble. A contextual "thinking" indicator during the multi-second Groq
  call, not a bare spinner. Can attach a location selected on the Map
  Explorer, sent as `latitude`/`longitude`.
- **Map Explorer (`/map`)** — React-Leaflet map centered on Mandi
  Bahauddin. Clicking calls `GET /environment`; the environmental panel
  shows every field (including nulls, labeled "Not available from these
  sources"), a `data_source` disclaimer so nothing reads as a field
  measurement, its own loading skeleton (the live GEE lookup can take a
  couple seconds) separate from the map itself, and an honest empty state
  for `available: false`. "Ask about this location" hands the coordinates
  to the AI Assistant.
- **Tree Species (`/species`, `/species/:id`)** — grid + detail from
  `GET /species` / `GET /species/{id}`. Every nullable field renders "Not
  available in current evidence," never hidden. Detail page distinguishes
  a real 404 ("Species not found") from other errors.
- **Knowledge Sources (`/sources`)** — search box over `POST /retrieve`,
  the "show your work" page — renders the actual documents backing a
  topic, distinct empty states for "haven't searched yet" vs. "no
  matches."
- **About (`/about`)** — static: project description, the evidence-first
  explainer (retrieval → citation-only generation → explicit uncertainty),
  architecture summary, scope, stack.

## Not yet built (frontend)

Document upload/ingestion UI (ingestion is CLI-only), chat history
persistence UI (no API for it yet), feedback/rating UI (no endpoint yet).

## Frontend setup

```bash
cd frontend
npm install
cp .env.example .env    # VITE_API_BASE_URL, defaults to http://localhost:8000/api
npm run dev
```

```bash
npm run build            # production build to dist/
```

---

## Full local run

```bash
# terminal 1
cd backend && uvicorn app.main:app --reload

# terminal 2
cd frontend && npm run dev
```

Then open the frontend, check the Dashboard's health strip reflects real
service status, click a point in Mandi Bahauddin on the Map Explorer, and
ask the AI Assistant a question about it.

## Next phase

Phase 8 (RAG evaluation): eval dataset (30–50 Q/A pairs with expected
sources/topics) and a harness comparing vector-only vs. vector+rerank
retrieval on Recall@K, Precision@K, MRR, and citation correctness.