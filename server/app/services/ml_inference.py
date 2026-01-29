"""ML inference service using ONNX Runtime."""

import os
from typing import Any, Optional

import numpy as np
import onnxruntime as ort

from app.config import get_settings


class MLInferenceService:
    """Service for running ONNX model inference."""

    def __init__(self):
        self._session: Optional[ort.InferenceSession] = None
        self._settings = get_settings()

    def _load_model(self) -> None:
        """Load ONNX model into memory."""
        model_path = self._settings.onnx_model_path
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Use optimized ONNX Runtime settings
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.intra_op_num_threads = 2
        
        self._session = ort.InferenceSession(
            model_path,
            sess_options,
            providers=["CPUExecutionProvider"],
        )

    @property
    def session(self) -> ort.InferenceSession:
        """Get or create inference session."""
        if self._session is None:
            self._load_model()
        return self._session  # type: ignore

    def predict(self, features: np.ndarray) -> dict[str, Any]:
        """
        Run prediction on feature array.
        
        Args:
            features: numpy array of shape (1, num_features)
            
        Returns:
            Dict with prediction_score (0-1) and is_human boolean
        """
        try:
            input_name = self.session.get_inputs()[0].name
            outputs = self.session.run(None, {input_name: features})
            
            # Assuming binary classification with probability output
            if len(outputs) > 1:
                # XGBoost outputs [labels, probabilities]
                probabilities = outputs[1]
                score = float(probabilities[0][1])  # Probability of human class
            else:
                # Single output (probability or logit)
                score = float(outputs[0][0])
            
            return {
                "prediction_score": score,
                "is_human": score >= 0.5,
            }
            
        except Exception as e:
            # Fallback for when model isn't available
            return {
                "prediction_score": -1.0,
                "is_human": False,
                "error": str(e),
            }

    def is_model_loaded(self) -> bool:
        """Check if model is loaded and ready."""
        return self._session is not None

    def warmup(self) -> None:
        """Warm up the model with a dummy prediction."""
        try:
            dummy_features = np.zeros((1, 36), dtype=np.float32)
            self.predict(dummy_features)
        except Exception:
            pass  # Model may not exist yet


# Singleton instance
ml_inference = MLInferenceService()
