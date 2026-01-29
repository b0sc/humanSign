"""Pydantic models for session data."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Request to create a new session."""
    
    user_external_id: str = Field(..., min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionResponse(BaseModel):
    """Session data response."""
    
    id: UUID
    user_id: UUID
    started_at: datetime
    ended_at: Optional[datetime]
    session_hash: Optional[str]
    domain: Optional[str]
    metadata: dict[str, Any]


class SessionEndRequest(BaseModel):
    """Request to end a session."""
    
    session_hash: Optional[str] = None


class SessionFeaturesResponse(BaseModel):
    """Computed features for a session."""
    
    id: UUID
    session_id: UUID
    computed_at: datetime
    total_keystrokes: int
    duration_ms: float
    avg_dwell_time: float
    std_dwell_time: float
    avg_flight_time: float
    std_flight_time: float
    avg_wpm: float
    error_rate: float
    pause_count: int
    avg_pause_duration: float
    digraph_features: dict[str, float]
    prediction_score: float
    is_human: bool
