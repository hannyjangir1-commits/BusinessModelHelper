# AI Business Architect — Architectural Specification

## 1. System Philosophy & Overview

**AI Business Architect** is a production-oriented web platform designed to transform raw business and startup concepts into rigorous, verifiable Business Model Canvases and pragmatic technology-stack recommendations.

### Core Architectural Principles:
1. **Python-First Core**: Business logic, AI pipeline orchestration, deterministic rule evaluations, database persistence, and PDF report generation are implemented entirely in Python 3.12 with FastAPI.
2. **Single-Origin Deployment**: In production, the React + TypeScript frontend is compiled during a multi-stage Docker build and served directly by FastAPI. This eliminates CORS complexities, reduces DNS lookups, and simplifies hosting on Render to a single unified web container.
3. **Defense-in-Depth Security**: Authentication uses Argon2id one-way password hashing, secure server-side session cookies with CSRF token verification, and strict ownership validation on all project resources to prevent Insecure Direct Object References (IDOR).
4. **Deterministic AI Engineering**: Upstream AI outputs are never trusted blindly. Model responses are parsed, validated against strict Pydantic v2 schemas, and evaluated by deterministic business rule validators before database persistence.

---

## 2. High-Level Architecture Diagram

```
[ Web Browser ]
      |
      | HTTPS (Single Public Origin)
      v
+-------------------------------------------------------------------------+
|                  Render Docker Web Service (0.0.0.0:$PORT)              |
|                                                                         |
|  +---------------------------------+  +------------------------------+  |
|  |     Static Assets (/static)     |  |       FastAPI Application     |  |
|  |   - React 19 SPA (Vite build)   |  |   - Correlation ID & Headers |  |
|  |   - Tailwind CSS Assets         |  |   - Exception Handlers       |  |
|  |   - Client-side Router          |  |   - Session & CSRF Auth      |  |
|  +---------------------------------+  +------------------------------+  |
|                                                      |                  |
|          +-------------------------------------------+                  |
|          |                     |                     |                  |
|          v                     v                     v                  |
|   [ Auth & Projects ]   [ AI Engine ]         [ ReportLab PDF ]         |
|   - Argon2id Hasher     - Prompt Versioning   - Multi-page tables       |
|   - IDOR Checks         - Schema Validator    - Dynamic headers/footers |
|   - Sliding Rate Limit  - Business Rules      - Streaming Response      |
|          |                     |                                        |
+----------|---------------------|----------------------------------------+
           |                     |
           v                     v
   [ Render PostgreSQL ]   [ Google Gemini API ]
   - Users & Projects      - gemini-2.5-flash
   - Versioned Blueprints  - Structured JSON
   - Generation Audits     - Bounded Retries
```

---

## 3. Component Breakdown

### 3.1 Backend Application (`backend/app`)
- **`config.py`**: Pydantic Settings v2 configuration management with dynamic normalization for PostgreSQL connection URLs and environment validation.
- **`database.py`**: SQLAlchemy 2.0 connection engine with automatic connection pooling, pre-ping validation, and session lifecycle management.
- **`dependencies.py`**: Dependency injection for database transactions, authenticated user resolution from secure cookies, and CSRF token verification on state-changing operations.
- **`services/ai/`**:
  - `client.py`: Centralized Gemini client with exponential backoff, rate-limit retry logic, latency measurement, and token tracking. Also provides `MockAIClient` for deterministic test suites.
  - `prompts.py`: Versioned prompt templates (`2026-v1.0`) enforcing structured JSON outputs and explicit separation between facts, recommendations, and assumptions.
  - `validation.py`: JSON extraction from LLM responses and Pydantic schema enforcement.
  - `business_rules.py`: Deterministic consistency checks and advisory warnings (budget feasibility, team size compatibility).
  - `generation.py`: End-to-end generation orchestrator managing database transactions, blueprint versioning, and failure logging.
- **`services/pdf_service.py`**: ReportLab publication-grade PDF generator rendering clean executive summaries, the 9-block canvas, full technology stack recommendations, and risk disclosures.

### 3.2 Frontend Application (`frontend/src`)
- **React 19 + TypeScript**: Type-safe component architecture.
- **Tailwind CSS v4**: Coherent SaaS design system with accessible contrast, subtle borders, restrained shadows, and responsive layouts.
- **`services/api.ts`**: Unified API client utilizing relative URLs, automatic cookie transmission, and CSRF header handling.
- **`context/AuthContext.tsx`**: Reactive session state management with automatic background session validation.

---

## 4. Scalability & Operational Evolution

1. **Phase 1 (Initial Launch / 0 - 1,000 Users)**:
   - Single Render Docker Web Service + Render Starter PostgreSQL.
   - Synchronous generation pipeline with 60-second timeouts.
2. **Phase 2 (Growth / 1,000 - 50,000 Users)**:
   - Add database connection pooling (PgBouncer).
   - Horizontal scaling of web containers to multiple instances behind Render's load balancer.
3. **Phase 3 (Enterprise Scale / 50,000+ Users)**:
   - Introduce asynchronous job queues (Celery / ARQ with Redis) for background generation.
   - Offload PDF documents to cloud object storage (AWS S3 / Cloudflare R2).
