# AI Business Architect — Database Architecture & Schema

The application uses PostgreSQL with SQLAlchemy 2.0 and Alembic for declarative schema management and migrations. In local/testing environments without PostgreSQL credentials, SQLite is supported via engine dialect adaptation.

---

## 1. Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    USERS ||--o{ PROJECTS : "owns"
    USERS ||--o{ GENERATION_RUNS : "initiates"
    USERS ||--o{ LEGAL_ACCEPTANCES : "consents to"
    PROJECTS ||--o{ BLUEPRINTS : "contains versions of"
    PROJECTS ||--o{ GENERATION_RUNS : "tracks runs for"

    USERS {
        string id PK
        string username UK
        string email UK
        string password_hash
        string display_name
        string bio
        string country
        string preferred_currency
        datetime created_at
        datetime updated_at
        datetime last_login_at
        boolean is_active
    }

    PROJECTS {
        string id PK
        string user_id FK
        string name
        text idea_description
        string industry
        string business_stage
        string target_market
        text target_audience
        float budget_amount
        string budget_currency
        string team_size
        text technical_preferences
        text constraints
        datetime created_at
        datetime updated_at
    }

    BLUEPRINTS {
        string id PK
        string project_id FK
        string module_type
        int version
        jsonb content_json
        datetime created_at
        datetime updated_at
    }

    GENERATION_RUNS {
        string id PK
        string project_id FK
        string user_id FK
        string module_type
        string status
        string model
        string prompt_version
        int latency_ms
        int input_token_count
        int output_token_count
        string error_code
        text error_message
        datetime created_at
        datetime completed_at
    }

    LEGAL_ACCEPTANCES {
        string id PK
        string user_id FK
        string document_type
        string document_version
        datetime accepted_at
    }
```

---

## 2. Table Specifications

### 2.1 `users`
- Stores registered user credentials and preferences.
- `username`: Indexed, unique, normalized lowercase (3-30 chars).
- `email`: Indexed, unique, normalized lowercase.
- `password_hash`: One-way Argon2id hash. Plaintext passwords are never stored.

### 2.2 `projects`
- Core entity representing a user's business project.
- Foreign key `user_id` references `users.id` with `ON DELETE CASCADE`.
- Indexed on `user_id` for efficient user-scoped queries.

### 2.3 `blueprints`
- Stores immutable, versioned outputs of the Business Model Canvas and Technology Stack.
- `content_json`: PostgreSQL `JSONB` with automatic fallback to generic JSON on non-PostgreSQL dialects.
- Composite unique constraint: `("project_id", "module_type", "version")` ensuring version integrity.
- Foreign key `project_id` references `projects.id` with `ON DELETE CASCADE`.

### 2.4 `generation_runs`
- Complete audit ledger of all AI provider invocations (both successful and failed).
- Tracks model identifiers, prompt template versions, execution latency, and token consumption.
- On generation failure, stores categorized error codes and safe diagnostic messages without corrupting existing blueprint records.

### 2.5 `legal_acceptances`
- Immutable audit log of user acceptance of Terms and Conditions and Privacy Policy versions upon registration.

---

## 3. Migration Management (Alembic)

Alembic is configured in `backend/alembic.ini` and `backend/migrations/`.

### Applying Migrations to Database:
```bash
# Set connection URL (or read from .env)
export DATABASE_URL="postgresql+psycopg://user:password@host:port/dbname"

# Apply latest revisions
alembic upgrade head
```

### Creating New Schema Revisions:
```bash
alembic revision --autogenerate -m "describe_changes"
```
