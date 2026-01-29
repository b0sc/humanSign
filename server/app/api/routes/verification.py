"""Verification API routes."""

from uuid import UUID
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services import keystroke_service, feature_extractor, ml_inference

router = APIRouter(prefix="/verify", tags=["verification"])


class VerificationRequest(BaseModel):
    """Request to verify a session."""
    session_id: UUID


class VerificationResult(BaseModel):
    """Verification result response."""
    session_id: UUID
    is_human: bool
    confidence_score: float
    features_summary: dict[str, float]
    computed_at: datetime


@router.post("", response_model=VerificationResult)
async def verify_session(request: VerificationRequest) -> VerificationResult:
    """
    Run ML verification on a session.
    
    Extracts features from keystroke data and runs ONNX model inference
    to determine if the typing pattern appears human or bot-generated.
    """
    # Get keystrokes
    keystrokes = await keystroke_service.get_session_keystrokes(request.session_id)
    
    if not keystrokes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No keystrokes found for session {request.session_id}",
        )
    
    if len(keystrokes) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient keystrokes for verification (minimum 10 required)",
        )
    
    # Extract features
    features = feature_extractor.extract_features(keystrokes)
    feature_array = feature_extractor.features_to_array(features)
    
    # Run inference
    prediction = ml_inference.predict(feature_array)
    
    # Build summary of key features
    features_summary = {
        "total_keystrokes": features["total_keystrokes"],
        "avg_dwell_time": round(features["avg_dwell_time"], 2),
        "avg_flight_time": round(features["avg_flight_time"], 2),
        "avg_wpm": round(features["avg_wpm"], 1),
        "error_rate": round(features["error_rate"], 4),
        "pause_count": features["pause_count"],
    }
    
    return VerificationResult(
        session_id=request.session_id,
        is_human=prediction["is_human"],
        confidence_score=max(0.0, min(1.0, prediction["prediction_score"])),
        features_summary=features_summary,
        computed_at=datetime.now(timezone.utc),
    )


@router.get("/health")
async def verification_health() -> dict[str, Any]:
    """Check if verification system is ready."""
    model_loaded = ml_inference.is_model_loaded()
    
    return {
        "status": "ready" if model_loaded else "model_not_loaded",
        "model_loaded": model_loaded,
    }
