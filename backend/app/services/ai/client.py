"""Centralized AI Client supporting Google Gemini official SDK with bounded retries and token tracking."""

import logging
import random
import time
from typing import Any, Dict, Optional, Tuple
import httpx
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
    """Official Google GenAI SDK client wrapper with strict timeout budgets."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.gemini_api_key
        self.model = model if model is not None else settings.gemini_model
        self.timeout = float(timeout if timeout is not None else settings.ai_request_timeout_seconds)
        self.max_retries = int(max_retries if max_retries is not None else settings.ai_max_retries)
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        if not self.api_key or not self.api_key.strip():
            raise AIAuthenticationError(
                "Gemini API key is not configured. Please set the GEMINI_API_KEY environment variable."
            )
        if self._client is None:
            timeout_ms = max(1, int(self.timeout * 1000)) if self.timeout else None
            http_options = types.HttpOptions(timeout=timeout_ms) if timeout_ms else None
            self._client = genai.Client(api_key=self.api_key, http_options=http_options)
        return self._client

    def generate(
        self,
        system_instruction: str,
        user_prompt: str,
        response_mime_type: Optional[str] = "application/json",
    ) -> Tuple[str, int, Optional[int], Optional[int]]:
        """Invoke Gemini model with bounded retries and overall timeout budget."""
        client = self._get_client()

        config_kwargs: Dict[str, Any] = {
            "system_instruction": system_instruction,
            "temperature": 0.4,
            "max_output_tokens": 8192,
        }
        if response_mime_type:
            config_kwargs["response_mime_type"] = response_mime_type

        total_budget_seconds = float(self.timeout) if self.timeout else 60.0
        overall_start = time.perf_counter()

        attempts = 0
        last_error: Optional[Exception] = None

        while attempts <= self.max_retries:
            elapsed_total = time.perf_counter() - overall_start
            remaining_total = total_budget_seconds - elapsed_total
            if remaining_total <= 0:
                raise AITimeoutError(
                    f"AI provider request timed out: total budget of {self.timeout}s exceeded across {attempts} attempt(s)."
                )

            attempts += 1
            # Bound per-attempt provider timeout to remaining time budget
            attempt_timeout_ms = max(100, int(remaining_total * 1000))
            config_kwargs["http_options"] = types.HttpOptions(timeout=attempt_timeout_ms)
            config = types.GenerateContentConfig(**config_kwargs)

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

            except (httpx.TimeoutException, TimeoutError) as e:
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                last_error = AITimeoutError(f"AI provider request timed out ({latency_ms}ms): {str(e)}")
                elapsed_after = time.perf_counter() - overall_start
                remaining = total_budget_seconds - elapsed_after
                if attempts > self.max_retries or remaining <= 0:
                    raise last_error

                backoff = (2 ** attempts) + random.uniform(0.1, 0.5)
                if remaining <= backoff:
                    raise AITimeoutError(
                        f"AI provider request timed out: remaining budget of {remaining:.2f}s is insufficient for retry backoff ({backoff:.2f}s)."
                    )
                logger.warning(
                    f"Transient AI timeout on attempt {attempts}/{self.max_retries}: {str(e)}. Retrying in {backoff:.2f}s..."
                )
                time.sleep(backoff)

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

                # Timeout / deadline exceeded
                if (
                    status_code in (408, 504)
                    or "deadline" in error_msg
                    or "timed out" in error_msg
                    or "timeout" in error_msg
                ):
                    last_error = AITimeoutError(f"Transient AI provider timeout ({status_code}): {str(e)}")
                elif status_code == 429 or "rate" in error_msg:
                    last_error = AIRateLimitError("AI rate limit encountered.")
                elif status_code in (500, 502, 503):
                    last_error = AITimeoutError(f"Transient AI provider error ({status_code}).")
                else:
                    last_error = e

                elapsed_after = time.perf_counter() - overall_start
                remaining = total_budget_seconds - elapsed_after
                if attempts > self.max_retries or remaining <= 0:
                    if isinstance(last_error, AITimeoutError):
                        raise last_error
                    break

                backoff = (2 ** attempts) + random.uniform(0.1, 0.5)
                if remaining <= backoff:
                    if isinstance(last_error, AITimeoutError):
                        raise last_error
                    raise AITimeoutError(
                        f"AI provider request timed out: total budget of {self.timeout}s exceeded before retry backoff ({backoff:.2f}s)."
                    )
                logger.warning(
                    f"Transient AI error on attempt {attempts}/{self.max_retries}: {str(e)}. Retrying in {backoff:.2f}s..."
                )
                time.sleep(backoff)

            except Exception as e:
                # General network or unexpected error
                if isinstance(e, (httpx.TimeoutException, TimeoutError)):
                    last_error = AITimeoutError(f"AI provider request timed out: {str(e)}")
                else:
                    last_error = e

                elapsed_after = time.perf_counter() - overall_start
                remaining = total_budget_seconds - elapsed_after
                if attempts > self.max_retries or remaining <= 0:
                    if isinstance(last_error, AITimeoutError):
                        raise last_error
                    break

                backoff = (2 ** attempts) + random.uniform(0.1, 0.5)
                if remaining <= backoff:
                    if isinstance(last_error, AITimeoutError):
                        raise last_error
                    raise AITimeoutError(
                        f"AI provider request timed out: total budget of {self.timeout}s exceeded before retry backoff ({backoff:.2f}s)."
                    )
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
        response_mime_type: Optional[str] = "application/json",
        **kwargs: Any,
    ) -> Tuple[str, int, Optional[int], Optional[int]]:
        if self.should_fail:
            if self.fail_error:
                raise self.fail_error
            raise AITimeoutError("Simulated mock timeout failure.")

        # Determine whether Business Model Canvas, Idea Validator, or Technology Stack was requested
        lowered_sys = system_instruction.lower()

        # Business Model Canvas
        if "customer_segments" in lowered_sys or "9-block business model canvas" in lowered_sys:
            mock_bmc_json = """{
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
            return mock_bmc_json, 150, 420, 850

        # Idea Validator
        if "validator" in lowered_sys or "validation" in lowered_sys or "swot" in lowered_sys:
            mock_val_json = """{
  "overview": "The business targets a verified friction in founder execution with significant upside if early demand is established prior to technical buildout.",
  "problem_solution_fit": {
    "problem_statement": "Founders struggle with fragmented planning, guesswork in financial math, and technical uncertainty during launch.",
    "who_experiences_it": "Early-stage technical and non-technical solo founders and indie hackers.",
    "frequency_and_severity": "Weekly recurring pain during early conception and fundraising sprints.",
    "existing_alternatives": ["Spreadsheets", "Generic chat interfaces", "Notion templates"],
    "supporting_evidence": ["High search volume for business plan templates and financial projection models."],
    "missing_evidence": ["Direct founder conversion data on willingness to pay for automated architecture planning."]
  },
  "target_customer_clarity": {
    "primary_segment": "Solo entrepreneurs and technical builders launching their first MVP.",
    "secondary_segments": ["University incubators", "Freelance agency advisors"],
    "buyer_vs_end_user": "Founder is typically both the buyer and the primary operator.",
    "customer_pain_points": ["Fear of running out of runway", "Uncertainty in choosing scalable tech stacks"],
    "adoption_barriers": ["Habitual reliance on ad-hoc spreadsheets and free ChatGPT prompts."],
    "unvalidated_assumptions": ["Founders prioritize structured exportable reports over conversational chat."]
  },
  "value_proposition_assessment": {
    "core_benefit": "End-to-end verified blueprinting combining Lean Canvas, deterministic financials, and production tech recommendations in minutes.",
    "differentiation_hypotheses": ["Deterministic financial formulas ensure CFO-level accuracy instead of hallucinated AI arithmetic."],
    "potential_weaknesses": ["Churn risk after a founder successfully validates their single current venture."],
    "critical_dependencies": ["High uptime on AI inference and reliable document generation."],
    "key_evidence_needed": ["Net Promoter Score above 40 from 20 alpha testers."]
  },
  "swot_analysis": {
    "strengths": ["Proprietary deterministic financial engine", "Unified single-origin architecture", "Zero mock fallback in production"],
    "weaknesses": ["Bootstrap marketing budget", "Single-founder engineering capacity"],
    "opportunities": ["Partnerships with startup accelerators and university entrepreneurship cells", "Growing indie hacker ecosystem"],
    "threats": ["Generic LLM tool suites adding native canvas plugins", "Fast-moving API pricing from cloud providers"]
  },
  "business_risks": [
    {
      "category": "Customer Adoption",
      "description": "Founders may use the tool once for initial validation and fail to retain.",
      "why_it_matters": "Increases customer acquisition cost amortization burden.",
      "likelihood": "Medium",
      "impact": "High",
      "supporting_info": "Common dynamic in early-stage business planning software.",
      "suggested_mitigation": "Introduce ongoing execution roadmaps and copilot iterations to retain active builders.",
      "recommended_next_action": "Survey initial 15 users on which features they would use on a monthly basis."
    },
    {
      "category": "Market",
      "description": "Proliferation of low-cost generic wrapper tools creating market noise.",
      "why_it_matters": "Higher CAC and skepticism among sophisticated founders.",
      "likelihood": "High",
      "impact": "Medium",
      "supporting_info": "Rapid expansion of AI tools in developer directories.",
      "suggested_mitigation": "Differentiate via rigorous financial math, source-attributed research, and exportable investor-grade PDFs.",
      "recommended_next_action": "Publish open architectural benchmarks comparing deterministic vs hallucinated models."
    },
    {
      "category": "Technology",
      "description": "Upstream LLM latency spikes during peak usage periods.",
      "why_it_matters": "Degrades user perception of responsiveness during intake wizards.",
      "likelihood": "Low",
      "impact": "Medium",
      "supporting_info": "Occasional transient rate limits on cloud providers.",
      "suggested_mitigation": "Exponential backoff with jitter and asynchronous job status tracking.",
      "recommended_next_action": "Run load test simulating 20 concurrent generation requests."
    }
  ],
  "validation_experiments": [
    {
      "experiment_name": "Founder Problem Interviews",
      "experiment_type": "Customer Interviews",
      "hypothesis": "At least 12 out of 15 founders will cite financial projection modeling as their most dreaded pre-launch hurdle.",
      "target_audience": "Active indie hackers on Reddit and Twitter/X.",
      "procedure": "Conduct 20-minute structured neutral interviews asking about past planning attempts.",
      "estimated_duration": "2 weeks",
      "estimated_cost": "$0",
      "success_criteria": "80% confirm high friction and state they would welcome automated modeling.",
      "interpretation_guidance": "If confirmed, emphasize financial engine in hero messaging."
    },
    {
      "experiment_name": "Landing Page Demand Test",
      "experiment_type": "Landing Page",
      "hypothesis": "A focused value proposition page will achieve >= 7% email waitlist conversion from organic developer traffic.",
      "target_audience": "Builders in entrepreneurship subreddits.",
      "procedure": "Deploy single-page landing site with blueprint screenshots and email capture.",
      "estimated_duration": "1 week",
      "estimated_cost": "$20 (domain & hosting)",
      "success_criteria": "100 qualified waitlist signups within 7 days.",
      "interpretation_guidance": "If below 3%, test alternative positioning focused on investor pitch readiness."
    }
  ],
  "interview_questions": [
    {
      "question_text": "Walk me through the last time you prepared a business plan or financial model for a project.",
      "focus_category": "Past Behavior",
      "rationale": "Focuses on concrete past actions rather than hypothetical future intentions."
    },
    {
      "question_text": "What tools or templates did you turn to, and where did they fall short?",
      "focus_category": "Current Friction",
      "rationale": "Reveals genuine friction and current competitive workarounds."
    },
    {
      "question_text": "Have you ever paid for a planning tool, course, or advisory service in the past 12 months?",
      "focus_category": "Budget Authority",
      "rationale": "Verifies historical willingness to allocate budget to solving this problem."
    }
  ],
  "summary": {
    "strongest_supporting_evidence": "Founders universally express frustration with complex spreadsheet financial formulas and generic AI chat advice.",
    "largest_uncertainties": ["Long-term recurring retention after initial business launch", "Optimal monthly price point for solo builders"],
    "highest_priority_risks": ["One-off tool churn without sticky execution features"],
    "most_useful_next_experiment": "15 problem discovery interviews with active founders building in public.",
    "unverified_assumptions": ["Solo builders will pay a monthly subscription vs a one-off export fee."],
    "qualitative_readiness_assessment": "Pre-Validation Stage (Strong hypothesis; recommend 10 founder interviews prior to heavy ad spend)."
  }
}"""
            return mock_val_json, 160, 480, 890

        if "competitive intelligence" in lowered_sys or "market research analyst" in lowered_sys or "competitor profiles" in lowered_sys or ("market research" in lowered_sys and "architecture" not in lowered_sys):
            mock_research_json = """{
  "executive_summary": "The market shows intense founder demand for verified business blueprinting and deterministic financial modeling, with existing players primarily split between static presentation tools and generic conversational bots.",
  "industry_definition": "AI-Assisted Business Planning & Architecture SaaS",
  "market_trends": [
    {
      "trend_title": "Demand for Deterministic Financial Precision",
      "description": "Founders and investors are rejecting hallucinated LLM calculations in favor of code-executed formulas.",
      "implications_for_founder": "Differentiate by emphasizing pure Python mathematical rigor and zero LLM arithmetic.",
      "supporting_sources": ["https://news.ycombinator.com/item?id=38129412"]
    },
    {
      "trend_title": "Rise of Micro-SaaS Solo Operators",
      "description": "Explosion of solo developers launching independent software ventures requiring rapid validation without consulting agencies.",
      "implications_for_founder": "Price accessible self-service tiers under $30/month with immediate export capabilities.",
      "supporting_sources": ["https://www.producthunt.com/products/business-model-canvas"]
    }
  ],
  "barriers_to_entry": [
    "High trust barrier for financial and architectural planning accuracy",
    "API rate limits and inference costs on unoptimized prompts",
    "Customer churn following initial business launch"
  ],
  "distribution_channels": [
    "Organic founder communities (Indie Hackers, Reddit, Product Hunt)",
    "Partnerships with university entrepreneurship incubators",
    "Open-source architectural case studies and templates"
  ],
  "competitors": [
    {
      "name": "LivePlan / Traditional Planners",
      "website": "https://www.liveplan.com",
      "product_summary": "Established traditional business planning software with multi-year accounting templates.",
      "target_audience": "Small business owners and bank loan applicants",
      "pricing_model": "Subscription",
      "estimated_pricing": "$20 - $40 / month",
      "key_features": ["Financial forecasts", "Bank-ready templates", "SBA format exports"],
      "positioning": "Traditional small business bank compliance",
      "differentiators": ["Recognized by traditional lenders"],
      "strengths": ["Decades of brand equity", "Extensive accounting terminology"],
      "weaknesses": ["Slow, manual input forms", "No AI tech stack recommendations", "Outdated UI"],
      "source_urls": ["https://www.producthunt.com/products/business-model-canvas"]
    },
    {
      "name": "Generic AI Chatbots (ChatGPT / Claude)",
      "website": "https://chatgpt.com",
      "product_summary": "General-purpose generative chat interfaces.",
      "target_audience": "Broad consumer & enterprise",
      "pricing_model": "Freemium",
      "estimated_pricing": "$20 / month",
      "key_features": ["Freeform text generation", "Prompt chat"],
      "positioning": "Universal AI assistant",
      "differentiators": ["Massive foundational model power"],
      "strengths": ["Universal accessibility", "Fast conversational brainstorm"],
      "weaknesses": ["Unreliable arithmetic", "No structured database persistence", "No exportable investor blueprint format"],
      "source_urls": ["https://news.ycombinator.com/item?id=38129412"]
    }
  ],
  "comparison_matrix": [
    {
      "criterion": "Target Audience",
      "founder_solution": "Solo founders & modern tech builders",
      "competitor_comparison": {
        "LivePlan / Traditional Planners": "Brick-and-mortar SMBs & bank applicants",
        "Generic AI Chatbots (ChatGPT / Claude)": "General public"
      }
    },
    {
      "criterion": "Financial Engine Rigor",
      "founder_solution": "Deterministic Python formulas + break-even units",
      "competitor_comparison": {
        "LivePlan / Traditional Planners": "Manual multi-page accounting tables",
        "Generic AI Chatbots (ChatGPT / Claude)": "Hallucinated / approximate numbers"
      }
    },
    {
      "criterion": "Technology Stack Guidance",
      "founder_solution": "Tailored production architecture recommendations with cost trade-offs",
      "competitor_comparison": {
        "LivePlan / Traditional Planners": "None",
        "Generic AI Chatbots (ChatGPT / Claude)": "Generic unstructured bullet points"
      }
    }
  ],
  "market_sizing": {
    "market_definition": "Global early-stage digital entrepreneurship planning software",
    "tam_description": "Over 5 million new digital ventures launched globally each year.",
    "sam_description": "Approx. 800,000 solo tech builders, agency consultants, and indie developers.",
    "som_description": "Initial target of 2,500 active subscribers within year 1.",
    "sizing_caveats": "Figures represent qualitative planning benchmarks derived from industry indicators."
  },
  "research_methodology_disclaimer": "Synthesized from external search evidence and AI competitive intelligence."
}"""
            return mock_research_json, 170, 520, 950

        if "execution roadmap" in lowered_sys or "actionable roadmap" in lowered_sys or ("roadmap" in lowered_sys and "architecture" not in lowered_sys and "devops" not in lowered_sys):
            mock_roadmap_json = """{
  "roadmap_philosophy": "De-risk customer willingness to pay and core unit economics in days 1-30 prior to writing production code, followed by focused MVP execution and managed beta rollout.",
  "tasks": [
    {
      "task_key": "TSK-01",
      "milestone": "30-day",
      "stage": "Research & Validation",
      "title": "Conduct 15 Founder Discovery Interviews",
      "description": "Interview 15 active early-stage founders to validate friction around business modeling and financial planning spreadsheets.",
      "priority": "critical",
      "estimated_effort_days": 3.0,
      "start_day": 1,
      "duration_days": 10,
      "dependencies": [],
      "deliverable": "Synthesized interview notes with common pain point frequency ranking",
      "success_criteria": ">= 80% confirm high friction with spreadsheets and unverified AI math",
      "related_risk": "Customer Adoption Risk",
      "kpi": "15 completed interviews"
    },
    {
      "task_key": "TSK-02",
      "milestone": "30-day",
      "stage": "Planning",
      "title": "Define Core Schema & API Specifications",
      "description": "Design Pydantic models, Alembic migrations, and endpoint contracts for the unified business blueprint platform.",
      "priority": "high",
      "estimated_effort_days": 2.5,
      "start_day": 11,
      "duration_days": 5,
      "dependencies": ["TSK-01"],
      "deliverable": "OpenAPI documentation and passing schema validation tests",
      "success_criteria": "Zero untyped endpoints and full Pydantic v2 validation",
      "related_risk": "Technical Architecture Risk",
      "kpi": "100% schema test coverage"
    },
    {
      "task_key": "TSK-03",
      "milestone": "30-day",
      "stage": "Planning",
      "title": "Design Interactive Figma / Tailwind UI Wireframes",
      "description": "Build responsive accessible layout components for the 9-block canvas, financial charts, and roadmap timeline.",
      "priority": "medium",
      "estimated_effort_days": 3.0,
      "start_day": 15,
      "duration_days": 7,
      "dependencies": ["TSK-02"],
      "deliverable": "Responsive Tailwind CSS component library",
      "success_criteria": "Mobile, tablet, and desktop responsive layouts with accessible contrast",
      "related_risk": "UI Usability Friction",
      "kpi": "Zero broken mobile views"
    },
    {
      "task_key": "TSK-04",
      "milestone": "60-day",
      "stage": "Prototype or MVP",
      "title": "Implement Deterministic Python Financial Engine",
      "description": "Code pure Python mathematical routines for revenue, COGS, break-even units, cash runway, and scenario modeling.",
      "priority": "critical",
      "estimated_effort_days": 5.0,
      "start_day": 31,
      "duration_days": 10,
      "dependencies": ["TSK-02"],
      "deliverable": "Financial engine unit test suite with 100% mathematical accuracy",
      "success_criteria": "Deterministic verification of known revenue, gross profit, and break-even cases",
      "related_risk": "Financial Credibility Risk",
      "kpi": "0 calculation discrepancies"
    },
    {
      "task_key": "TSK-05",
      "milestone": "60-day",
      "stage": "Prototype or MVP",
      "title": "Build AI Gemini Structured Generation Pipelines",
      "description": "Implement Gemini SDK wrapper with exponential backoff, token tracking, and structured Pydantic repair.",
      "priority": "critical",
      "estimated_effort_days": 6.0,
      "start_day": 40,
      "duration_days": 12,
      "dependencies": ["TSK-04"],
      "deliverable": "Robust AI service pipeline with zero silent mock fallback in production",
      "success_criteria": "Clean failure handling and graceful user-facing error reporting",
      "related_risk": "AI Provider Latency & Rate Limits",
      "kpi": ">= 99% structured JSON parse rate"
    },
    {
      "task_key": "TSK-06",
      "milestone": "60-day",
      "stage": "Launch Preparation",
      "title": "Containerize & Deploy to Render Web Services",
      "description": "Set up multi-stage Docker build, configure Render PostgreSQL internal database connection, and verify health checks.",
      "priority": "high",
      "estimated_effort_days": 3.0,
      "start_day": 52,
      "duration_days": 6,
      "dependencies": ["TSK-05"],
      "deliverable": "Live production URL on Render with single-origin static serving",
      "success_criteria": "Liveness /health endpoint returns 200 OK and assets load under 1.5s",
      "related_risk": "Deployment Downtime",
      "kpi": "100% deployment uptime"
    },
    {
      "task_key": "TSK-07",
      "milestone": "90-day",
      "stage": "Launch",
      "title": "Onboard 20 Private Beta Founders",
      "description": "Invite 20 active founders to build and export their business blueprints and collect structured feedback.",
      "priority": "high",
      "estimated_effort_days": 4.0,
      "start_day": 61,
      "duration_days": 14,
      "dependencies": ["TSK-06"],
      "deliverable": "User feedback report and Net Promoter Score metric",
      "success_criteria": ">= 70% complete at least 3 planning modules",
      "related_risk": "Onboarding Drop-off",
      "kpi": "NPS >= 45"
    },
    {
      "task_key": "TSK-08",
      "milestone": "90-day",
      "stage": "Measurement & Iteration",
      "title": "Iterate Copilot Interactivity & Public Launch",
      "description": "Incorporate beta founder feedback, polish interactive editing, and announce on Product Hunt and developer communities.",
      "priority": "medium",
      "estimated_effort_days": 5.0,
      "start_day": 76,
      "duration_days": 14,
      "dependencies": ["TSK-07"],
      "deliverable": "Public launch release and announcement posts",
      "success_criteria": ">= 200 registered users in the first 14 days",
      "related_risk": "Distribution Stagnation",
      "kpi": "200 registered founders"
    }
  ]
}"""
            return mock_roadmap_json, 160, 500, 920

        if "business blueprint editor" in lowered_sys or "propose_edit" in lowered_sys:
            mock_copilot_proposal_json = """{
  "target_module": "business_model",
  "target_section": "customer_segments",
  "reasoning": "Refined customer segments to prioritize solo developers and micro-SaaS builders with high willingness to pay.",
  "proposed_content": {
    "block_title": "Customer Segments",
    "summary": "High-intent solo tech founders, micro-SaaS builders, and startup accelerator cohorts seeking verified blueprints.",
    "recommendations": [
      "Target developer communities on GitHub and Twitter/X with open-source blueprints.",
      "Offer self-service tier with instant PDF export.",
      "Partner with startup accelerators for cohort-wide subscriptions."
    ]
  }
}"""
            return mock_copilot_proposal_json, 140, 320, 480

        if "copilot" in lowered_sys or "founder's question" in lowered_sys or "architect copilot" in lowered_sys:
            mock_copilot_qa = (
                "Based on your saved blueprint, your primary strategic advantage is combining deterministic "
                "financial modeling with automated technology stack blueprints. To reduce churn, focus on the "
                "30-day roadmap milestones for founder discovery interviews."
            )
            return mock_copilot_qa, 120, 280, 150

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
    "purpose": "Multi-stage container execution, automated rolling deployments, and SSL management.",
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
