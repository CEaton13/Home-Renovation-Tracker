"""Pydantic Model for a task object."""
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

Task_Status = Literal["todo", "in_progress", "blocked", "done"]
Trade = Literal["plumbing", "electrical", "carpentry", "hvac", "demolition", "painting", "flooring", "general"]


class TaskCreate(BaseModel):
    """A single task record tied to a project."""

    description: str = Field(min_length=1, max_length=500)
    est_cost: int = Field(ge=0)
    trade_category: Trade


class TaskUpdate(BaseModel):
    """Request response for updating an existing task."""

    description: str | None = Field(default=None, min_length=1, max_length=500)
    est_cost: int | None = Field(default=None, ge=0)
    trade: Trade | None = None
    status: Task_Status | None = None

class TaskComplete(BaseModel):
    """Returns the acutual cost once the task has been completed."""

    actual_cost: int = Field(ge=0)

class TaskRead(BaseModel):
    """Response returned for a task."""

    id: int
    project_id: int
    description: str
    est_cost: int
    actual_cost: int | None
    trade_category: Trade
    status: Task_Status