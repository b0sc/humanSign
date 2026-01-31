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
    """
    Augment dataset with speed variations.
    """
    print(f"Original dataset shape: {df.shape}")
    
    augmented_rows = []
    
    # Identify timing columns
    timing_cols = [col for col in df.columns if any(x in col for x in ['hold', 'dd', 'ud', 'flight', 'latency'])]
    
    print(f"Augmenting {len(timing_cols)} timing features...")
    
    for _, row in df.iterrows():
        # Wide range of speed variations (0.5x to 1.5x)
        variations = [0.5, 0.6, 0.8, 1.2, 1.4, 1.5]
        
        for scale in variations:
            row_aug = row.copy()
            for col in timing_cols:
                if isinstance(row[col], (int, float)):
                    row_aug[col] = row[col] * scale
            augmented_rows.append(row_aug)
        
        # Random Jitter
        for _ in range(2):
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

def train_generalist_model():
    """Train XGBoost model on ROBUST features only."""
    
    # Load data
    df = pd.read_csv(DATASET_PATH)
    
    # Augment data first (while we have all columns)
    df = augment_data(df)
    
    # Prepare features and target
    TARGET_COL = "subject"
    DROP_META = ["subject", "sessionIndex", "rep"]
    
    # CRITICAL: Drop text-dependent features (absolute flight speeds)
    # We keep Dwell (Hold) features as they are text-independent.
    # We keep Variance/Std features as they represent consistency/skill.
    # we DROP dd_mean, dd_median, ud_mean, ud_median
    DROP_FEATURES = ['dd_mean', 'dd_median', 'ud_mean', 'ud_median']
    
    print(f"Dropping text-dependent features: {DROP_FEATURES}")
    
    X = df.drop(columns=DROP_META + DROP_FEATURES, errors='ignore')
    y = df[TARGET_COL]
    
    print(f"Using {X.shape[1]} features: {X.columns.tolist()}")
    
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
    print("Training Generalist XGBoost model...")
    model = XGBClassifier(
        n_estimators=1000, 
        max_depth=4,       
        learning_rate=0.03,
        subsample=0.7,     
        colsample_bytree=0.7,
        gamma=3,           
        min_child_weight=5,
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
    train_generalist_model()
