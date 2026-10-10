"""Schemas for AI generation audit runs and blueprints."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, computed_field


class GenerationRunResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    module_type: str
    status: str
    model: str
    prompt_version: str
    latency_ms: Optional[int] = None
    input_token_count: Optional[int] = None
    output_token_count: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BlueprintResponse(BaseModel):
    id: str
    project_id: str
    module_type: str
    version: int
    content_json: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def content(self) -> Dict[str, Any]:
        return self.content_json

    @computed_field
    @property
    def sources(self) -> List[Any]:
        if isinstance(self.content_json, dict):
            return self.content_json.get("sources", [])
        return []

    model_config = ConfigDict(from_attributes=True)


class BlueprintVersionItem(BaseModel):
    id: str
    version: int
    module_type: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
