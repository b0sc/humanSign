from fastapi import APIRouter, File, UploadFile, HTTPException, status
from datetime import datetime
from app.core.config import settings
from app.schemas.verification import (
    VerificationRequest,
    VerificationResponse,
    PredictionResult,
    KeystrokeEvent,
)
from app.services.feature_extractor import FeatureExtractor
from app.services.ml import run_model
from app.services.parser import read_humansign_file, extract_jws, basic_jws_sanity_check
from app.services.crypto import verify_jws_signature
from app.services.hash import compute_sha256
from app.services.events import flatten_chain, verify_chain
from app.pipeline.pipeline import process_session

router = APIRouter(
    prefix="/api/v1",
    tags=['Verification']
)

@router.post("/verify", response_model=VerificationResponse)
async def verify_signature(request: VerificationRequest):
    """Verify keystroke dynamics of provided events."""
    try:
        # Validate keystroke events
        if not request.keystroke_events:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No keystroke events provided"
            )
        
        if len(request.keystroke_events) < 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum 5 keystroke events required"
            )
        
        # Extract features from keystroke events
        features = FeatureExtractor.extract_from_keystroke_events(
            request.keystroke_events
        )
        
        # Run ML model prediction
        ml_result = run_model(features)
        
        if ml_result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Model prediction failed: {ml_result['error']}"
            )
        
        # Extract prediction details
        prediction_data = ml_result["result"]
        ml_confidence = prediction_data["confidence"]
        prediction_class = prediction_data["prediction"]
        
        # Determine verification result based on confidence threshold
        threshold = settings.model_confidence_threshold
        verification_result = "GENUINE" if ml_confidence >= threshold else "FORGED"
        
        # Build response
        response = VerificationResponse(
            status="completed",
            verification_result=verification_result,
            ml_prediction=PredictionResult(
                prediction=prediction_class,
                confidence=ml_confidence,
                probabilities=prediction_data["probabilities"]
            ),
            confidence_score=ml_confidence,
            timestamp=datetime.now(),
            details={
                "keystroke_count": len(request.keystroke_events),
                "features_extracted": len(features),
                "threshold_used": threshold,
                "decision_logic": f"confidence ({ml_confidence:.4f}) >= threshold ({threshold})"
            }
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )


@router.post("/verify-files", response_model=VerificationResponse)
async def verify_files(document: UploadFile = File(...), humansign: UploadFile = File(...)):
    """Verify document authenticity using HumanSign file and keystroke dynamics."""
    try:
        if not document or not humansign:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both document and humansign files are required"
            )

        if document.content_type not in settings.allowed_doc_types:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported document type"
            )
        
        if not humansign.filename.endswith(settings.humansign_extension):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Invalid humansign file extension"
            )
        
        # Check file sizes
        async def get_file_size(file: UploadFile):
            contents = await file.read()
            size = len(contents)
            await file.seek(0)
            return size
        
        doc_size = await get_file_size(document)
        hs_size = await get_file_size(humansign)
        
        if doc_size > settings.max_file_size or hs_size > settings.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds limit"
            )
        
        # Process humansign file
        raw_humansign = await read_humansign_file(humansign)
        jws_token = extract_jws(raw_humansign)
        basic_jws_sanity_check(jws_token)

        verified_payload = verify_jws_signature(jws_token)

        stored_hash = verified_payload.get("document_hash")

        if not stored_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid HumanSign Payload: missing document hash"
            )

        # Verify document hash
        computed_hash = await compute_sha256(document)

        if computed_hash != stored_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PROOF FAILED: Document was modified after sealing"
            )
        
        # Extract and verify event chain
        chain = verified_payload.get("chain")
        if not chain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing event chain"
            )
        
        verify_chain(chain)
        
        events = flatten_chain(chain)
        
        # Use the pipeline to extract and aggregate features from events
        subject = verified_payload.get("subject", "unknown")
        session_index = verified_payload.get("sessionIndex", 0)
        rep = verified_payload.get("rep")
        
        features = process_session(
            events=events,
            subject=subject,
            session_index=session_index,
            rep=rep
        )
        
        # Debug: Log extracted features
        print(f"\n=== FEATURE EXTRACTION DEBUG ===")
        print(f"Total events: {len(events)}")
        print(f"Subject: {subject}, Session: {session_index}")
        print(f"All features: {features}")
        print(f"Feature keys: {list(features.keys())}")
        print(f"Feature values: {[(k, v) for k, v in features.items()]}")
        
        # Remove metadata fields from features dict, keep only ML features
        ml_features = {k: v for k, v in features.items() if k not in ["subject", "sessionIndex", "rep"]}
        
        # Filter to only features that were used in training (exactly 25 features)
        training_feature_names = [
            'hold_mean', 'hold_std', 'hold_cv', 'hold_min', 'hold_max', 'hold_skew',
            'dd_mean', 'dd_std', 'dd_median', 'dd_iqr', 'dd_variance',
            'ud_mean', 'ud_std', 'ud_median', 'ud_iqr', 'ud_variance',
            'intra_session_variance', 'rhythm_stability', 'tempo_consistency',
            'early_late_hold_delta', 'early_late_dd_delta', 'early_late_ud_delta',
            'hold_outlier_rate', 'dd_outlier_rate', 'ud_outlier_rate'
        ]
        
        # Keep only training features (fill missing with 0)
        ml_features = {k: ml_features.get(k, 0.0) for k in training_feature_names}
        
        # Debug logging
        print(f"\n=== FILE VERIFICATION FEATURE DEBUG ===")
        print(f"Total extracted features: {len({k: v for k, v in features.items() if k not in ['subject', 'sessionIndex', 'rep']})}")
        print(f"Training features used: {len(ml_features)}")
        print(f"Subject: {subject}")
        print(f"Feature names: {list(ml_features.keys())}")
        print(f"=== END DEBUG ===\n")
        
        # Run ML model prediction
        ml_result = run_model(ml_features)
        
        if ml_result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Model prediction failed: {ml_result['error']}"
            )
        
        # Extract prediction details
        prediction_data = ml_result["result"]
        ml_confidence = prediction_data["confidence"]
        prediction_class = prediction_data["prediction"]
        
        # Determine verification result
        threshold = settings.model_confidence_threshold
        verification_result = "GENUINE" if ml_confidence >= threshold else "FORGED"
        
        # Build response
        response = VerificationResponse(
            status="completed",
            verification_result=verification_result,
            ml_prediction=PredictionResult(
                prediction=prediction_class,
                confidence=ml_confidence,
                probabilities=prediction_data["probabilities"]
            ),
            confidence_score=ml_confidence,
            timestamp=datetime.now(),
            details={
                "keystroke_count": len(events),
                "features_extracted": len(ml_features),
                "threshold_used": threshold,
                "decision_logic": f"confidence ({ml_confidence:.4f}) >= threshold ({threshold})",
                "document_hash_valid": computed_hash == stored_hash,
                "signature_valid": True,
                "subject": verified_payload.get("subject")
            }
        )
        
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File verification failed: {str(e)}"
        )