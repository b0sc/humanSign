from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "ml" / "models" / "humansign_phase1_final_dataset.csv"

def augment_data(df):
    """Augment dataset with speed and jitter variations."""
    print(f"Original dataset shape: {df.shape}")
    
    augmented_rows = []
    
    # Identify timing columns (features starting with hold, dd, ud, flight, latency)
    timing_cols = [col for col in df.columns if any(x in col for x in ['hold', 'dd', 'ud', 'flight', 'latency'])]
    
    print(f"Augmenting {len(timing_cols)} timing features...")
    
    for _, row in df.iterrows():
        # Aggressive speed variations
        variations = [0.5, 0.6, 0.7, 0.8, 1.2, 1.3, 1.4, 1.5]
        
        for scale in variations:
            row_aug = row.copy()
            for col in timing_cols:
                if isinstance(row[col], (int, float)):
                    row_aug[col] = row[col] * scale
            augmented_rows.append(row_aug)
        
        # Jitter
        for _ in range(3): # increased jitter samples
            row_jitter = row.copy()
            noise = np.random.uniform(0.85, 1.15)
            for col in timing_cols:
                if isinstance(row[col], (int, float)):
                    row_jitter[col] = row[col] * noise
            augmented_rows.append(row_jitter)
    
    df_aug = pd.DataFrame(augmented_rows)
    df_final = pd.concat([df, df_aug], ignore_index=True)
    
    print(f"Augmented dataset shape: {df_final.shape}")
    return df_final

def train_hold_only_model():
    """Train XGBoost model on DWELL TIME features only."""
    
    # Load data
    df = pd.read_csv(DATASET_PATH)
    
    # Augment data
    df = augment_data(df)
    
    # Prepare features and target
    TARGET_COL = "subject"
    DROP_META = ["subject", "sessionIndex", "rep"]
    
    # CRITICAL: Drop ALL flight time features
    # We remove anything with dd, ud, rhythm, tempo
    # We only keep 'hold_' and maybe global variance if it isn't dd based
    
    # Get all features
    all_features = [c for c in df.columns if c not in DROP_META]
    
    # Keep only hold features
    KEEP_FEATURES = [c for c in all_features if 'hold' in c]
    
    print(f"Selected Hold-Only features: {KEEP_FEATURES}")
    
    X = df[KEEP_FEATURES]
    y = df[TARGET_COL]
    
    print(f"Using {X.shape[1]} features")
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    
    print(f"Train X: {X_train.shape}")
    print(f"Test X: {X_test.shape}")
    
    # Train model
    print("Training Hold-Only Model...")
    model = XGBClassifier(
        n_estimators=1000, 
        max_depth=4,
        learning_rate=0.03,
        subsample=0.7,
        colsample_bytree=0.7,
        gamma=2,
        min_child_weight=3,
        alpha=0.5,
        lambda_=1.0, 
        random_state=42,
        n_jobs=-1,
        objective="multi:softprob",
        eval_metric="mlogloss"
    )
    model.fit(X_train, y_train)
    print("✓ Model training completed")
    
    # Save artifacts
    ARTIFACT_DIR = PROJECT_ROOT / "ml" / "models" / "artifacts"
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    
    joblib.dump(model, ARTIFACT_DIR / "humansign_model.pkl")
    joblib.dump(label_encoder, ARTIFACT_DIR / "label_encoder.pkl")
    joblib.dump(X.columns.tolist(), ARTIFACT_DIR / "feature_list.pkl")
    
    print(f"✓ Model artifacts saved to {ARTIFACT_DIR}")
    
    # Evaluate
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    print(f"Training Accuracy: {train_score:.4f}")
    print(f"Testing Accuracy: {test_score:.4f}")
    
    return model

if __name__ == "__main__":
    train_hold_only_model()
