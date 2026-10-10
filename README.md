# AI Business Architect

> **Turn your business idea into an actionable blueprint.**

AI Business Architect is a complete, production-oriented web platform built with a **Python-first architecture** and a modern **React 19 + TypeScript** frontend. It enables solo founders, student entrepreneurs, and engineering teams to transform raw startup concepts into rigorous **9-block Business Model Canvases** and pragmatic **technology stack recommendations**, backed by real AI generation, version history, inline editing, and publication-grade PDF exports.

---

## 1. Problem Statement & Mission

Starting a new venture is fraught with ambiguity. Founders often struggle to:
1. Structure their business model across critical dimensions (channels, value propositions, unit economics).
2. Choose a pragmatic technology stack that matches their actual team capabilities and budget constraints rather than over-engineering prematurely.
3. Validate underlying assumptions before investing significant time and capital.

AI Business Architect solves this by orchestrating structured, domain-grounded business modelling and architectural recommendations via Google Gemini, validated through strict Pydantic schemas and deterministic business rules.

---

## 2. Key Features

- **Public Landing & Marketing Pages**: Clean SaaS landing page, interactive canvas preview, feature deep-dives, how-it-works workflow, FAQ, and legal links.
- **Genuine Authentication & Security**: Argon2id password hashing, HTTP-only session cookies with CSRF protection, and sliding-window rate limiting.
- **Mandatory Legal Tracking**: Explicit versioned consent tracking for Terms and Conditions and Privacy Policy upon registration.
- **Guided Business Intake Wizard**: 4-step wizard capturing venture identity, market demographics, budget tiers, and technical constraints, with local draft auto-saving.
- **Module 1: 9-Block Business Model Canvas**:
  - Covers Customer Segments, Value Propositions, Channels, Customer Relationships, Revenue Streams, Key Resources, Key Activities, Key Partnerships, and Cost Structure.
  - Generates summaries, actionable recommendations, assumptions, risks, and validation experiments.
  - Full block-level inline editing, version comparison, and regeneration.
- **Module 2: Technology Stack Recommendation**:
  - Covers Frontend, Backend, Database, Hosting & Infrastructure, and Third-Party Services.
  - Transparent cost estimates, trade-offs, alternatives, scalability milestones, and security safeguards.
- **Full Version History & Audit Logging**: Every generation attempt is audited with model names, prompt versions, latency, and token consumption. Previous successful blueprints are preserved when regenerating or if upstream failures occur.
- **Publication-Ready PDF Export**: Generates multi-page PDF executive blueprints on the fly using ReportLab in Python.
- **User Profile & Account Lifecycle**: Self-service profile updates, currency preferences, password change, and permanent account deletion with cascading cleanup.
- **Unified Single-Origin Docker Container**: Production multi-stage Docker build where the React frontend is compiled and served directly from FastAPI, perfectly tailored for Render.

---

## 3. Technology Stack

### Backend (Python-First)
- **Runtime**: Python 3.12
- **Framework**: FastAPI & Uvicorn
- **Validation**: Pydantic v2 & Pydantic Settings
- **ORM & Database**: SQLAlchemy 2.0 & Psycopg 3 (PostgreSQL)
- **Migrations**: Alembic
- **AI Integration**: Official Google GenAI SDK (`google-genai` / `google-generativeai`)
- **PDF Generation**: ReportLab
- **Password Hashing**: Argon2id (`argon2-cffi`)
- **Cryptographic Sessions**: `itsdangerous`
- **Testing**: Pytest & FastAPI TestClient

### Frontend
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS v4
- **Iconography**: Lucide React

### Infrastructure & Deployment
- **Containerization**: Multi-stage Docker
- **Local Dev Orchestration**: Docker Compose
- **Production Hosting**: Render Docker Web Service + Render Managed PostgreSQL

---

