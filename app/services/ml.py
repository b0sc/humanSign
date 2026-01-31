import sys
from pathlib import Path
from typing import Dict, Any
import numpy as np
import joblib

# Add ML root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = PROJECT_ROOT / "ml"
sys.path.insert(0, str(ML_ROOT))

class MLModelManager:
    """Manages ML model loading and inference (Singleton pattern)."""
    
    _instance = None
    _model = None
    _label_encoder = None
    _feature_list = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_artifacts()
        return cls._instance
    
    def _load_artifacts(self):
        """Load the trained XGBoost model and related artifacts."""
        artifacts_dir = ML_ROOT / "models" / "artifacts"
        
        # Load model
        model_path = artifacts_dir / "humansign_model.pkl"
        if model_path.exists():
            try:
                self._model = joblib.load(str(model_path))
                print(f"✓ XGBoost model loaded")
            except Exception as e:
                print(f"✗ Error loading model: {e}")
                self._model = None
        else:
            print(f"⚠ Model not found at {model_path}")
            self._model = None
        
        # Load label encoder
        encoder_path = artifacts_dir / "label_encoder.pkl"
        if encoder_path.exists():
            try:
                self._label_encoder = joblib.load(str(encoder_path))
                print(f"✓ Label encoder loaded")
            except Exception as e:
                print(f"✗ Error loading label encoder: {e}")
        
        # Load feature list
        feature_path = artifacts_dir / "feature_list.pkl"
        if feature_path.exists():
            try:
                self._feature_list = joblib.load(str(feature_path))
                print(f"✓ Feature list loaded")
            except Exception as e:
                print(f"✗ Error loading feature list: {e}")
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None
    
    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Run inference on input features.
        
        Args:
            features: Dictionary of engineered features
            
        Returns:
            Prediction result with confidence
        """
        if self._model is None:
            raise RuntimeError("Model not loaded. Run: python ml/models/train_model.py")
        
        try:
            # Convert features dict to array in consistent order
            if self._feature_list:
                # Use the saved feature order
                feature_array = np.array([[features.get(name, 0) for name in self._feature_list]])
                print(f"[ML Service] Using {len(self._feature_list)} features from saved list")
                print(f"[ML Service] Provided features: {len(features)}")
                print(f"[ML Service] Saved feature order: {self._feature_list}")
                print(f"[ML Service] Feature array shape: {feature_array.shape}")
            else:
                # Fallback: use sorted keys
                feature_names = sorted(features.keys())
                feature_array = np.array([[features[name] for name in feature_names]])
                print(f"[ML Service] Using fallback with {len(feature_names)} features")
            
            # Get prediction and probability
            prediction = self._model.predict(feature_array)
            probabilities = self._model.predict_proba(feature_array)
            
            # Get the predicted class and confidence
            pred_class = int(prediction[0])
            confidence = float(max(probabilities[0]))
            
            return {
                "prediction": pred_class,
                "confidence": confidence,
                "probabilities": {
                    f"class_{i}": float(prob) 
                    for i, prob in enumerate(probabilities[0])
                }
            }
        except Exception as e:
            raise RuntimeError(f"Prediction failed: {str(e)}")

# Global model instance (loads once on startup)
model_manager = MLModelManager()

def run_model(input_features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process features through ML pipeline and get predictions.
    
    Args:
        input_features: Dictionary containing keystroke dynamics features
        
    Returns:
        Prediction results
    """
    try:
        # Run prediction
        result = model_manager.predict(input_features)
        
        return {
            "status": "success",
            "result": result,
            "features_used": len(input_features)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }