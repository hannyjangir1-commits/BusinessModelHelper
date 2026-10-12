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

## 6. AI Business Idea Validator Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/projects/{id}/validator/generate` | Generate / regenerate strategic validation report (SWOT, risks, experiments) | Yes |
| `GET` | `/api/projects/{id}/validator` | Get latest (or specified `?version=X`) validation report | Yes |
| `PATCH` | `/api/projects/{id}/validator` | Manually refine and save validation report content | Yes |
| `GET` | `/api/projects/{id}/validator/versions`| List all saved validation report versions | Yes |

### Idea Validator Data Structure Example
`POST /api/projects/{id}/validator/generate` response:
```json
{
  "success": true,
  "data": {
    "id": "bp-uuid-1234",
    "project_id": "proj-uuid-5678",
    "module_type": "validation_report",
    "version": 1,
    "content_json": {
      "overview": "Strong market need in creator economy with distinct differentiation...",
      "problem_solution_fit": {
        "problem_statement": "Independent creators struggle with multi-platform workflow fragmentation.",
        "who_experiences_it": "Full-time digital creators earning $20k-$100k annually.",
        "frequency_and_severity": "Daily friction causing 5+ hours wasted per week.",
        "existing_alternatives": ["Notion templates", "Manual spreadsheets", "Zapier webhooks"],
        "supporting_evidence": ["Creator surveys show 68% cite workflow as main burnout driver."],
        "missing_evidence": ["Willingness to switch from existing free setups."]
      },
      "target_customer_clarity": {
        "primary_segment": "Solo newsletter writers and video creators",
        "secondary_segments": ["Boutique agency managers"],
        "buyer_vs_end_user": "Same individual",
        "customer_pain_points": ["Disjointed tooling", "Subscription fatigue"],
        "adoption_barriers": ["Data migration friction"],
        "unvalidated_assumptions": ["Desire for all-in-one vs best-of-breed"]
      },
      "value_proposition_assessment": {
        "core_benefit": "Unified multi-channel automation in under 15 minutes setup",
        "differentiation_hypotheses": ["Pre-built creator templates with zero code"],
        "potential_weaknesses": ["Broad feature scope risks shallow functionality"],
        "critical_dependencies": ["Social platform API rate limits"],
        "key_evidence_needed": ["Organic retention above 40% at 30 days"]
      },
      "swot_analysis": {
        "strengths": ["Fast lightweight UI", "Affordable starter pricing"],
        "weaknesses": ["Small founding team", "No direct enterprise sales force"],
        "opportunities": ["Rapid expansion of independent creator economy"],
        "threats": ["Platform API policy shifts", "Incumbent platform expansion"]
      },
      "business_risks": [
        {
          "category": "Customer Adoption",
          "description": "High switching costs from established creator stacks",
          "why_it_matters": "Increases customer acquisition cost",
          "likelihood": "Medium",
          "impact": "High",
          "supporting_info": "Creators resist rebuilding audience databases",
          "suggested_mitigation": "Build 1-click import bridges for Substack and YouTube",
          "recommended_next_action": "Interview 10 creators about migration friction"
        }
      ],
      "validation_experiments": [
        {
          "experiment_name": "Concierge Onboarding Pilot",
          "experiment_type": "Pilot",
          "hypothesis": "If we manually migrate workflows, 70% will activate within 48h",
          "target_audience": "10 target newsletter creators",
          "procedure": "Offer free 30-min setup call in exchange for workflow review",
          "estimated_duration": "2 weeks",
          "estimated_cost": "$0",
          "success_criteria": ">= 7 active daily users after 14 days",
          "interpretation_guidance": "If <5 activate, redesign the core workflow loop"
        }
      ],
      "interview_questions": [
        {
          "question_text": "Walk me through the last time you published content across multiple platforms.",
          "focus_category": "Past Behavior",
          "rationale": "Focuses on concrete historical actions rather than speculative promises."
        }
      ],
      "summary": {
        "strongest_supporting_evidence": "Demonstrated manual workaround pain",
        "largest_uncertainties": ["Price elasticity"],
        "highest_priority_risks": ["Platform lock-in"],
        "most_useful_next_experiment": "Concierge Onboarding Pilot",
        "unverified_assumptions": ["Willingness to pay $29/mo"],
        "qualitative_readiness_assessment": "Pre-Validation: Validate migration feasibility before building automated sync"
      }
    }
  }
}
```

---

## 7. Market and Competitor Research Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/projects/{id}/market-research/generate` | Run live SSRF-protected search & generate competitor intelligence | Yes |
| `GET` | `/api/projects/{id}/market-research` | Get latest (or specified `?version=X`) market research report | Yes |
| `PATCH` | `/api/projects/{id}/market-research` | Manually edit competitor profiles and research data | Yes |
| `GET` | `/api/projects/{id}/market-research/versions`| List all saved market research versions | Yes |

