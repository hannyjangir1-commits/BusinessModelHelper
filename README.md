# AI Business Architect — Version 2.0

> **Transform raw venture ideas into comprehensive, source-backed, and executable business blueprints.**

AI Business Architect is an enterprise-grade, full-stack AI platform engineered with a **Python-first architecture** and a modern **React 19 + TypeScript** frontend. It enables startup founders, solo entrepreneurs, and product leaders to validate venture assumptions, perform source-attributed market intelligence, generate phased 30-60-90 day execution roadmaps, and iteratively refine their strategy through a controlled AI Copilot.

---

## 1. Product Overview & Version Architecture

### Version 1 Capabilities (Preserved & Maintained)
- **Guided Business Intake Wizard**: Multi-step intake capturing venture problem, customer profile, industry, budget tiers, team structure, and constraints with local draft persistence.
- **9-Block Business Model Canvas (BMC)**: Visual 9-block matrix covering Customer Segments, Value Propositions, Channels, Customer Relationships, Revenue Streams, Key Resources, Key Activities, Key Partnerships, and Cost Structure. Supports block-level inline editing, version comparison, and regeneration.
- **Technology Stack Recommendation**: Domain-tailored recommendations spanning Frontend, Backend, Database, Infrastructure/Hosting, and Third-Party Services with trade-off matrices, cost brackets, and security considerations.
- **Blueprint Versioning & Audit History**: Full audit trail recording prompt versions, latencies, token consumption, and model names. Failed generation runs never overwrite existing successful blueprints.
- **Enterprise PDF Export**: Multi-page executive PDF report generation built with pure Python ReportLab.
- **Secure Authentication & Account Lifecycle**: Argon2id password hashing, HTTP-only session cookies with CSRF defense, sliding-window rate limiting, and versioned Terms & Privacy Policy acceptance.

### Version 2 Capabilities (Active Integrated Modules)
1. **AI Business Idea Validator**:
   - Evaluates Problem–Solution fit, Target Customer clarity, and Value Proposition differentiation.
   - Comprehensive SWOT analysis (Strengths, Weaknesses, Opportunities, Threats) and categorized business risk matrix (Customer, Market, Tech, Regulatory, Financial).
   - Generates actionable lean validation experiments with explicit hypotheses, protocols, and success metrics.
   - Formulates neutral, non-leading customer interview scripts focusing on past behavior rather than hypothetical validation.
2. **Market and Competitor Research**:
   - Live external search integration backed by a clean provider abstraction (`BaseResearchProvider`, default `DuckDuckGoResearchProvider`).
   - Strict Server-Side Request Forgery (SSRF) defense prohibiting private/loopback/link-local address retrieval.
   - Verified competitor matrix with extracted positioning, pricing, differentiators, and live source attribution citations with access timestamps.
   - Graceful offline fallback: If external search credentials or network connectivity are unavailable, clear error banners are presented without fabricating fake live sources.
3. **AI Execution Roadmap**:
   - Phased 30-day, 60-day, and 90-day execution milestones structured across Research, MVP Prototype, Launch Prep, and Scale phases.
   - Directed Acyclic Graph (DAG) cycle detection using 3-color Depth-First Search (DFS) to prevent circular task dependencies.
   - Persistent task management: Full CRUD operations, priority assignments, deliverables, KPIs, and status updates (`not_started`, `in_progress`, `completed`, `blocked`).
4. **Business Blueprint Copilot**:
   - Context-aware project advisor operating exclusively on the authenticated user's selected venture.
   - Strict separation of concern: Read-only Q&A (`answer_question`) vs. controlled schema modification (`propose_edit`).
   - Controlled before-and-after diff previews with explicit Accept and Reject workflows. Proposals never mutate saved blueprints until explicitly confirmed by the founder.
   - Full version audit logging of accepted revisions.

---

## 2. Technology Stack

### Backend (Python-First)
- **Runtime**: Python 3.12+
- **Web Framework**: FastAPI & Uvicorn (ASGI)
- **Data Validation**: Pydantic v2 & Pydantic Settings
- **ORM & Database Driver**: SQLAlchemy 2.0 & Psycopg 3 (`postgresql+psycopg://`)
- **Database Migrations**: Alembic
- **AI Orchestration**: Official Google GenAI SDK (`google-genai`)
- **Document Generation**: ReportLab (Vector PDF generation)
- **Password Security**: Argon2id via `argon2-cffi`
- **Session Cryptography**: `itsdangerous`
- **Testing**: Pytest & `pytest-asyncio`

