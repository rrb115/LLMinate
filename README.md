# AI-Call Optimizer / De-LLM-ifier

Local-first system that scans codebases for AI API calls, infers intent, scores rule-solvability, proposes safe deterministic refactors, and supports patch review/apply/revert with shadow-run comparisons.

## Tech Stack
- Backend: Python 3.11, FastAPI, Pydantic, SQLAlchemy, SQLite
- Analysis: tree-sitter, Semgrep, heuristic intent inference, scikit-learn-compatible scoring pipeline (heuristic baseline implemented)
- Refactor: LibCST-ready Python planner + jscodeshift codemod scaffold for JS/TS
- Frontend: React + TypeScript (Vite) + Tailwind CSS
- Testing: pytest, Playwright
- Tooling: Docker, Docker Compose, black, isort, mypy, eslint, prettier

## Repository Layout
- `/backend` FastAPI app, scanner, scoring, patch planner, queue worker
- `/frontend` UI for scan/review/patch/shadow workflows
- `/samples` mandatory sample cases used by tests
- `/ci` helper scripts

## Run Locally
```bash
docker-compose up --build
```
- Backend docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Frontend: [http://localhost:5173](http://localhost:5173)

## API Endpoints
- `POST /api/scan`
- `GET /api/status/{scan_id}`
- `GET /api/results/{scan_id}`
- `GET /api/patch/{scan_id}/{candidate_id}`
- `POST /api/apply/{scan_id}/{candidate_id}`
- `POST /api/revert/{scan_id}/{candidate_id}`
- `POST /api/shadow-run/{scan_id}/{candidate_id}`
- `GET /api/metrics`

All `/api/*` endpoints require header:
- `X-Local-Auth: local-dev`

## Safety
- Default mode is suggestion-only.
- Auto-apply is reversible and isolated per candidate branch:
  - `ai-prune/{scan_id}/{candidate_id}`
- Apply endpoint requires `safety_flag=true`.
- Fallback behavior is attached to every candidate.

## Samples
- `samples/python_yes_no`
- `samples/structured_extraction`
- `samples/js_fuzzy`
- `samples/non_replaceable`

## Tests
```bash
cd backend && pytest -q
cd frontend && npm run test:e2e
```

## Notes
- This project does not call any external paid AI APIs.
- Shadow-run uses a local mocked LLM fixture service.
