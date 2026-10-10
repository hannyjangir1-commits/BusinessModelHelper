"""Response extraction, JSON parsing, and Pydantic schema validation."""

import json
import re
from typing import Any, Dict, Type, TypeVar
from pydantic import BaseModel, ValidationError

from app.schemas.business_model import BusinessModelCanvasData
from app.schemas.technology_stack import TechnologyStackData
from app.services.ai.errors import AIMalformedOutputError, AISchemaValidationError

T = TypeVar("T", bound=BaseModel)


def extract_json_from_text(raw_text: str) -> Dict[str, Any]:
    """Extract valid JSON from LLM response text, stripping markdown wrappers or preambles."""
    if not raw_text or not raw_text.strip():
        raise AIMalformedOutputError("Received empty response from AI provider.")

    text = raw_text.strip()

    # If wrapped in markdown code fence: ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()

    # Sometimes LLMs add leading or trailing non-JSON comments
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        text = text[first_brace : last_brace + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise AIMalformedOutputError(f"Could not parse valid JSON from AI response: {str(e)}")


def validate_schema(data_dict: Dict[str, Any], schema_cls: Type[T]) -> T:
    """Validate dictionary against Pydantic schema class."""
    try:
        return schema_cls.model_validate(data_dict)
    except ValidationError as e:
        errors = e.errors()
        error_details = {
            "fields": [str(err.get("loc")) for err in errors],
            "messages": [err.get("msg") for err in errors],
        }
        raise AISchemaValidationError(
            f"Schema validation failed for {schema_cls.__name__}: {len(errors)} error(s) found.",
            details=error_details,
        )


def validate_bmc_response(raw_text: str) -> BusinessModelCanvasData:
    """Parse and validate Business Model Canvas response."""
    data_dict = extract_json_from_text(raw_text)

    # Normalize if model nested the 9 blocks inside a list (e.g. 'canvas', 'blocks', 'business_model_canvas')
    canonical_bmc_keys = [
        "customer_segments",
        "value_propositions",
        "channels",
        "customer_relationships",
        "revenue_streams",
        "key_resources",
        "key_activities",
        "key_partnerships",
        "cost_structure",
    ]
    for container_key in ("canvas", "blocks", "business_model_canvas", "sections"):
        if container_key in data_dict and isinstance(data_dict[container_key], list):
            for item in data_dict[container_key]:
                if isinstance(item, dict):
                    title = str(item.get("block_title", "")).lower().strip().replace(" ", "_").replace("-", "_")
                    for k in canonical_bmc_keys:
                        if k in title or title in k:
                            data_dict[k] = item
                            break

    return validate_schema(data_dict, BusinessModelCanvasData)


def validate_tech_stack_response(raw_text: str) -> TechnologyStackData:
    """Parse and validate Technology Stack response."""
    data_dict = extract_json_from_text(raw_text)

    # Normalize if categories are returned inside a list
    canonical_tech_keys = [
        "frontend",
        "backend",
        "database",
        "hosting_infrastructure",
        "third_party_services",
    ]
    for container_key in ("categories", "stack", "recommendations", "components"):
        if container_key in data_dict and isinstance(data_dict[container_key], list):
            for item in data_dict[container_key]:
                if isinstance(item, dict):
                    cat = str(item.get("category", "")).lower().strip().replace(" ", "_").replace("-", "_").replace("&", "_")
                    for k in canonical_tech_keys:
                        if k in cat or cat in k or ("host" in cat and "host" in k) or ("third" in cat and "third" in k):
                            data_dict[k] = item
                            break

    # Unwrap if category is provided as a list of recommendation items (e.g. frontend: [{...}])
    for k in canonical_tech_keys:
        if k in data_dict and isinstance(data_dict[k], list) and len(data_dict[k]) > 0:
            data_dict[k] = data_dict[k][0]

    return validate_schema(data_dict, TechnologyStackData)
