# AI Business Architect — Version 2.0

> **Transform raw venture ideas into comprehensive, source-backed, and financially grounded business blueprints.**

AI Business Architect is an enterprise-grade, full-stack AI platform engineered with a **Python-first architecture** and a modern **React 19 + TypeScript** frontend. It enables startup founders, solo entrepreneurs, and product leaders to validate venture assumptions, compute deterministic 12-month financial forecasts, perform source-attributed market intelligence, generate phased 30-60-90 day execution roadmaps, and iteratively refine their strategy through a controlled AI Copilot.

---

## 1. Product Overview & Version Architecture

### Version 1 Capabilities (Preserved & Maintained)
- **Guided Business Intake Wizard**: Multi-step intake capturing venture problem, customer profile, industry, budget tiers, team structure, and constraints with local draft persistence.
- **9-Block Business Model Canvas (BMC)**: Visual 9-block matrix covering Customer Segments, Value Propositions, Channels, Customer Relationships, Revenue Streams, Key Resources, Key Activities, Key Partnerships, and Cost Structure. Supports block-level inline editing, version comparison, and regeneration.
- **Technology Stack Recommendation**: Domain-tailored recommendations spanning Frontend, Backend, Database, Infrastructure/Hosting, and Third-Party Services with trade-off matrices, cost brackets, and security considerations.
- **Blueprint Versioning & Audit History**: Full audit trail recording prompt versions, latencies, token consumption, and model names. Failed generation runs never overwrite existing successful blueprints.
- **Enterprise PDF Export**: Multi-page executive PDF report generation built with pure Python ReportLab.
- **Secure Authentication & Account Lifecycle**: Argon2id password hashing, HTTP-only session cookies with CSRF defense, sliding-window rate limiting, and versioned Terms & Privacy Policy acceptance.

### Version 2 Capabilities (New Integrated Modules)
1. **AI Business Idea Validator**:
   - Evaluates Problem–Solution fit, Target Customer clarity, and Value Proposition differentiation.
   - Comprehensive SWOT analysis (Strengths, Weaknesses, Opportunities, Threats) and categorized business risk matrix (Customer, Market, Tech, Regulatory, Financial).
   - Generates actionable lean validation experiments with explicit hypotheses, protocols, and success metrics.
   - Formulates neutral, non-leading customer interview scripts focusing on past behavior rather than hypothetical validation.
2. **Financial Projection Engine (Deterministic Pure Python)**:
   - **Zero AI arithmetic**: Gemini interprets assumptions, but 100% of numerical calculations (revenue, COGS, gross margin, operating profit, net profit, break-even units/revenue, monthly cash burn, and runway) are executed using deterministic Python formulas.
   - Configurable 12-month projections supporting monthly growth rates, fixed/variable costs, payment processing, tax provisions, and initial startup capital.
   - Multi-scenario simulation: Conservative, Expected, and Optimistic cases driven by explicit assumption adjustments.
3. **Market and Competitor Research**:
   - Live external search integration backed by a clean provider abstraction (`BaseResearchProvider`, default `DuckDuckGoResearchProvider`).
   - Strict Server-Side Request Forgery (SSRF) defense prohibiting private/loopback/link-local address retrieval.
   - Verified competitor matrix with extracted positioning, pricing, differentiators, and live source attribution citations with access timestamps.
   - Graceful offline fallback: If external search credentials or network connectivity are unavailable, clear error banners are presented without fabricating fake live sources.
4. **AI Execution Roadmap**:
   - Phased 30-day, 60-day, and 90-day execution milestones structured across Research, MVP Prototype, Launch Prep, and Scale phases.
   - Directed Acyclic Graph (DAG) cycle detection using 3-color Depth-First Search (DFS) to prevent circular task dependencies.
   - Persistent task management: Full CRUD operations, priority assignments, deliverables, KPIs, and status updates (`not_started`, `in_progress`, `completed`, `blocked`).
5. **Business Blueprint Copilot**:
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
- **AI Orchestration**: Official Google GenAI SDK (`google-genai` / `google-generativeai`)
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

## 3. Financial Calculation Formulas & Business Rules

All financial calculations are computed deterministically in `backend/app/services/financial_service.py` to prevent hallucinated numbers:

- **Monthly Sales Volume**:
  $$\text{Units}_t = \text{Initial Units} \times (1 + \text{Monthly Growth Rate})^{t-1}$$
- **Monthly Revenue**:
  $$\text{Revenue}_t = \text{Units}_t \times \text{Selling Price}$$
- **Variable Cost of Goods Sold (COGS)**:
  $$\text{COGS}_t = \text{Units}_t \times \text{Variable Cost Per Unit} + (\text{Revenue}_t \times \text{Payment Processing Rate})$$
- **Gross Profit & Margin**:
  $$\text{Gross Profit}_t = \text{Revenue}_t - \text{COGS}_t$$
  $$\text{Gross Margin} = \frac{\text{Gross Profit}_t}{\text{Revenue}_t} \times 100\%$$
- **Contribution Margin per Unit**:
  $$\text{Contribution Margin} = \text{Selling Price} - \text{Variable Cost Per Unit}$$
