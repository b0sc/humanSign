from pathlib import Path
import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "ml"
    / "models"
    / "humansign_phase1_final_dataset.csv"
)

def train_xgboost_model():
    """Train XGBoost model for keystroke dynamics authentication."""
    
    # Load data
    df = pd.read_csv(DATASET_PATH)
    print(f"Dataset shape: {df.shape}")
    print(f"First few rows:\n{df.head()}\n")
    
    # Prepare features and target
    TARGET_COL = "subject"
    DROP_COLUMNS = ["subject", "sessionIndex", "rep"]
    
    X = df.drop(columns=DROP_COLUMNS)
    y = df[TARGET_COL]
    
    print(f"X shape: {X.shape}")
    print(f"y shape: {y.shape}")
    print(f"First 5 feature names: {X.columns[:5].tolist()}\n")
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    print(f"Number of unique subjects: {len(label_encoder.classes_)}\n")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y_encoded,
        test_size=0.2,
        random_state=42,
        stratify=y_encoded
    )
    
    print(f"Train X: {X_train.shape}")
    print(f"Test X: {X_test.shape}")
    print(f"Train y: {y_train.shape}")
    print(f"Test y: {y_test.shape}\n")
    
    # Train model with better hyperparameters for generalization
    print("Training XGBoost model with optimized hyperparameters...")
    model = XGBClassifier(
        n_estimators=1000,  # More trees
        max_depth=4,  # Shallower trees to reduce overfitting
        learning_rate=0.01,  # Lower learning rate
        subsample=0.7,  # Use 70% of samples
        colsample_bytree=0.7,  # Use 70% of features
        colsample_bylevel=0.7,
        gamma=2,  # Higher regularization
        min_child_weight=3,  # Require more samples per leaf
        alpha=0.5,  # L1 penalty
        lambda_=1.0,  # L2 penalty
        random_state=42,
        n_jobs=-1,
        objective="multi:softprob",
        eval_metric="mlogloss",
        verbosity=0
    )
    model.fit(X_train, y_train)
    print("✓ Model training completed\n")
    
    # Save artifacts
    ARTIFACT_DIR = PROJECT_ROOT / "ml" / "models" / "artifacts"
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    
    joblib.dump(model, ARTIFACT_DIR / "humansign_model.pkl")
    joblib.dump(label_encoder, ARTIFACT_DIR / "label_encoder.pkl")
    joblib.dump(X.columns.tolist(), ARTIFACT_DIR / "feature_list.pkl")
    
    print(f"✓ Model artifacts saved to {ARTIFACT_DIR}\n")
    
    # Evaluate
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    print(f"Training Accuracy: {train_score:.4f}")
    print(f"Testing Accuracy: {test_score:.4f}\n")
    
    return model


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Training HumanSign XGBoost Model")
    print("=" * 60)
    print()
    
    try:
        # Train the model
        model = train_xgboost_model()
        
        # Verify model was saved
        model_path = PROJECT_ROOT / "ml" / "models" / "artifacts" / "humansign_model.pkl"
        if model_path.exists():
            size_kb = model_path.stat().st_size / 1024
            print(f"✓ Model file size: {size_kb:.2f} KB")
            print(f"✓ Model location: {model_path}")
            print("\n" + "=" * 60)
            print("✅ Training Complete!")
            print("=" * 60)
            print("\n🚀 Start FastAPI server with:")
            print("   fastapi dev app/main.py")
            print("\n📊 Test the API with:")
            print('   curl -X POST "http://localhost:8000/api/v1/verify" \\')
            print('     -H "Content-Type: application/json" \\')
            print('     -d \'{"keystroke_events": [{"key": "a", "timestamp": 100, "duration": 50}]}\'')
            print("=" * 60)
        else:
            print(f"✗ Error: Model file not found at {model_path}")
            
    except Exception as e:
        print(f"✗ Training failed: {str(e)}")
        import traceback
        traceback.print_exc()