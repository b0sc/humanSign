"""Session management API routes."""

from uuid import UUID
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.models import SessionCreate, SessionResponse, SessionEndRequest, SessionFeaturesResponse
from app.db import get_connection, queries
from app.services import keystroke_service, feature_extractor, ml_inference

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/start", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def start_session(request: SessionCreate) -> SessionResponse:
    """Start a new typing session."""
    async with get_connection() as conn:
        # Get or create user
        user = await conn.fetchrow(queries.GET_USER_BY_EXTERNAL_ID, request.user_external_id)
        
        if not user:
            user = await conn.fetchrow(
                queries.CREATE_USER,
                request.user_external_id,
                {},
            )
        
        # Create session
        session = await conn.fetchrow(
            queries.CREATE_SESSION,
            user["id"],
            request.domain,
            request.metadata,
        )
    
    return SessionResponse(
        id=session["id"],
        user_id=session["user_id"],
        started_at=session["started_at"],
        ended_at=session["ended_at"],
        session_hash=session["session_hash"],
        domain=session["domain"],
        metadata=session["metadata"],
    )


@router.post("/{session_id}/end", response_model=SessionResponse)
async def end_session(session_id: UUID, request: SessionEndRequest) -> SessionResponse:
    """End a typing session."""
    async with get_connection() as conn:
        session = await conn.fetchrow(
            queries.END_SESSION,
            session_id,
            request.session_hash,
        )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    return SessionResponse(
        id=session["id"],
        user_id=session["user_id"],
        started_at=session["started_at"],
        ended_at=session["ended_at"],
        session_hash=session["session_hash"],
        domain=session["domain"],
        metadata=session["metadata"],
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: UUID) -> SessionResponse:
    """Get session details."""
    async with get_connection() as conn:
        session = await conn.fetchrow(queries.GET_SESSION, session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    return SessionResponse(
        id=session["id"],
        user_id=session["user_id"],
        started_at=session["started_at"],
        ended_at=session["ended_at"],
        session_hash=session["session_hash"],
        domain=session["domain"],
        metadata=session["metadata"],
    )


@router.get("/{session_id}/features")
async def get_session_features(session_id: UUID) -> dict[str, Any]:
    """
    Get computed features for a session.
    
    If features haven't been computed yet, computes them on-demand.
    """
    # Check if features exist
    async with get_connection() as conn:
        existing = await conn.fetchrow(queries.GET_SESSION_FEATURES, session_id)
    
    if existing:
        return dict(existing)
    
    # Compute features on-demand
    keystrokes = await keystroke_service.get_session_keystrokes(session_id)
    
    if not keystrokes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No keystrokes found for session {session_id}",
        )
    
    features = feature_extractor.extract_features(keystrokes)
    
    return {
        "session_id": session_id,
        "computed": True,
        "features": features,
    }
