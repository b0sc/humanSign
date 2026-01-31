"""
Debug script to compare training vs verification features
"""
import pandas as pd
import joblib
from pathlib import Path
from app.pipeline.pipeline import process_session

PROJECT_ROOT = Path(__file__).resolve().parent

# Load training data to see feature names
DATASET_PATH = PROJECT_ROOT / "ml" / "models" / "humansign_phase1_final_dataset.csv"
df = pd.read_csv(DATASET_PATH)

# Get feature names (exclude metadata columns)
DROP_COLUMNS = ["subject", "sessionIndex", "rep"]
training_features = df.drop(columns=DROP_COLUMNS).columns.tolist()

print("=" * 60)
print("TRAINING DATA FEATURES")
print("=" * 60)
print(f"Total features: {len(training_features)}")
print(f"Feature names:\n{training_features}\n")

# Load the saved feature list from model artifacts
artifacts_dir = PROJECT_ROOT / "ml" / "models" / "artifacts"
feature_list_path = artifacts_dir / "feature_list.pkl"

if feature_list_path.exists():
    saved_features = joblib.load(str(feature_list_path))
    print("=" * 60)
    print("SAVED MODEL FEATURES")
    print("=" * 60)
    print(f"Total features: {len(saved_features)}")
    print(f"Feature names:\n{saved_features}\n")
    
    # Compare
    print("=" * 60)
    print("COMPARISON")
    print("=" * 60)
    print(f"Match: {training_features == saved_features}")
    
    if training_features != saved_features:
        print("\nMISSING in saved:")
        for f in training_features:
            if f not in saved_features:
                print(f"  - {f}")
        
        print("\nEXTRA in saved:")
        for f in saved_features:
            if f not in training_features:
                print(f"  + {f}")
else:
    print("⚠ feature_list.pkl not found!")

print("\n" + "=" * 60)
print("VALID SUBJECT IDS (from training data)")
print("=" * 60)
unique_subjects = df["subject"].unique()
print(f"Total subjects: {len(unique_subjects)}")
print(f"Subject range: {sorted(unique_subjects)[:5]}...{sorted(unique_subjects)[-5:]}")
print(f"\n⚠ 'user' is NOT a valid subject!")
print(f"✓ Use subject IDs from 0-{len(unique_subjects)-1}")
