"""Pydantic Model for a project object."""
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from datetime import datetime

Proj_Status = Literal["planning", "in_progress", "on_hold", "completed", "cancelled"]

class Project(BaseModel):
    """A single Project."""

    model_config = ConfigDict(extra="forbid") # prevent any extra properties from being inculded in the declaration of this object

    name: str = Field(min_length=5, max_length=200) 
    room: str = Field(min_length=1)
    budget: int
    start_date: datetime
    target_completion_date: datetime
    project_status: Proj_Status

    # id: str = Field(pattern=r"^TKT-\d{5}$") # regular expression to ensure that the id is in the correct format
    # title: str = Field(min_length=5, max_length=200) 
    # body: str = Field(min_length=1)
    # priority: Priority
    # status: Status
    # category: Category
    # tenant: str = Field(min_length=1, max_length=50)
    # customer_id: str = Field(pattern=r"^CUS-\d{5}$") # regular expression to ensure that the customer_id is in the correct format
    # assignee: str | None = None
    # channel: Channel
    # tags: list[str] = Field(default_factory=list, max_length=10) # default_factory is used to create a new list for each instance of the Ticket class, and max_length is used to limit the number of tags to 10
    # created_at: datetime 
    # updated_at: datetime