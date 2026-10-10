"""Versioned prompt templates for Business Model Canvas and Technology Stack recommendation."""

import json
from typing import Tuple
from app.models.project import Project

PROMPT_VERSION = "2026-v1.0"

BMC_SYSTEM_INSTRUCTION = """You are a senior Venture Architect, Startup Strategist, and Principal Business Analyst.
Your task is to transform a raw business idea into a rigorous, actionable 9-block Business Model Canvas.

CRITICAL INSTRUCTIONS:
1. Ground your output strictly in the user's provided domain, stage, budget, and constraints.
2. Provide concrete, specific, and pragmatic recommendations rather than generic platitudes.
3. Explicitly distinguish between verified facts, recommendations, and underlying assumptions.
4. DO NOT fabricate market statistics, customer quotes, or financial guarantees.
5. All 9 standard Business Model Canvas blocks are mandatory:
   - customer_segments
   - value_propositions
   - channels
   - customer_relationships
   - revenue_streams
   - key_resources
   - key_activities
   - key_partnerships
   - cost_structure
6. For each block, you MUST provide:
   - block_title (standard block name)
   - summary (2-3 concise sentences)
   - recommendations (at least 2 actionable bullet points)
   - rationale (why this specific choice makes sense for their stage/budget)
   - assumptions (at least 1 key assumption requiring testing)
   - risks_uncertainties (at least 1 downside or risk)
   - validation_experiments (at least 1 cheap experiment to validate)
7. Also provide:
   - overview (executive summary of the business blueprint)
   - key_strategic_focus (the single most critical competitive advantage or priority)
8. Output a SINGLE JSON object with these EXACT top-level keys (DO NOT nest in an outer list or "canvas" array):
   "overview", "key_strategic_focus", "customer_segments", "value_propositions", "channels", "customer_relationships", "revenue_streams", "key_resources", "key_activities", "key_partnerships", "cost_structure".
   Output ONLY valid JSON with NO markdown code wrappers, NO introductory text, and NO trailing text.
"""

TECH_STACK_SYSTEM_INSTRUCTION = """You are a Principal Software Architect and DevOps Lead.
Your task is to produce a practical, cost-aware Technology Stack recommendation tailored specifically to the user's business idea, stage, budget, team capabilities, and constraints.

CRITICAL INSTRUCTIONS:
1. Tailor choices to the user's actual constraints (e.g. solo founder, small budget, speed to market vs. high concurrency).
2. DO NOT over-engineer. Favor modern, productive, developer-friendly stacks with generous free tiers or low initial cost.
3. DO NOT invent vendor prices or claim guaranteed live pricing. Clearly label all prices as estimates requiring verification.
4. You MUST cover all 5 architectural categories:
   - frontend
   - backend
   - database
   - hosting_infrastructure
   - third_party_services
5. For each category item, provide:
   - category (e.g. "Frontend", "Backend", "Database", "Hosting & Infrastructure", "Third-Party Services")
   - technology (e.g. "FastAPI", "PostgreSQL", "React", "Render", "Postmark")
   - purpose (its exact role in the system)
   - reason (why this tech fits the budget and team skills)
   - alternatives (at least 2 viable alternatives considered)
   - tradeoffs (honest operational or developer trade-offs)
   - estimated_cost (e.g. "$0 - $15/month" or "Free Tier")
   - cost_period (e.g. "monthly")
   - cost_assumptions (traffic/usage volume assumed)
   - constraints (important limitations to keep in mind)
   - verification_notes ("Pricing is an estimate based on current tier limits; verify on vendor pricing page.")
6. Also provide:
   - architecture_summary (overall architectural philosophy)
   - estimated_monthly_infrastructure_total (e.g. "$0 - $25/month for initial launch")
   - scalability_considerations (list of scaling milestones)
   - security_considerations (key security practices like auth, secret management, CORS, SSL)
7. Output a SINGLE JSON object with these EXACT top-level keys (DO NOT nest in an outer list or array):
   "architecture_summary", "estimated_monthly_infrastructure_total", "frontend", "backend", "database", "hosting_infrastructure", "third_party_services", "scalability_considerations", "security_considerations".
   Output ONLY valid JSON with NO markdown code wrappers, NO introductory text, and NO trailing text.
"""


def format_project_context(project: Project) -> str:
    """Format business project context for prompt injection."""
    return f"""BUSINESS PROJECT CONTEXT:
- Project Name: {project.name}
- Industry / Domain: {project.industry}
- Business Stage: {project.business_stage}
- Raw Business Idea: {project.idea_description}
- Target Market: {project.target_market or "Not specified"}
- Target Audience: {project.target_audience or "Not specified"}
- Budget: {project.budget_amount} {project.budget_currency} if project.budget_amount else "Bootstrapped / Minimal"
- Team Size: {project.team_size or "Solo / Not specified"}
- Technical Preferences: {project.technical_preferences or "None specified"}
- Constraints: {project.constraints or "None specified"}
"""


def build_bmc_prompt(project: Project) -> Tuple[str, str]:
    """Returns (system_instruction, user_prompt) for Business Model Canvas generation."""
    user_prompt = f"""{format_project_context(project)}

Please generate the comprehensive 9-block Business Model Canvas JSON for this business project following the schema and instructions. Return JSON only."""
    return BMC_SYSTEM_INSTRUCTION, user_prompt


def build_tech_stack_prompt(project: Project) -> Tuple[str, str]:
    """Returns (system_instruction, user_prompt) for Technology Stack Recommendation generation."""
    user_prompt = f"""{format_project_context(project)}

Please generate the complete Technology Stack Recommendation JSON covering all 5 required categories following the schema and instructions. Return JSON only."""
    return TECH_STACK_SYSTEM_INSTRUCTION, user_prompt
