"""Market and Competitor Research orchestration pipeline with source attribution."""

from datetime import datetime, timezone
import json
import logging
from typing import Any, List, Optional, Tuple
from sqlalchemy import desc, func, select, update
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.models.blueprint import Blueprint
from app.models.generation import GenerationRun
from app.models.project import Project
from app.models.user import User
from app.schemas.market_research import MarketResearchReportData, SourceItem
from app.services.ai.client import GeminiAIClient
from app.services.ai.prompts import PROMPT_VERSION
from app.services.research.provider import BaseResearchProvider, get_research_provider

logger = logging.getLogger(__name__)


def generate_search_queries(project: Project) -> List[str]:
    """Derive targeted search queries from business project parameters."""
    return [
        f"{project.industry} top competitors alternatives pricing",
        f"{project.industry} market trends growth barriers",
        f"{project.name} {project.industry} customer segments",
    ]


def fetch_external_evidence(
    provider: BaseResearchProvider,
    queries: List[str],
) -> List[SourceItem]:
    """Execute queries against external search provider and deduplicate sources."""
    seen_urls = set()
    aggregated_sources: List[SourceItem] = []

    for q in queries:
        try:
            results = provider.search(q, max_results=4)
            for s in results:
                if s.url not in seen_urls:
                    seen_urls.add(s.url)
                    aggregated_sources.append(s)
        except Exception as e:
            logger.warning(f"Error querying external search for '{q}': {str(e)}")

    return aggregated_sources


def build_research_synthesis_prompt(
    project: Project,
    sources: List[SourceItem],
) -> Tuple[str, str]:
    """Build Gemini prompt grounding competitive synthesis in retrieved external sources."""
    system_instruction = (
        "You are a rigorous Market Research Analyst and Competitive Intelligence Specialist. "
        "Analyze the provided business project and synthesized external web evidence. "
        "Ground your findings in the provided source excerpts wherever available. "
        "Do not fabricate competitors, fake URLs, or non-existent market sizes. "
        "If specific pricing or feature data is not observed in the sources, explicitly mark it as 'Unknown / Requires direct quote'. "
        "Return ONLY a single valid JSON object adhering to the schema. No markdown formatting."
    )

    sources_summary = "\n".join([
        f"- Source [{s.url}] ({s.title}): {s.snippet}"
        for s in sources[:8]
    ]) if sources else "No external search results retrieved (Analyze based on established domain heuristics)."

    user_prompt = f"""
Business Project Context:
Name: {project.name}
Industry: {project.industry}
Idea: {project.idea_description}
Business Stage: {project.business_stage}
Target Market: {project.target_market or 'Unspecified'}

Retrieved External Sources & Citations:
{sources_summary}

Synthesize a comprehensive market research report matching this exact JSON schema:
{{
  "executive_summary": "<Strategic summary of competitive dynamics, customer bargaining power, and landscape>",
  "industry_definition": "<Precise market segment boundaries and target sector>",
  "market_trends": [
    {{
      "trend_title": "<Trend 1>",
      "description": "<Detailed trend observation>",
      "implications_for_founder": "<How founder should adapt>",
      "supporting_sources": ["<URL from sources list if applicable>"]
    }},
    {{
      "trend_title": "<Trend 2>",
      "description": "<Detailed trend observation>",
      "implications_for_founder": "<How founder should adapt>",
      "supporting_sources": ["<URL from sources list if applicable>"]
    }}
  ],
  "barriers_to_entry": ["<Barrier 1>", "<Barrier 2>", "<Barrier 3>"],
  "distribution_channels": ["<Direct sales>", "<SEO / Content>", "<Strategic partnerships>"],
  "competitors": [
    {{
      "name": "<Competitor Name 1>",
      "website": "<Official domain or URL>",
      "product_summary": "<What they offer>",
      "target_audience": "<Who they serve>",
      "pricing_model": "Subscription",
      "estimated_pricing": "<Observed pricing tiers or 'Custom Quote'>",
      "key_features": ["<Feature 1>", "<Feature 2>"],
      "positioning": "<Their brand claim>",
      "differentiators": ["<Claimed differentiator>"],
      "strengths": ["<Observed strength 1>"],
      "weaknesses": ["<Observed customer complaint or weakness>"],
      "source_urls": ["<Source URL>"]
    }},
    {{
      "name": "<Competitor Name 2>",
      "website": "<Official domain or URL>",
      "product_summary": "<What they offer>",
      "target_audience": "<Who they serve>",
      "pricing_model": "Freemium",
      "estimated_pricing": "<Observed pricing tiers>",
      "key_features": ["<Feature 1>", "<Feature 2>"],
      "positioning": "<Their brand claim>",
      "differentiators": ["<Claimed differentiator>"],
      "strengths": ["<Observed strength 1>"],
      "weaknesses": ["<Observed weakness 1>"],
      "source_urls": ["<Source URL>"]
    }}
  ],
  "comparison_matrix": [
    {{
      "criterion": "Target Audience",
      "founder_solution": "Solo founders & early MVPs",
      "competitor_comparison": {{
        "<Competitor 1>": "Mid-market & enterprise",
        "<Competitor 2>": "General non-technical consumer"
      }}
    }},
    {{
      "criterion": "Pricing Accessibility",
      "founder_solution": "Transparent low-barrier entry",
      "competitor_comparison": {{
        "<Competitor 1>": "High enterprise retainer",
        "<Competitor 2>": "Freemium with feature lock"
      }}
    }},
    {{
      "criterion": "Technical Depth",
      "founder_solution": "Deterministic financials + production tech recommendations",
      "competitor_comparison": {{
        "<Competitor 1>": "High-level strategy only",
        "<Competitor 2>": "Generic AI chat text"
      }}
    }}
  ],
  "market_sizing": {{
    "market_definition": "<Scope definition>",
    "tam_description": "<Total addressable market qualitative context>",
    "sam_description": "<Serviceable addressable market>",
    "som_description": "<Initial obtainable market target>",
    "sizing_caveats": "Figures represent qualitative planning benchmarks derived from industry indicators."
  }},
  "research_methodology_disclaimer": "Synthesized from external search evidence and AI competitive intelligence."
}}
"""
    return system_instruction, user_prompt


