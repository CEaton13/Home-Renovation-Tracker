"""Pydantic Model for a project object."""
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from datetime import date

Proj_Status = Literal["planning", "in_progress", "on_hold", "completed", "cancelled"]

class ProjectCreate(BaseModel):
    """Create a single renovation Project."""
    
    name: str = Field(min_length=1, max_length=200) 
    room: str = Field(min_length=1)
    budget: int = Field(ge=0)
    start_date: date
    target_completion_date: date

class ProjectUpdate(BaseModel):
    """Update to an existing renovation project."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    budget: int | None = Field(default=None, ge=0)
    target_completion_date: date | None = None
    status: Proj_Status | None = None


class ProjectRead(BaseModel):
    """Returned response for a single renovation project."""

    id: int
    name: str
    room: str
    budget_cents: int
    start_date: date
    target_completion_date: date
    status: Proj_Status