"""Centralized AI Client supporting Google Gemini official SDK with bounded retries and token tracking."""

import logging
import random
import time
from typing import Optional, Tuple
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import get_settings
from app.services.ai.errors import (
    AIAuthenticationError,
    AIQuotaExceededError,
    AIRateLimitError,
    AIRetryExhaustedError,
    AITimeoutError,
    AIUnsupportedModelError,
)

logger = logging.getLogger(__name__)


class GeminiAIClient:
    """Official Google GenAI SDK client wrapper."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.gemini_api_key
        self.model = model if model is not None else settings.gemini_model
        self.timeout = settings.ai_request_timeout_seconds
        self.max_retries = settings.ai_max_retries
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        if not self.api_key or not self.api_key.strip():
            raise AIAuthenticationError(
                "Gemini API key is not configured. Please set the GEMINI_API_KEY environment variable."
            )
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate(
        self,
        system_instruction: str,
        user_prompt: str,
    ) -> Tuple[str, int, Optional[int], Optional[int]]:
        """Invoke Gemini model with exponential backoff and return (raw_text, latency_ms, input_tokens, output_tokens)."""
        client = self._get_client()

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            temperature=0.4,
            max_output_tokens=8192,
        )

        attempts = 0
        last_error: Optional[Exception] = None

        while attempts <= self.max_retries:
            attempts += 1
            start_time = time.perf_counter()
            try:
                response = client.models.generate_content(
                    model=self.model,
                    contents=user_prompt,
                    config=config,
                )
                latency_ms = int((time.perf_counter() - start_time) * 1000)

                raw_text = response.text or ""
                input_tokens = None
                output_tokens = None
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    input_tokens = getattr(response.usage_metadata, "prompt_token_count", None)
                    output_tokens = getattr(response.usage_metadata, "candidates_token_count", None)

                logger.info(
                    "AI generation succeeded",
                    extra={
                        "extra_fields": {
                            "model": self.model,
                            "latency_ms": latency_ms,
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "attempt": attempts,
                        }
                    },
                )
                return raw_text, latency_ms, input_tokens, output_tokens

            except APIError as e:
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                status_code = getattr(e, "code", 500)
                error_msg = str(e).lower()

                # Non-retryable authentication failure
                if status_code in (401, 403) or "api_key_invalid" in error_msg or "permission" in error_msg:
                    raise AIAuthenticationError(f"AI provider authentication failed: {str(e)}")

                # Non-retryable model retirement / not found error
                if status_code == 404 or "not_found" in error_msg or "no longer available" in error_msg:
                    raise AIUnsupportedModelError(
                        f"Configured Gemini model '{self.model}' is not found or no longer available: {str(e)}"
                    )

                # Quota exhaustion / Free tier limit
                if "quota" in error_msg or "resource_exhausted" in error_msg:
                    raise AIQuotaExceededError(
                        "AI provider quota exhausted or free-tier rate limit reached. Please check your Gemini API billing/quota or retry in a short while."
                    )

                # Rate limit
                if status_code == 429 or "rate" in error_msg:
                    last_error = AIRateLimitError("AI rate limit encountered.")
                elif status_code in (500, 502, 503, 504):
                    last_error = AITimeoutError(f"Transient AI provider error ({status_code}).")
                else:
                    last_error = e

                if attempts > self.max_retries:
                    break

                # Exponential backoff with jitter
                backoff = (2 ** attempts) + random.uniform(0.1, 0.5)
                logger.warning(
                    f"Transient AI error on attempt {attempts}/{self.max_retries}: {str(e)}. Retrying in {backoff:.2f}s..."
                )
                time.sleep(backoff)

            except Exception as e:
                # General network or timeout error
                last_error = e
                if attempts > self.max_retries:
                    break
                backoff = (2 ** attempts) + random.uniform(0.1, 0.5)
                time.sleep(backoff)

        raise AIRetryExhaustedError(
            f"AI provider request failed after {self.max_retries} retries: {str(last_error)}"
        )


class MockAIClient:
    """Test double providing deterministic, realistic responses for testing."""

    def __init__(self, should_fail: bool = False, fail_error: Optional[Exception] = None) -> None:
        self.should_fail = should_fail
        self.fail_error = fail_error
        self.model = "mock-gemini-v1"

    def generate(
        self,
        system_instruction: str,
        user_prompt: str,
    ) -> Tuple[str, int, Optional[int], Optional[int]]:
        if self.should_fail:
            if self.fail_error:
                raise self.fail_error
            raise AITimeoutError("Simulated mock timeout failure.")

        # Determine whether Business Model Canvas or Technology Stack was requested
        if "customer_segments" in system_instruction.lower():
            mock_json = """{
  "overview": "A specialized AI-powered business blueprint platform designed to streamline startup validation and software architectural planning.",
  "key_strategic_focus": "Automated domain-specific business modelling and pragmatic technology recommendations.",
  "customer_segments": {
    "block_title": "Customer Segments",
    "summary": "Technical and non-technical founders, early-stage solo entrepreneurs, and startup incubators.",
    "recommendations": [
      "Focus primarily on individual solo founders building their initial MVP.",
      "Target university entrepreneurship programs and accelerators as institutional partners."
    ],
    "rationale": "Solo founders have the highest pain point regarding business modelling and technology stack uncertainty.",
    "assumptions": ["Founders are willing to pay for structured business validation and blueprint exports."],
    "risks_uncertainties": ["Market saturation with generic generic AI chatbots."],
    "validation_experiments": ["Interview 20 founders in startup communities regarding their business plan bottlenecks."]
  },
  "value_propositions": {
    "block_title": "Value Propositions",
    "summary": "Transform raw startup ideas into verifiable Business Model Canvases and production-ready tech stacks in minutes.",
    "recommendations": [
      "Deliver rigorous 9-block canvases with actionable validation experiments.",
      "Provide concrete technology recommendations with realistic cost transparency."
    ],
    "rationale": "Saves founders weeks of fragmented research and architectural debate.",
    "assumptions": ["Actionable structure provides higher perceived value than generic prose."],
    "risks_uncertainties": ["Users may misunderstand AI suggestions as legally binding advice."],
    "validation_experiments": ["Offer free blueprint reviews to 10 founders and measure Net Promoter Score."]
  },
  "channels": {
    "block_title": "Channels",
    "summary": "Developer communities, Product Hunt, GitHub, and organic educational SEO.",
    "recommendations": [
      "Publish open-source architectural blueprints and business case studies.",
      "Engage directly in startup communities on Reddit, Indie Hackers, and X."
    ],
    "rationale": "Organic content marketing aligns with a bootstrapped marketing budget.",
    "assumptions": ["High-intent search traffic exists for business plan generation."],
    "risks_uncertainties": ["Long lead time for SEO ranking."],
    "validation_experiments": ["Publish 3 detailed case studies and track referral traffic and conversions."]
  },
  "customer_relationships": {
    "block_title": "Customer Relationships",
    "summary": "Self-service SaaS with transparent guided onboarding and automated AI generation.",
    "recommendations": [
      "Provide step-by-step intake forms with draft saving.",
      "Offer exportable PDF reports for investor and team sharing."
    ],
    "rationale": "Minimizes support overhead while delivering immediate value.",
    "assumptions": ["Users can navigate self-service without requiring 1-on-1 consulting."],
    "risks_uncertainties": ["Low user retention if they only validate a single business idea."],
    "validation_experiments": ["Measure completion rate of the multi-step intake wizard."]
  },
  "revenue_streams": {
    "block_title": "Revenue Streams",
    "summary": "Freemium tiered subscription for multi-project generation and team exports.",
    "recommendations": [
      "Free tier: 1 project with full canvas and tech stack generation.",
      "Pro tier ($19/month): unlimited projects, regeneration, version comparison, and PDF export."
    ],
    "rationale": "Low entry friction with recurring value for active builders and agencies.",
    "assumptions": ["At least 4% of active users will convert to Pro tier."],
    "risks_uncertainties": ["Churn after the initial blueprint is created."],
    "validation_experiments": ["Test a pre-order paywall on export features with a discount."]
  },
  "key_resources": {
    "block_title": "Key Resources",
    "summary": "Python AI orchestration pipeline, vetted domain prompt templates, and PostgreSQL database.",
    "recommendations": [
      "Maintain proprietary structured prompt templates and deterministic validation rules.",
      "Build high-reliability PDF generation and export capabilities."
    ],
    "rationale": "Reliable data persistence and structured output form the primary intellectual property.",
    "assumptions": ["LLM provider costs remain predictable under standard usage."],
    "risks_uncertainties": ["Upstream AI provider API changes or price increases."],
    "validation_experiments": ["Benchmark API token costs across 50 sample generations."]
  },
  "key_activities": {
    "block_title": "Key Activities",
    "summary": "AI pipeline optimization, prompt engineering, platform reliability, and community growth.",
    "recommendations": [
      "Continuously evaluate AI output quality against real founder feedback.",
      "Monitor system health, error rates, and latency."
    ],
    "rationale": "Consistent output quality is the primary driver of organic recommendations.",
    "assumptions": ["Regular prompt refinement increases user satisfaction."],
    "risks_uncertainties": ["Model drift causing malformed structured outputs."],
    "validation_experiments": ["Implement automated regression tests for prompt responses."]
  },
  "key_partnerships": {
    "block_title": "Key Partnerships",
    "summary": "AI model providers (Google Gemini), cloud platform (Render), and founder communities.",
    "recommendations": [
      "Partner with startup incubators to bundle the platform for cohort members.",
      "Maintain reliable cloud and AI provider integrations."
    ],
    "rationale": "Incubators provide high-intent user cohorts in batches.",
    "assumptions": ["Accelerators look for tools to standardize student founder pitches."],
    "risks_uncertainties": ["Slow enterprise / incubator sales cycles."],
    "validation_experiments": ["Pitch 3 university entrepreneurship cell directors."]
  },
  "cost_structure": {
    "block_title": "Cost Structure",
    "summary": "Cloud hosting (Render), AI API usage (Gemini), database storage, and domain/DNS.",
    "recommendations": [
      "Keep infrastructure lean via unified Docker container deployment.",
      "Implement rate limits and token caching to prevent API abuse."
    ],
    "rationale": "Guarantees a low break-even point with minimal monthly burn rate.",
    "assumptions": ["Monthly operational expenses remain under $50 during initial 1,000 users."],
    "risks_uncertainties": ["Spike in API costs from malicious or heavy automated users."],
    "validation_experiments": ["Simulate 100 concurrent generations and calculate peak cloud costs."]
  }
}"""
            return mock_json, 150, 420, 850

        # Technology Stack
        mock_tech_json = """{
  "architecture_summary": "A modern, lightweight Python-first web architecture combining FastAPI for high-performance API handling and React for a reactive, responsive user interface, deployed on containerized PaaS.",
  "estimated_monthly_infrastructure_total": "$7 - $25/month for initial launch",
  "frontend": {
    "category": "Frontend",
    "technology": "React 19 with TypeScript and Tailwind CSS",
    "purpose": "Interactive single-page application interface, state management, and real-time form intake.",
    "reason": "Provides type safety, high developer velocity, rich accessible components, and rapid UI styling.",
    "alternatives": ["Vue 3", "Next.js", "Svelte"],
    "tradeoffs": ["Requires client-side build step and careful bundle optimization."],
    "estimated_cost": "$0 (Bundled with backend container)",
    "cost_period": "monthly",
    "cost_assumptions": ["Static assets compiled and served directly from FastAPI or CDN."],
    "constraints": ["Keep dependencies lean to maintain fast initial load."],
    "verification_notes": "Pricing is an estimate based on current tier limits; verify on vendor pricing page."
  },
  "backend": {
    "category": "Backend",
    "technology": "FastAPI (Python 3.12) with Uvicorn",
    "purpose": "REST API service, authentication, AI orchestration, PDF generation, and input validation.",
    "reason": "Asynchronous performance, native Pydantic v2 validation, and seamless integration with Python AI SDKs.",
    "alternatives": ["Django REST Framework", "Flask", "Node.js Express"],
    "tradeoffs": ["Async Python requires awareness of non-blocking I/O patterns."],
    "estimated_cost": "$7/month (Render Starter Web Service)",
    "cost_period": "monthly",
    "cost_assumptions": ["Single container handling up to 50 requests/sec with uvicorn workers."],
    "constraints": ["Container memory limit of 512MB on starter tier."],
    "verification_notes": "Pricing is an estimate based on current tier limits; verify on vendor pricing page."
  },
  "database": {
    "category": "Database",
    "technology": "PostgreSQL 16 with SQLAlchemy 2.0 & Psycopg 3",
    "purpose": "Relational data persistence for users, projects, blueprints, and audit records.",
    "reason": "ACID compliance, robust JSONB support for blueprint versions, and mature migration tooling via Alembic.",
    "alternatives": ["MySQL", "MongoDB", "SQLite"],
    "tradeoffs": ["Requires connection pool management and migration discipline."],
    "estimated_cost": "$7/month (Render Managed PostgreSQL Starter)",
    "cost_period": "monthly",
    "cost_assumptions": ["1GB storage is sufficient for > 100,000 project and blueprint records."],
    "constraints": ["Requires SSL connection string in production."],
    "verification_notes": "Pricing is an estimate based on current tier limits; verify on vendor pricing page."
  },
  "hosting_infrastructure": {
    "category": "Hosting & Infrastructure",
    "technology": "Docker on Render Web Services",
    "purpose": "Multi-stage container execution, automated zero-downtime deployments, and SSL management.",
    "reason": "Single unified origin avoiding CORS issues, simple git push deployments, and built-in health checks.",
    "alternatives": ["Railway", "Fly.io", "AWS ECS / App Runner"],
    "tradeoffs": ["Cold starts on free tiers; starter paid plan recommended for production."],
    "estimated_cost": "$14/month combined (Web + DB)",
    "cost_period": "monthly",
    "cost_assumptions": ["Standard traffic with automated backups."],
    "constraints": ["Single region deployment recommended initially."],
    "verification_notes": "Pricing is an estimate based on current tier limits; verify on vendor pricing page."
  },
  "third_party_services": {
    "category": "Third-Party Services",
    "technology": "Google Gemini API & Postmark / SendGrid",
    "purpose": "Large language model inference for business modeling and transactional emails.",
    "reason": "Competitive per-token pricing, high context window, and fast inference times.",
    "alternatives": ["OpenAI GPT-4o", "Anthropic Claude 3.5 Sonnet"],
    "tradeoffs": ["External API dependency subject to provider rate limits."],
    "estimated_cost": "$0 - $10/month depending on generation volume",
    "cost_period": "usage-based",
    "cost_assumptions": ["Free tier covers initial testing; ~$0.002 per complete blueprint generation."],
    "constraints": ["Requires server-side API key configuration and exponential backoff."],
    "verification_notes": "Pricing is an estimate based on current tier limits; verify on vendor pricing page."
  },
  "scalability_considerations": [
    "Phase 1 (0 - 1,000 users): Single container + managed Postgres on Render.",
    "Phase 2 (1,000 - 50,000 users): Add database connection pooling (PgBouncer) and scale web service to 2 instances.",
    "Phase 3 (50,000+ users): Introduce background job processing (Celery / ARQ) for asynchronous generations and S3 storage for PDFs."
  ],
  "security_considerations": [
    "Argon2id password hashing with constant-time verification.",
    "HTTP-only, Secure session cookies with SameSite protection and CSRF validation.",
    "Strict server-side Pydantic input validation on all incoming payloads.",
    "Zero secrets exposed to browser bundles or client-side code."
  ]
}"""
        return mock_tech_json, 180, 510, 920
