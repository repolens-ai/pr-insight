from __future__ import annotations

from enum import Enum
from typing import Tuple, TypedDict

from pydantic import BaseModel


class Range(BaseModel):
    line_start: int  # should be 0-indexed
    line_end: int
    column_start: int = -1
    column_end: int = -1


class TodoItem(TypedDict):
    relevant_file: str
    line_range: Tuple[int, int]
    content: str


class PRReviewHeader(str, Enum):
    REGULAR = "## PR Reviewer Guide"
    INCREMENTAL = "## Incremental PR Reviewer Guide"


class ReasoningEffort(str, Enum):
    XHIGH = "xhigh"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"
    NONE = "none"


class PRDescriptionHeader(str, Enum):
    DIAGRAM_WALKTHROUGH = "Diagram Walkthrough"
    FILE_WALKTHROUGH = "File Walkthrough"


class ModelType(str, Enum):
    REGULAR = "regular"
    WEAK = "weak"
    REASONING = "reasoning"
