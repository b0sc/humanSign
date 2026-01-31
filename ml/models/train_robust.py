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
    Augment dataset with speed variations to improve robustness.
    Generates 3 augmented copies for every sample:
    1. Fast mode (0.8x timings)
    2. Slow mode (1.2x timings)
    3. Noise mode (random scale 0.9-1.1)
    """
    print(f"Original dataset shape: {df.shape}")
    
    augmented_rows = []
    
    # Identify column groups
    all_timing_cols = [col for col in df.columns if any(x in col for x in ['hold', 'dd', 'ud', 'flight', 'latency', 'rhythm', 'tempo'])]
    
    hold_cols = [c for c in all_timing_cols if 'hold' in c]
    flight_cols = [c for c in all_timing_cols if c not in hold_cols]
    
    print(f"Augmenting {len(hold_cols)} Hold features (Conservative) and {len(flight_cols)} Flight features (Aggressive)...")
    
    for _, row in df.iterrows():
        # 1. Conservative Hold Augmentation (0.8x - 1.2x)
        # 2. Aggressive Flight Augmentation (0.4x - 2.5x) - Simulate Free Text Variance
        
        # We create multiple "Possible Worlds" for each user sample
        
        # Scenario A: user matches speed, text is VERY different (Flight varies wildy)
        for flight_scale in [0.4, 0.6, 1.5, 2.0, 2.5]:
            row_aug = row.copy()
            # Hold stays mostly same (small jitter)
            for c in hold_cols:
                if isinstance(row[c], (int, float)):
                    row_aug[c] = row[c] * np.random.uniform(0.9, 1.1)
            # Flight changes drastically
            for c in flight_cols:
                if isinstance(row[c], (int, float)):
                    row_aug[c] = row[c] * flight_scale
            augmented_rows.append(row_aug)

        # Scenario B: User types faster/slower overall (Both change)
        for global_scale in [0.7, 0.8, 1.2, 1.3]:
            row_aug = row.copy()
            for c in all_timing_cols:
                if isinstance(row[c], (int, float)):
                    row_aug[c] = row[c] * global_scale
            augmented_rows.append(row_aug)
            
        # Scenario C: Just Random Noise (Robustness)
        for _ in range(3):
            row_aug = row.copy()
            for c in hold_cols:
                if isinstance(row[c], (int, float)):
                    row_aug[c] = row[c] * np.random.uniform(0.85, 1.15)
            for c in flight_cols:
                if isinstance(row[c], (int, float)):
                    row_aug[c] = row[c] * np.random.uniform(0.5, 1.5) # High noise on flight
            augmented_rows.append(row_aug)
    
    # Create DataFrame from augmented rows
    df_aug = pd.DataFrame(augmented_rows)
    
    # Combine original and augmented
    df_final = pd.concat([df, df_aug], ignore_index=True)
    
    print(f"Augmented dataset shape: {df_final.shape}")
    return df_final

def train_robust_model():
    """Train XGBoost model with text-agnostic augmentation."""
    
    # Load data
    df = pd.read_csv(DATASET_PATH)
    
    # Augment data
    df = augment_data(df)
    
    # Prepare features and target
    TARGET_COL = "subject"
    DROP_COLUMNS = ["subject", "sessionIndex", "rep"]
    
    X = df.drop(columns=DROP_COLUMNS)
    y = df[TARGET_COL]
    
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
    print("Training Weighted Robust XGBoost model...")
    # Using max_depth=4 as a sweet spot between Generalist(3) and Specialist(5)
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
    train_robust_model()
