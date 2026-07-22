"""Pydantic Model for a task object."""
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

Task_Status = Literal["todo", "in_progress", "blocked", "done"]
Trade = Literal["plumbing", "electrical", "carpentry", "HVAC", "demolition"]


class Task(BaseModel):
    """A single task record tied to a project."""

    model_config = ConfigDict(extra="forbid") # prevent any extra properties from being inculded in the declaration of this object

    project_record: str = Field(min_length=5, max_length=200) # Look into a regular expression possibly 
    description: str = Field(min_length=1)
    est_cost: int
    actual_cost: int
    trade_category: Trade
    task_status: Task_Status


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