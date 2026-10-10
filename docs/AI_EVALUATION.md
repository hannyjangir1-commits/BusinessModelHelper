# AI Business Architect — AI Evaluation Suite & Quality Gates

This document details the evaluation methodology, dataset composition, and automated quality gates governing AI generation pipelines in the AI Business Architect platform.

---

## 1. Evaluation Methodology

Rather than treating AI calls as black boxes, the platform enforces structured generation quality across four dimensions:

1. **Schema Compliance**: Evaluates whether model outputs strictly parse into the required Pydantic v2 schemas (`BusinessModelCanvasData` and `TechnologyStackData`).
2. **Completeness**:
   - For BMC: Verifies all 9 canvas blocks are fully populated with summaries, recommendations, assumptions, risks, and validation experiments.
   - For Tech Stack: Verifies all 5 architectural categories (Frontend, Backend, Database, Hosting, Third-Party APIs) are provided.
3. **Deterministic Consistency**:
   - Executes deterministic Python rules verifying that low-budget projects trigger advisory channel warnings if high-expenditure marketing is suggested.
   - Ensures technology stacks flag operational over-engineering (e.g. Kubernetes for solo founders).
4. **Latency & Token Efficiency**:
   - Measures end-to-end inference and parsing latency in milliseconds.
   - Audits input prompt token counts and generated output token counts.

---

## 2. Benchmark Test Cases (`backend/evaluations/test_cases.json`)

The evaluation dataset comprises 5 realistic startup archetypes representing varied domains, stages, and budgets:

| Case ID | Venture Name | Domain | Stage | Budget | Constraints |
|---|---|---|---|---|---|
| `case-01-edtech-ai` | NeuroLearn Adaptive STEM | EdTech | Validation | $5,000 USD | FERPA compliance |
| `case-02-cleantech-logistics`| FleetZero Carbon Optimizer | CleanTech | MVP | €25,000 EUR | EU CSRD carbon rules |
| `case-03-creator-economy` | PromptVibe Audio Kits | Creator Tools | Idea | $500 USD | Hosting < $20/month |
| `case-04-healthtech-remote` | PulseCardio Telehealth | Digital Health| Prototype | $50,000 USD | HIPAA & BAA requirements|
| `case-05-b2b-procurement` | VendorMatch Procurement | B2B SaaS | Validation | $10,000 USD| SOC2 readiness |

---

## 3. Running the AI Evaluation Suite

To execute the automated evaluation runner:

```bash
# Set PYTHONPATH to backend
export PYTHONPATH="backend"

# Run evaluation suite
python backend/evaluations/run_evaluations.py
```

### Execution Modes:
- **With Live Gemini API**: If `GEMINI_API_KEY` is present in the environment, the suite runs live against the configured Gemini model (`gemini-2.5-flash`).
- **With Mock Client**: If no API key is provided (e.g., standard CI/CD pipelines), the suite runs deterministically using `MockAIClient` without network calls.

The runner generates a machine-readable report at `backend/evaluations/evaluation_report.json`.
