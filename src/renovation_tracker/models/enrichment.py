"""Pydantic models for AI-generated project enrichment."""

from typing import Literal

from pydantic import BaseModel, Field

from renovation_tracker.models.task import Trade


class SuggestedTask(BaseModel):
    """A single AI-suggested task within a project's enrichment."""

    description: str = Field(min_length=1, max_length=500)
    trade_category: Trade
    rough_estimate: int = Field(ge=0)


class EnrichmentPayload(BaseModel):
    """Validated structured output from the enrichment model call."""

    suggested_tasks: list[SuggestedTask] = Field(default_factory=list, max_length=20)
    confidence: float = Field(ge=0, le=1)
    ai_generated: Literal[True] = True