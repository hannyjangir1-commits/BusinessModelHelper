# AI Business Architect — Security Architecture & Threat Model

The AI Business Architect platform applies a comprehensive defense-in-depth model across the entire application lifecycle.

---

## 1. Authentication & Credential Storage

1. **Argon2id Password Hashing**:
   - The platform uses `argon2-cffi` configured with production-grade parameters:
     - Memory Cost: 65,536 KiB (64 MB)
     - Time Cost (Iterations): 3
     - Parallelism: 4 threads
     - Hash Length: 32 bytes
   - Plaintext passwords are never persisted to disk, stored in memory beyond validation, logged, or returned in API responses.
2. **Password Complexity Policy**:
   - Minimum length: 8 characters; maximum length: 128 characters.
   - Enforces inclusion of at least one alphabetical letter and one numeric digit.

---

## 2. Session Management & Cookie Security

1. **HTTP-Only Cookies**:
   - Client-side JavaScript cannot access the session cookie (`document.cookie`), mitigating Cross-Site Scripting (XSS) session theft.
2. **Production Secure Flag**:
   - Configured via `SESSION_HTTPS_ONLY=true` in production to ensure transmission occurs exclusively over HTTPS/TLS connections.
3. **SameSite Policy**:
   - Cookies use `SameSite=Lax` to protect against Cross-Site Request Forgery (CSRF).
4. **Cryptographic Signatures**:
   - Sessions are signed using `itsdangerous.URLSafeTimedSerializer` with a server-side 256-bit secret key and salt. Tampered tokens are immediately rejected.
5. **CSRF Protection**:
   - For state-changing mutations (`POST`, `PATCH`, `DELETE`), client requests must supply an `X-CSRF-Token` header matching the token bound to the active session.

---

## 3. Authorization & IDOR Prevention

1. **Strict Ownership Enforcing**:
   - All database queries resolving projects, blueprints, and audit runs enforce `user_id == current_user.id`.
   - Guessing or enumerating UUIDs belonging to other users yields generic `404 Not Found` responses rather than disclosing resource existence.
2. **Mass-Assignment Defense**:
   - Pydantic update schemas constrain modifiable fields. Critical fields such as `user_id`, `id`, `created_at`, and `password_hash` are completely excluded from request schemas.

---

## 4. Rate Limiting & Abuse Prevention

1. **In-Memory Sliding Window Rate Limiting**:
   - Login attempts are bounded to 5 attempts per 5-minute sliding window per IP and username.
   - Registration attempts are bounded to 10 attempts per hour per IP.
2. **Bounded AI Retries**:
   - AI generation requests use exponential backoff with jitter capped at 3 retries for transient errors. Authentication failures and malformed requests fail immediately without retry loops.

---

## 5. Secret Protection & Logging Hygiene

1. **Zero Client-Side Secrets**:
   - The Google Gemini API key and database credentials exist exclusively on the server. No secrets are prefixed with `VITE_` or embedded in the compiled JavaScript bundle.
2. **Structured Log Sanitization**:
   - `logging_config.py` filters sensitive dictionary keys (`password`, `secret_key`, `gemini_api_key`, `token`) and scrubs database passwords from connection URLs before formatting.
