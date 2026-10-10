# AI Business Architect — API Specification

The AI Business Architect backend exposes a RESTful JSON API prefixed by `/api`. All endpoints use standard HTTP verbs, return consistent response envelopes, and provide OpenAPI 3.0 documentation at `/docs`.

---

## 1. Response Envelope Conventions

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional user-friendly message"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error explanation",
    "details": { ... }
  }
}
```

---

## 2. Authentication & Profile Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/register` | Register new user with legal consent | No |
| `POST` | `/api/auth/login` | Authenticate with username/email & password | No |
| `POST` | `/api/auth/logout` | Invalidate session cookie | Yes |
| `GET` | `/api/auth/me` | Retrieve authenticated user profile | Yes |
| `POST` | `/api/auth/change-password`| Change user password | Yes |
| `GET` | `/api/profile` | Get user profile details | Yes |
| `PATCH` | `/api/profile` | Update display name, bio, currency | Yes |
| `DELETE` | `/api/profile` | Permanently delete account & cascade projects | Yes |

### Register Request Example
`POST /api/auth/register`
```json
{
  "username": "venture_founder",
  "email": "founder@venture.com",
  "password": "StrongPassword123!",
  "confirm_password": "StrongPassword123!",
  "terms_accepted": true,
  "privacy_acknowledged": true
}
```

---

## 3. Project Management Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/projects` | Create a new business project | Yes |
| `GET` | `/api/projects` | List projects (pagination & search) | Yes |
| `GET` | `/api/projects/{id}` | Get single project by ID (IDOR protected) | Yes |
| `PATCH` | `/api/projects/{id}` | Update project details | Yes |
| `DELETE` | `/api/projects/{id}` | Delete project & cascade blueprints | Yes |

### Query Parameters for `GET /api/projects`
- `page` (integer, default: `1`)
- `page_size` (integer, default: `20`)
- `search` (string, optional: matches name, idea, or industry)
- `industry` (string, optional)

---

## 4. AI Business Model Canvas Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/projects/{id}/business-model/generate` | Generate / regenerate 9-block canvas | Yes |
| `GET` | `/api/projects/{id}/business-model` | Get latest (or specified `?version=X`) canvas | Yes |
| `GET` | `/api/projects/{id}/business-model/versions`| List all saved canvas versions | Yes |
| `PATCH` | `/api/projects/{id}/business-model` | Edit and save canvas block modifications | Yes |

---

## 5. AI Technology Stack Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/projects/{id}/technology-stack/generate` | Generate / regenerate technology stack | Yes |
| `GET` | `/api/projects/{id}/technology-stack` | Get latest (or specified `?version=X`) stack | Yes |
| `GET` | `/api/projects/{id}/technology-stack/versions`| List all saved tech stack versions | Yes |
| `PATCH` | `/api/projects/{id}/technology-stack` | Edit and save tech stack modifications | Yes |

---

## 6. Audit & Generation History Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/projects/{id}/generations` | List all AI generation audit runs for project | Yes |
| `GET` | `/api/generations/{generation_id}` | Get details of a single generation attempt | Yes |

---

## 7. Export Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/projects/{id}/export/pdf` | Stream generated publication-grade PDF report | Yes |

---

## 8. Legal & Health Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/legal/documents` | Retrieve metadata for Terms, Privacy, Use | No |
| `GET` | `/api/legal/status` | Check if authenticated user accepted current docs| Optional |
| `GET` | `/health` | Liveness check probe | No |
| `GET` | `/ready` | Readiness check probe verifying database | No |
