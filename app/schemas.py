from typing import Literal
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


TaskStatus = Literal["pending", "in_progress", "completed"]
TaskPriority = Literal["Low", "Medium", "High"]


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus = "pending"
    priority: TaskPriority = "Medium"
    due_date: date | None = None
    project: str = Field(default="General", max_length=100)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None
    project: str | None = Field(default=None, max_length=100)


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: date | None
    project: str