### Frontend (Client-Side)
- **Framework**: React 19 with TypeScript
- **Bundler & Dev Server**: Vite
- **Styling**: Tailwind CSS v4
- **Iconography**: Lucide React
- **Architecture**: Single-Page Application (SPA) compiled into static assets served directly by FastAPI under a unified single-origin architecture.

### Deployment & Infrastructure
- **Containerization**: Multi-stage Docker (Stage 1: Node 22 frontend builder, Stage 2: Python 3.12-slim runtime)
- **Hosting Target**: Render Docker Web Service + Render Managed PostgreSQL
- **Orchestration**: Docker Compose for local containerized development

---

## 3. Local Development Setup (Windows / Linux / macOS)

### Prerequisites
- **Python**: Version 3.12 or higher
- **Node.js**: `^20.19.0 || >=22.12.0` (Node 22 LTS recommended) & npm
- **Database**: Local PostgreSQL 15+ instance, Docker Compose (`docker compose up -d db`), or local SQLite for automated tests
- **Windows Launcher**: `start_local.bat` is provided for one-click startup on Windows.

### Step 1: Clone Repository & Configure Environment
```bash
git clone https://github.com/hannyjangir1-commits/BusinessModelHelper.git
cd BusinessModelHelper

# Copy configuration template
cp .env.example .env
```

Edit `.env` to configure your local settings. Never paste real production secrets into version control.

#### Key Environment Variables:
| Variable | Required | Default / Safe Local Value | Description |
|---|---|---|---|
| `APP_ENV` | Yes | `development` | Environment mode (`development`, `production`, `test`). |
| `SECRET_KEY` | Yes | *Generate safe 64-char hex* | Session signing & CSRF token key. Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`. |
| `DATABASE_URL` | Yes | `postgresql+psycopg://postgres:postgres@localhost:5432/ai_business_architect` | SQLAlchemy connection URL (uses Psycopg 3 driver). |
| `GEMINI_API_KEY` | For Live AI | `your_gemini_api_key_here` | Google Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey). |
| `GEMINI_MODEL` | Yes | `gemini-3.5-flash-lite` | Application runtime Gemini model. *(Note: Do not confuse this runtime setting with the Antigravity coding model).* |
| `SESSION_COOKIE_NAME` | No | `aba_session` | Session cookie identifier. |
| `SESSION_HTTPS_ONLY` | Yes | `false` | Set to `false` for local HTTP; must be `true` in production. |
| `SESSION_SAME_SITE` | Yes | `lax` | Cookie CSRF defense policy (`lax`, `strict`). |
| `RESEARCH_PROVIDER` | No | `duckduckgo` | External market research provider with SSRF safeguards. |
| `PUBLIC_SITE_URL` | No | `http://localhost:8000` | Canonical public site URL (leave empty or set to local origin). |

### Step 2: Set Up Python Virtual Environment
```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
# Optional development dependencies:
pip install -r backend/requirements-dev.txt
```

### Step 3: Run Database Migrations
```powershell
# Apply additive database migrations
python -m alembic -c backend/alembic.ini upgrade head
```

### Step 4: Build Frontend Assets
```powershell
cd frontend
npm install
npm run build
cd ..
```

### Step 5: Start Development Server
You can launch the platform in one of two ways:

**Option A — Windows One-Click Launcher:**
```powershell
.\start_local.bat
```
The script validates your Python environment, applies migrations, verifies frontend assets, and launches the server.

**Option B — Direct Command:**
```powershell
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
- Web Application: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Interactive API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check Liveness: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Database Readiness: [http://127.0.0.1:8000/ready](http://127.0.0.1:8000/ready)

---

## 4. Automated Verification & Testing

### Running Backend Pytest Suite
Execute the full backend test suite covering unit formulas, Argon2id security, CSRF protection, SSRF url validation, DAG cycle detection, multi-user isolation, static file traversal protection, concurrency versioning, and rate limiting:
```powershell
# Run from repository root
.\.venv\Scripts\python.exe -m pytest backend/tests -v
```
> **Verified Status (October 12, 2026)**: **71 passed, 1 skipped** (72 total tests). The single skipped test exercises Unix symlink traversal on non-elevated Windows environments.

### Running Frontend Tests
Execute the frontend test suite verifying intake draft persistence and user isolation, debounced search, pagination, workspace concurrency and partial failure isolation, accessible modals, and SEO metadata:
```powershell
cd frontend
npm test
```
> **Verified Status (October 12, 2026)**: **40 passed** (40 total tests).

### Running Frontend Production Build & Typecheck
```powershell
cd frontend
npm run build
# Executes: tsc -b && vite build
```
> **Verified Status (October 12, 2026)**: TypeScript strict compilation (`tsc -b`) and Vite production bundle passed with 0 errors.

### Running AI Quality & Schema Evaluation Suite
Tests 5 startup archetypes (EdTech, CleanTech, Creator Economy, Telehealth, B2B SaaS) across all structured AI pipelines:
```powershell
# Run evaluation suite using deterministic mock generator:
.\.venv\Scripts\python.exe backend/evaluations/run_evaluations.py --mock

