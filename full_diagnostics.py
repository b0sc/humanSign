"""
Complete diagnostics to understand model state
"""
import joblib
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent

print("=" * 80)
print("COMPREHENSIVE MODEL DIAGNOSTICS")
print("=" * 80)

# 1. Check training data
DATASET_PATH = PROJECT_ROOT / "ml" / "models" / "humansign_phase1_final_dataset.csv"
df = pd.read_csv(DATASET_PATH)

print("\n1. TRAINING DATA STRUCTURE")
print("-" * 80)
print(f"Total rows: {len(df)}")
print(f"Total columns: {len(df.columns)}")
print(f"Column names ({len(df.columns)}):")
for i, col in enumerate(df.columns, 1):
    print(f"  {i:2d}. {col}")

print(f"\nUnique subjects: {df['subject'].nunique()}")
print(f"Subject list: {sorted(df['subject'].unique())}")
print(f"Subject data type: {df['subject'].dtype}")

# 2. Check saved artifacts
artifacts_dir = PROJECT_ROOT / "ml" / "models" / "artifacts"

print("\n2. SAVED MODEL ARTIFACTS")
print("-" * 80)

# Check model
model_path = artifacts_dir / "humansign_model.pkl"
if model_path.exists():
    model = joblib.load(str(model_path))
    print(f"✓ Model file exists: {model_path}")
    print(f"  Model type: {type(model).__name__}")
    print(f"  Model classes: {model.classes_}")
    print(f"  Number of classes: {len(model.classes_)}")
else:
    print(f"✗ Model file NOT found: {model_path}")

# Check label encoder
encoder_path = artifacts_dir / "label_encoder.pkl"
if encoder_path.exists():
    encoder = joblib.load(str(encoder_path))
    print(f"\n✓ Label encoder exists: {encoder_path}")
    print(f"  Encoder classes: {encoder.classes_}")
    print(f"  Number of classes: {len(encoder.classes_)}")
else:
    print(f"\n✗ Label encoder NOT found: {encoder_path}")

# Check features
feature_path = artifacts_dir / "feature_list.pkl"
if feature_path.exists():
    features = joblib.load(str(feature_path))
    print(f"\n✓ Feature list exists: {feature_path}")
    print(f"  Features: {features}")
    print(f"  Number of features: {len(features)}")
else:
    print(f"\n✗ Feature list NOT found: {feature_path}")

# 3. Expected features from training data
print("\n3. EXPECTED TRAINING FEATURES")
print("-" * 80)
DROP_COLUMNS = ["subject", "sessionIndex", "rep"]
X = df.drop(columns=DROP_COLUMNS)
print(f"Expected features ({len(X.columns)}):")
for i, col in enumerate(X.columns, 1):
    print(f"  {i:2d}. {col}")

# 4. Data quality check
print("\n4. DATA QUALITY CHECK")
print("-" * 80)
print(f"Missing values:\n{df.isnull().sum()}")
print(f"\nFeature statistics (first 5):")
print(X.iloc[:, :5].describe())

# 5. Subject distribution
print("\n5. SUBJECT DISTRIBUTION")
print("-" * 80)
subject_counts = df['subject'].value_counts().sort_index()
print(subject_counts)

print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)
print("""
1. SUBJECT ISSUE:
   - Training subjects are: s002, s003, s004, ... (string format)
   - Your test uses "user" which is NOT in the training data
   - FIX: Use a valid subject like "s002" or "s015" in your test

2. FEATURE COUNT:
   - Training expects: 25 features (from CSV columns 4-28)
   - You're sending: 31 features
   - FIX: Ensure feature filtering is applied correctly

3. MODEL QUALITY:
   - Test accuracy from training: ~88%
   - Current verification accuracy: 28%
   - REASON: Wrong subject + feature mismatch
   - FIX: Use correct subject + exact 25 features

4. NEXT STEPS:
   a) Verify feature filtering is working (should be 25, not 31)
   b) Test with "s002" or another valid subject
   c) Check API logs for feature extraction output
   d) If still low, retrain with hyperparameter optimization
""")

print("=" * 80)
