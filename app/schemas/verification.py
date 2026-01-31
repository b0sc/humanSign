from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class KeystrokeEvent(BaseModel):
    """Represents a single keystroke event."""
    key: str
    timestamp: float = Field(..., description="Timestamp in milliseconds")
    duration: float = Field(..., description="Key press duration in milliseconds")
    pressure: Optional[float] = Field(None, description="Key pressure (0-1)")

class VerificationRequest(BaseModel):
    """Request body for document verification."""
    keystroke_events: List[KeystrokeEvent]
    document_hash: Optional[str] = None
    signature: Optional[str] = None

class PredictionResult(BaseModel):
    """ML prediction result."""
    prediction: int = Field(..., description="0=Forged, 1=Genuine")
    confidence: float = Field(..., description="Confidence score 0-1")
    probabilities: Dict[str, float]

class VerificationResponse(BaseModel):
    """Response for verification endpoint."""
    status: str
    verification_result: str
    ml_prediction: PredictionResult
    confidence_score: float
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None