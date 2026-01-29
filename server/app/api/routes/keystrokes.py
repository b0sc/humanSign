"""Keystroke ingestion API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.models import KeystrokeBatchRequest, KeystrokeBatchResponse
from app.services import keystroke_service
from app.db import get_connection, queries

router = APIRouter(prefix="/keystrokes", tags=["keystrokes"])


@router.post("/batch", response_model=KeystrokeBatchResponse, status_code=status.HTTP_201_CREATED)
async def ingest_keystroke_batch(batch: KeystrokeBatchRequest) -> KeystrokeBatchResponse:
    """
    Ingest a batch of keystroke events.
    
    Events are processed to calculate dwell time and flight time,
    then stored in the database.
    """
    # Verify session exists
    async with get_connection() as conn:
        session = await conn.fetchrow(queries.GET_SESSION, batch.session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {batch.session_id} not found",
        )
    
    if session["ended_at"] is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add keystrokes to ended session",
        )
    
    # Calculate base sequence number for this batch
    base_sequence = batch.batch_sequence * 100  # Assuming max 100 per batch
    
    # Process and store
    processed = await keystroke_service.process_batch(batch, base_sequence)
    stored_count = await keystroke_service.store_batch(processed)
    
    return KeystrokeBatchResponse(
        session_id=batch.session_id,
        events_processed=stored_count,
        batch_sequence=batch.batch_sequence,
    )


@router.get("/{session_id}")
async def get_session_keystrokes(session_id: UUID):
    """Get all keystrokes for a session."""
    keystrokes = await keystroke_service.get_session_keystrokes(session_id)
    
    if not keystrokes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No keystrokes found for session {session_id}",
        )
    
    return {"session_id": session_id, "count": len(keystrokes), "keystrokes": keystrokes}
