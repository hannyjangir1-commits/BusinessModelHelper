# AI Business Architect — Render Production Deployment Guide

This guide details the step-by-step procedure for deploying the **AI Business Architect** platform to Render using a Docker-based Web Service and Render PostgreSQL.

---

## 1. Architecture on Render

```
[ User Browser ]
       |
       | HTTPS
       v
[ Render Web Service (Docker) ]
   ├── React 19 Frontend (Served from /static)
   ├── FastAPI Backend (Python 3.12)
   ├── ReportLab PDF Engine
   └── Gemini AI Client
       |
       +---> [ Render Managed PostgreSQL ]
```

---

## 2. Prerequisites
1. A [Render Account](https://render.com).
2. A GitHub repository containing this codebase.
3. A Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/app/apikey).

---

## 3. Step-by-Step Deployment Instructions

### Step 3.1: Create Render PostgreSQL Database
1. Open the [Render Dashboard](https://dashboard.render.com).
2. Click **New +** → **PostgreSQL**.
3. Configure the database parameters:
   - **Name**: `ai-business-architect-db`
   - **Database**: `ai_business_architect`
   - **User**: `ai_architect_user`
   - **Region**: Choose a region (e.g. `Oregon (US West)`). *Ensure your web service shares this region.*
   - **Plan**: `Starter` (or `Free` for initial exploration).
4. Click **Create Database**.
5. Once provisioned, note the **Internal Connection String** (format: `postgres://ai_architect_user:password@dpg-...:5432/ai_business_architect`).

---

### Step 3.2: Create Render Docker Web Service
1. In the Render Dashboard, click **New +** → **Web Service**.
2. Select your connected GitHub repository: `BusinessModelHelper`.
3. Configure service settings:
   - **Name**: `ai-business-architect`
   - **Region**: Same region selected for PostgreSQL.
   - **Runtime**: **Docker**.
   - **Dockerfile Path**: `./Dockerfile`.
   - **Plan**: `Starter` (recommended for responsive inference).
4. Configure **Environment Variables**:

| Variable Name | Example Value / Source | Description |
|---|---|---|
| `APP_ENV` | `production` | Enables production security modes |
| `DATABASE_URL` | *Use Render Internal Connection String* | Automatically converted to `postgresql+psycopg://` |
| `SECRET_KEY` | *Click 'Generate' in Render dashboard* | 64-character cryptographic hex secret |
| `GEMINI_API_KEY` | `AIzaSy...` | Your Google Gemini API Key |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Gemini model identifier |
| `SESSION_HTTPS_ONLY` | `true` | Enforces Secure flag on session cookies |
| `SESSION_SAME_SITE` | `lax` | Cookie CSRF policy |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

5. Configure **Health Check Path**:
   - Set **Health Check Path** to `/ready` (verifies both FastAPI liveness and PostgreSQL database connectivity with a bounded 3s timeout).
6. Click **Create Web Service**.

---

### Step 3.3: Database Migrations & Rolling Deployment Architecture

#### Automated Migrations (Starter Plan via `render.yaml`)
When deployed via `render.yaml` on the `Starter` plan, Render automatically executes:
```yaml
preDeployCommand: alembic upgrade head
```
- **Serialized Execution**: Runs once in an ephemeral container *before* new web instances start and before traffic is routed.
- **Decoupled from Web Startup**: The web container `Dockerfile` does **not** run migrations on startup (`CMD ["sh", "-c", "exec uvicorn app.main:app ..."]`). This prevents multi-replica race conditions and avoids repeated migration checks when a web container restarts.

#### Manual / Free Tier Single-Run Migration Procedure
If deploying manually or on Render's **Free Tier** (where `preDeployCommand` is unsupported by Render):
1. Never put `alembic upgrade head` in the container `CMD` or startup script.
2. In the Render Dashboard, go to your Web Service -> **Shell** tab.
3. Run the single-run command manually before rolling out code updates:
   ```bash
   alembic upgrade head
   ```
4. Confirm migration success (`INFO  [alembic.runtime.migration] Running upgrade ...`) before triggering the new build deployment.

#### Backward-Compatible Expand/Contract Strategy for Rolling Deploys
During a Render rolling deployment, incoming requests are handled concurrently by both existing (old code) and newly provisioning (new code) container replicas. Therefore, database schema changes must be backward-compatible:
1. **Phase 1 (Expand)**:
   - Add new columns as `nullable` or with sensible database defaults.
   - Add new tables or non-blocking indexes.
   - Do **not** drop or rename existing columns, and do **not** add restrictive `NOT NULL` constraints to active tables in use by the running code.
2. **Phase 2 (Deploy Code)**:
   - Deploy application code that writes to both old and new structures (or safely reads the new structure with fallbacks).
   - Old code continues to function against the expanded database schema without errors.
3. **Phase 3 (Contract)**:
   - After the new deployment is fully active and all old container replicas are terminated, execute a subsequent migration to remove deprecated columns or enforce stricter constraints.

> **Note on Downtime Claims**: We do not promise unconditional "zero downtime." True zero downtime during rolling deploys requires strictly adhering to the 3-phase expand/contract lifecycle, non-blocking DDL locks, and ensuring connection pools recycle cleanly.

---

## 4. Verification Checklist
Once deployed:
1. Visit your public Render URL: `https://ai-business-architect.onrender.com`.
2. Confirm the landing page renders with responsive styling.
3. Test `/health`: verify `status: "healthy"`.
4. Test `/ready`: verify `status: "ready"` and `database: "connected"`.
5. Register a new user account, accepting the Terms and Privacy Policy.
6. Create a project and generate both the Business Model Canvas and Technology Stack.
7. Click **Export PDF Blueprint** and verify the downloaded document.

---

## 5. GitHub Branch Protection & CI Configuration
A GitHub Actions CI workflow is provided in `.github/workflows/ci.yml`.

> **Important**: The CI workflow alone does not prevent developers or automated tools from merging or pushing directly to `main`. You must explicitly configure branch protection rules in GitHub:

1. Navigate to your repository on GitHub: `Settings` → `Branches`.
2. Under **Branch protection rules**, click **Add branch protection rule**.
3. Set **Branch name pattern** to `main`.
4. Check **Require a pull request before merging**.
5. Check **Require status checks to pass before merging**.
6. Check **Require branches to be up to date before merging**.
7. In the status checks search box, select:
   - `Backend Tests (Pytest)`
   - `Frontend Lint, Test & Build`
   - `Docker Production Image Build`
8. Check **Do not allow bypassing the above settings** (or enforce for administrators).
9. Click **Save changes**.
