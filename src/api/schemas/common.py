"""CivicPulse — Common Response Schemas."""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class APIResponse(BaseModel):
    """Standard success response wrapper."""
    status: str = "success"
    data: Any = None
    meta: Optional[dict] = None


class APIError(BaseModel):
    """Standard error response."""
    status: str = "error"
    code: str
    message: str
    timestamp: datetime


class PaginationMeta(BaseModel):
    """Cursor-based pagination metadata."""
    cursor: Optional[str] = None
    has_more: bool = False
    total: Optional[int] = None
    limit: int = 20
