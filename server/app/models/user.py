"""Pydantic models for user data."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Request to create or get user."""
    
    external_id: str = Field(..., min_length=1, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)


class UserResponse(BaseModel):
    """User data response."""
    
    id: UUID
    external_id: str
    created_at: datetime
    metadata: dict[str, Any]