*(Note: `/api/projects/{id}/research/*` is supported as an alias route for backward compatibility).*

### SSRF Safeguards on External Research
Outbound research requests validate all target URLs using IP address parsing to strictly prohibit:
- Private IPv4 ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
- Loopback addresses (`127.0.0.0/8`, `::1`)
- Link-local and cloud metadata addresses (`169.254.0.0/16`, `fe80::/10`)
- Multicast and reserved ranges

---

## 8. AI Execution Roadmap Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/projects/{id}/roadmap/generate` | Generate intelligent 30/60/90-day execution roadmap | Yes |
| `GET` | `/api/projects/{id}/roadmap` | Retrieve overview with tasks, milestones, and completion stats | Yes |
| `POST` | `/api/projects/{id}/roadmap/tasks` | Create a new custom roadmap task | Yes |
| `PATCH` | `/api/projects/{id}/roadmap/tasks/{task_id}`| Update task status, priority, milestone, or details | Yes |
| `DELETE` | `/api/projects/{id}/roadmap/tasks/{task_id}`| Permanently delete a roadmap task | Yes |
| `GET` | `/api/projects/{id}/roadmap/versions` | List historical roadmap blueprint versions | Yes |

### Create Roadmap Task Request Example
`POST /api/projects/{id}/roadmap/tasks`
```json
{
  "milestone": "30-day",
  "stage": "Customer Validation",
  "title": "Conduct 15 founder discovery interviews",
  "description": "Recruit and interview target creators focusing on workflow bottlenecks",
  "priority": "critical",
  "status": "in_progress",
  "estimated_effort_days": 5.0,
  "start_day": 1,
  "duration_days": 14,
  "dependencies": [],
  "deliverable": "Interview synthesis notes and pain-point frequency table",
  "success_criteria": "At least 12 completed interviews with actionable transcripts",
  "related_risk": "Lack of customer problem validation",
  "kpi": "15 completed interviews"
}
```

### DAG Dependency Cycle Defense
When tasks declare prerequisites in `dependencies`, the roadmap engine performs cycle detection using a **3-color Depth-First Search (DFS)** algorithm. Circular dependencies (e.g., Task A depends on Task B which depends on Task A) are rejected with a `422 Unprocessable Entity` error before writing to the database.

---

## 9. Business Blueprint Copilot Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/projects/{id}/copilot/chat` | Interact with Copilot (Q&A advisor or propose block edit) | Yes |
| `POST` | `/api/projects/{id}/copilot/proposals/{proposal_id}/accept`| Explicitly accept and apply proposal diff to blueprint | Yes |
| `POST` | `/api/projects/{id}/copilot/proposals/{proposal_id}/reject`| Explicitly reject proposal without modifying blueprints | Yes |
| `GET` | `/api/projects/{id}/copilot/revisions` | List audit log of historical proposals and decisions | Yes |

### Copilot Propose Edit Interaction Example
`POST /api/projects/{id}/copilot/chat`
```json
{
  "query": "Refine the Customer Segments block to prioritize solo content creators and add high-intent agency niches.",
  "action_type": "propose_edit",
  "target_module": "business_model",
  "target_section": "customer_segments"
}
```

Response with Proposal Diff:
```json
{
  "success": true,
  "data": {
    "action_type": "propose_edit",
    "proposal": {
      "proposal_id": "prop-uuid-7890",
      "target_module": "business_model",
      "target_section": "customer_segments",
      "previous_content": {
        "title": "Customer Segments",
        "description": "General digital creators and social media influencers"
      },
      "proposed_content": {
        "title": "Customer Segments",
        "description": "Primary: Solo newsletter writers and YouTube creators ($20k-$100k ARR). Secondary: Boutique influencer agencies managing 5-15 client accounts."
      },
      "reasoning": "Sharper segmentation focuses go-to-market efforts on users with proven willingness to pay.",
      "status": "pending",
      "created_at": "2026-10-12T19:00:00Z"
    }
  }
}
```

> **Safety Rule**: A proposal **never** mutates the underlying blueprint until the user explicitly issues `POST /api/projects/{id}/copilot/proposals/{proposal_id}/accept`.

---

## 10. Audit & Generation History Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/projects/{id}/generations` | List all AI generation audit runs for project | Yes |
| `GET` | `/api/generations/{generation_id}` | Get details of a single generation attempt | Yes |

---

## 11. Export Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/projects/{id}/export/pdf` | Stream generated publication-grade PDF report | Yes |

---

## 12. Legal & Health Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/legal/documents` | Retrieve metadata for Terms, Privacy, Use | No |
| `GET` | `/api/legal/status` | Check if authenticated user accepted current docs| Optional |
| `GET` | `/health` | Liveness check probe | No |
| `GET` | `/ready` | Readiness check probe verifying database (bounded 3s timeout)| No |
