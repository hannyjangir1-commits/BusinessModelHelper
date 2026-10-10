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
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model identifier |
| `SESSION_HTTPS_ONLY` | `true` | Enforces Secure flag on session cookies |
| `SESSION_SAME_SITE` | `lax` | Cookie CSRF policy |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

5. Configure **Health Check Path**:
   - Set **Health Check Path** to `/health`.
6. Click **Create Web Service**.

---

### Step 3.3: Apply Database Migrations on Render
Render builds the Docker container (building the frontend and packaging the backend) and spins up the instance.

To run initial database migrations:
1. In the Web Service dashboard, navigate to the **Shell** tab.
2. Run the migration command:
   ```bash
   alembic upgrade head
   ```
3. You will see:
   ```
   INFO  [alembic.runtime.migration] Running upgrade  -> 51b1e8b864ff, initial_schema
   ```

---

## 4. Verification Checklist
Once deployed:
1. Visit your public Render URL: `https://ai-business-architect.onrender.com`.
2. Confirm the landing page renders with responsive styling.
3. Test `/health`: verify `status: "healthy"`.
4. Test `/ready`: verify `database: "connected"`.
5. Register a new user account, accepting the Terms and Privacy Policy.
6. Create a project and generate both the Business Model Canvas and Technology Stack.
7. Click **Export PDF Blueprint** and verify the downloaded document.