- **Break-Even Analysis**:
  $$\text{Break-Even Units} = \lceil \frac{\text{Monthly Fixed Costs}}{\text{Contribution Margin}} \rceil \quad (\text{if Contribution Margin} > 0)$$
  $$\text{Break-Even Revenue} = \text{Break-Even Units} \times \text{Selling Price}$$
  *Note: If Contribution Margin $\le 0$, the business cannot cover variable costs, and break-even is safely marked as undefined with an explanatory warning.*
- **Operating Profit (EBIT)**:
  $$\text{Operating Profit}_t = \text{Gross Profit}_t - \text{Fixed Operating Expenses}_t$$
- **Net Profit**:
  $$\text{Net Profit}_t = \text{Operating Profit}_t - \text{Estimated Taxes}_t$$
- **Cash Flow & Runway**:
  $$\text{Closing Cash}_t = \text{Opening Cash}_t + \text{Net Cash Flow}_t$$
  $$\text{Runway (Months)} = \frac{\text{Closing Cash}}{\text{Average Monthly Burn Rate}}$$

*Disclaimer: Projections are model-based planning estimates and do not constitute certified accounting, investment, or tax advice.*

---

## 4. Local Development Setup (Windows / Linux / macOS)

### Prerequisites
- **Python**: Version 3.12 or higher
- **Node.js**: Version 20 or higher & npm
- **Database**: Local PostgreSQL 15+ instance or Docker Compose

### Step 1: Clone Repository & Configure Environment
```bash
git clone https://github.com/hannyjangir1-commits/BusinessModelHelper.git
cd BusinessModelHelper

# Copy configuration template
cp .env.example .env
```
Edit `.env` and set your credentials:
```ini
APP_ENV=development
SECRET_KEY=generate_a_random_32_byte_hex_string
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/ai_business_architect
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

### Step 2: Set Up Python Virtual Environment
```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

### Step 3: Run Database Migrations
```powershell
# Apply additive Version 1 and Version 2 migrations
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
```powershell
# Run backend server (serving both API and compiled SPA)
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
- Web Application: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Interactive API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check Liveness: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Database Readiness: [http://127.0.0.1:8000/ready](http://127.0.0.1:8000/ready)

---

## 5. Automated Verification & Testing

### Running Backend Pytest Suite
All 32 test cases verify unit formulas, SSRF defenses, DAG cycle checks, AI schema validation, and multi-user isolation:
```powershell
# Run from repository root
.\.venv\Scripts\python.exe -m pytest backend/tests -v
```

### Running Frontend Production Build & Typecheck
```powershell
cd frontend
npm run build
# Executes: tsc -b && vite build
```

### Running AI Quality & Schema Evaluation Suite
Tests 5 diverse startup archetypes (EdTech, CleanTech, Creator Economy, Telehealth, B2B SaaS) across all structured AI pipelines:
```powershell
# Run evaluation suite using deterministic mock generator:
.\.venv\Scripts\python.exe backend/evaluations/run_evaluations.py --mock

# Run evaluation suite using live Gemini API (requires GEMINI_API_KEY):
.\.venv\Scripts\python.exe backend/evaluations/run_evaluations.py
```
Output results are recorded in `backend/evaluations/evaluation_report.json`.

---

## 6. Docker & Production Deployment (Render)

### Production Dockerfile
The repository contains a hardened, multi-stage `Dockerfile`:
1. **Builder Stage**: `node:22-alpine` installs dependencies and runs `npm run build`.
2. **Runtime Stage**: `python:3.12-slim` installs minimal OS libraries and Python packages, copies compiled SPA static assets to `/app/static`, applies Alembic migrations automatically on boot, and runs Uvicorn on dynamic `$PORT`.

### Deployment to Render
The application is pre-configured via `render.yaml` for a unified Render deployment:
- **1 Render Docker Web Service**: Builds from root `Dockerfile`.
- **1 Render PostgreSQL Database**: Managed PostgreSQL database.
- **Environment Variables**:
  - `APP_ENV=production`
  - `SECRET_KEY` (Auto-generated by Render)
  - `DATABASE_URL` (Bound from `ai-business-architect-db.connectionString`)
  - `GEMINI_API_KEY` (Set securely in Render Dashboard)
  - `GEMINI_MODEL=gemini-2.5-flash`
  - `SESSION_HTTPS_ONLY=true`
  - `SESSION_SAME_SITE=lax`

**Zero-Downtime Migration Execution**:
The Docker container entrypoint executes:
```sh
alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```
This guarantees additive migrations are applied before the web service begins listening on `$PORT`.

---

## 7. Security & Governance Safeguards

- **No Silent Mock AI Fallback in Production**: When `APP_ENV=production`, missing or invalid `GEMINI_API_KEY` configurations raise explicit, actionable errors rather than masquerading fake responses as authentic AI.
- **Server-Side Request Forgery (SSRF) Guard**: The market intelligence module validates outbound research URLs against private IPv4/IPv6 ranges (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, link-local, loopback, multicast) before retrieval.
- **Cross-User Data Isolation**: Every endpoint accessing projects, blueprints, financial models, roadmap tasks, or revision records strictly enforces owner ID verification against the active session.
- **Non-Destructive Database Evolution**: Version 2 schema updates are strictly additive; Version 1 accounts, projects, and canvases remain fully intact.

---

## 8. License & Disclaimers

This project is licensed under the MIT License.
AI Business Architect outputs are intended for entrepreneurial planning and conceptual software architecture. They do not replace certified legal, accounting, investment, or engineering advice.