def validate_research_response(
    raw_text: str,
    sources: List[SourceItem],
) -> MarketResearchReportData:
    """Parse JSON and validate against MarketResearchReportData schema, injecting citations."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        data_dict = json.loads(cleaned)
    except Exception as e:
        raise ValidationError(f"AI returned invalid JSON: {str(e)}")

    # Ensure collected sources are injected into the final validated model
    data_dict["sources"] = [s.model_dump() for s in sources]

    try:
        return MarketResearchReportData.model_validate(data_dict)
    except Exception as e:
        raise ValidationError(f"Research output failed schema validation: {str(e)}")


def generate_market_research_report(
    db: Session,
    user: User,
    project: Project,
    client: Optional[Any] = None,
    search_provider: Optional[BaseResearchProvider] = None,
) -> Tuple[Blueprint, List[str]]:
    """Execute end-to-end Market & Competitor Research workflow."""
    ai_client = client or GeminiAIClient()
    model_name = getattr(ai_client, "model", "gemini-2.5-flash")
    provider = search_provider or get_research_provider()

    # 1. Audit generation run record
    run = GenerationRun(
        project_id=project.id,
        user_id=user.id,
        module_type="market_research",
        status="running",
        model=model_name,
        prompt_version=PROMPT_VERSION,
    )
    db.add(run)
    db.commit()
    run_id = run.id

    try:
        # 2. Derive queries and retrieve live search sources
        queries = generate_search_queries(project)
        sources = fetch_external_evidence(provider, queries)

        # 3. Build prompt and invoke AI synthesis
        system_instruction, user_prompt = build_research_synthesis_prompt(project, sources)
        raw_text, latency_ms, input_tokens, output_tokens = ai_client.generate(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
        )

        # 4. Parse and validate schema
        validated_data = validate_research_response(raw_text, sources)

        # 5. Determine next version
        latest_version = db.execute(
            select(func.coalesce(func.max(Blueprint.version), 0)).where(
                Blueprint.project_id == project.id,
                Blueprint.module_type == "market_research",
            )
        ).scalar_one()
        new_version = latest_version + 1

        # 6. Save persistent blueprint
        blueprint = Blueprint(
            project_id=project.id,
            module_type="market_research",
            version=new_version,
            content_json=validated_data.model_dump(),
        )
        db.add(blueprint)

        # 7. Complete audit run
        db.execute(
            update(GenerationRun)
            .where(GenerationRun.id == run_id)
            .values(
                status="success",
                latency_ms=latency_ms,
                input_token_count=input_tokens,
                output_token_count=output_tokens,
                completed_at=datetime.now(timezone.utc),
            )
        )

        project.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(blueprint)

        warnings = []
        if not sources:
            warnings.append("No live web sources were retrievable. Report synthesized based on baseline domain heuristics.")

        return blueprint, warnings

    except Exception as e:
        db.rollback()
        error_code = getattr(e, "code", "RESEARCH_GENERATION_FAILED")
        error_msg = getattr(e, "message", str(e))

        db.execute(
            update(GenerationRun)
            .where(GenerationRun.id == run_id)
            .values(
                status="failed",
                error_code=error_code,
                error_message=error_msg,
                completed_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
        logger.error(f"Market research generation failed: {error_msg}")
        raise