## 4. Repository Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/             # REST endpoints (auth, projects, bmc, tech, exports, etc.)
│   │   ├── core/            # Security, sessions, rate limiting, exceptions
│   │   ├── models/          # SQLAlchemy models (User, Project, Blueprint, etc.)
│   │   ├── schemas/         # Pydantic v2 schemas
│   │   ├── services/
│   │   │   ├── ai/          # Centralized Gemini client, prompts, validation, rules
│   │   │   └── pdf_service.py # ReportLab PDF generator
│   │   ├── config.py        # Pydantic Settings v2
│   │   ├── database.py      # SQLAlchemy engine & session factory
│   │   └── main.py          # FastAPI application & SPA static server
│   ├── migrations/          # Alembic migration scripts
│   ├── tests/               # Pytest test suite (unit, API, security, AI pipeline)
│   ├── evaluations/         # AI benchmark dataset & evaluation runner
│   ├── alembic.ini
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # UI component library & Layout
│   │   ├── context/         # AuthContext
│   │   ├── pages/           # Landing, Auth, Dashboard, Intake, Workspace, Legal
│   │   ├── services/api.ts  # Typed API client
│   │   ├── types/           # TypeScript interfaces
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── docs/                    # Architecture, API, DB, Security, Evaluation, Render docs
├── Dockerfile               # Multi-stage production container build
├── docker-compose.yml       # Local development multi-container orchestration
├── render.yaml              # Render infrastructure specification
└── .env.example             # Safe environment variable configuration template
```

---

## 5. Local Setup & Development

### Prerequisites
- Python 3.12+
- Node.js 20+ & npm
- PostgreSQL (or SQLite for testing)

### Step 1: Clone Repository & Create Environment Configuration
```bash
git clone https://github.com/hannyjangir1-commits/BusinessModelHelper.git
cd BusinessModelHelper

# Copy configuration template
cp .env.example .env
```

Edit `.env` to configure your database connection and `GEMINI_API_KEY`.

### Step 2: Set Up Python Backend
```bash
# Create and activate virtual environment
python -m venv .venv

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### Step 3: Run Database Migrations
```bash
alembic upgrade head
```

### Step 4: Set Up and Build Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```

### Step 5: Start the Development Server
```bash
# Run FastAPI server
uvicorn app.main:app --app-dir backend --reload --port 8000
```
- Open [http://localhost:8000](http://localhost:8000) to view the application.
- Open [http://localhost:8000/docs](http://localhost:8000/docs) to explore OpenAPI documentation.

---

## 6. Running Tests & AI Evaluations

### Run Pytest Test Suite:
```bash
# Set PYTHONPATH to backend
export PYTHONPATH="backend"  # Windows PowerShell: $env:PYTHONPATH="backend"

# Run automated tests
pytest -v backend/tests
```

### Run AI Quality Evaluation Suite:
```bash
python backend/evaluations/run_evaluations.py
```
This tests 5 varied startup archetypes and generates an evaluation report in `backend/evaluations/evaluation_report.json`.

---

## 7. Docker & Local Container Execution

### Build Production Docker Image:
```bash
docker build -t ai-business-architect:latest .
```

### Run Container Locally:
```bash
docker run -p 8000:8000 \
  -e SECRET_KEY="your-secret-key-32-chars-minimum" \
  -e GEMINI_API_KEY="your-gemini-api-key" \
  -e DATABASE_URL="postgresql+psycopg://user:pass@host:5432/dbname" \
  ai-business-architect:latest
```

### Run with Docker Compose:
```bash
docker compose up --build
```

---

## 8. Deployment to Render

See [docs/DEPLOYMENT_RENDER.md](file:///d:/TE%20-%20SEM%285%29/businessplanner/BusinessModelHelper/docs/DEPLOYMENT_RENDER.md) for full deployment instructions.

1. Connect your GitHub repository on Render.
2. Create a Render Managed PostgreSQL database.
3. Create a Docker Web Service referencing `./Dockerfile`.
4. Add environment variables (`APP_ENV=production`, `SECRET_KEY`, `DATABASE_URL`, `GEMINI_API_KEY`, `SESSION_HTTPS_ONLY=true`).
5. Open the Web Service Shell and apply migrations: `alembic upgrade head`.

---

## 9. Legal & Advisory Notice

AI Business Architect outputs are intended for preliminary venture exploration, conceptual ideation, and software architectural planning. They do not constitute certified legal, financial, tax, accounting, or professional engineering counsel. All vendor pricing and regulatory requirements must be independently verified.

---

## 10. License

This project is licensed under the MIT License.