# Run evaluation suite using live Gemini API (requires GEMINI_API_KEY):
.\.venv\Scripts\python.exe backend/evaluations/run_evaluations.py
```
Output results are recorded in `backend/evaluations/evaluation_report.json`.

---

## 5. Docker & Production Deployment (Render)

### Production Dockerfile
The repository contains a hardened, multi-stage `Dockerfile`:
1. **Builder Stage**: `node:22-alpine` installs dependencies and runs `npm run build`.
2. **Runtime Stage**: `python:3.12-slim` installs minimal OS libraries and Python packages, copies compiled SPA static assets to `/app/static`, and runs as a dedicated non-root user (`appuser:appgroup`, UID 10001) with least-privilege file permissions (755).
3. **Container Entrypoint**: Web startup is decoupled from database migrations (`CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]`).

### Deployment to Render
The application is pre-configured via `render.yaml` for a unified Render deployment:
- **1 Render Docker Web Service**: Builds from root `Dockerfile` on the `Starter` plan.
- **Readiness Probing**: Health check path `/ready` verifies both web service and PostgreSQL database readiness with a bounded 3-second query timeout.
- **Serialized Migrations**: Uses Render's documented `preDeployCommand: alembic upgrade head` to execute migrations once in an isolated ephemeral container before routing traffic to new container instances.
- **1 Render PostgreSQL Database**: Managed PostgreSQL database.
- **Environment Variables**:
  - `APP_ENV=production`
  - `SECRET_KEY` (Auto-generated by Render)
  - `DATABASE_URL` (Bound from `ai-business-architect-db.connectionString`)
  - `GEMINI_API_KEY` (Set securely in Render Dashboard)
  - `GEMINI_MODEL=gemini-3.5-flash-lite`
  - `SESSION_HTTPS_ONLY=true`
  - `SESSION_SAME_SITE=lax`

### Rolling Deploys & Expand/Contract Migrations
During a Render rolling deployment, incoming requests are handled concurrently by both existing (old code) and newly provisioning (new code) container replicas. To prevent deployment failures and service interruptions, database schema modifications must follow the **Expand/Contract** pattern:
1. **Expand**: Add columns as nullable or with defaults, and add non-blocking indexes. Never drop or rename active columns in an initial deploy.
2. **Deploy Code**: Deploy the new application version. Both old and new application instances function correctly against the expanded database.
3. **Contract**: Once the rollout is complete and all old container replicas are terminated, execute a subsequent migration to prune deprecated columns or enforce stricter constraints.

> **Downtime Note**: Unconditional "zero downtime" is not guaranteed automatically. Smooth rolling deploys require backward-compatible expand/contract schema evolution, bounded query timeouts, and proper connection pool recycling.

### CI Pipeline & Branch Protection
A GitHub Actions CI workflow is configured in `.github/workflows/ci.yml` verifying backend pytest suites, frontend linting/testing/building, and production Docker builds.

To enforce that code cannot be merged without passing CI checks:
1. Navigate to repository **Settings** → **Branches** → **Add branch protection rule**.
2. Set pattern to `main`.
3. Check **Require a pull request before merging**.
4. Check **Require status checks to pass before merging** and select:
   - `Backend Tests (Pytest)`
   - `Frontend Lint, Test & Build`
   - `Docker Production Image Build`
5. Check **Require branches to be up to date before merging**.
6. Check **Do not allow bypassing the above settings**.

---

## 6. Security & Governance Safeguards

- **No Silent Mock AI Fallback in Production**: When `APP_ENV=production`, missing or invalid `GEMINI_API_KEY` configurations raise explicit, actionable errors rather than masquerading fake responses as authentic AI.
- **Server-Side Request Forgery (SSRF) Guard**: The market intelligence module validates outbound research URLs against private IPv4/IPv6 ranges (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, link-local, loopback, multicast) before retrieval.
- **Cross-User Data Isolation**: Every endpoint accessing projects, blueprints, roadmap tasks, or revision records strictly enforces owner ID verification against the active session.
- **Non-Destructive Database Evolution**: Version 2 schema updates are strictly additive; Version 1 accounts, projects, and canvases remain fully intact.

---

## 7. Disclaimers & Intended Use

AI Business Architect outputs are intended for entrepreneurial planning and conceptual software architecture. They do not replace certified legal, accounting, investment, or engineering advice.
