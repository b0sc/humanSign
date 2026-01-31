"""
Data Quality Analysis - Find and fix issues
"""
import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATASET_PATH = PROJECT_ROOT / "ml" / "models" / "humansign_phase1_final_dataset.csv"

df = pd.read_csv(DATASET_PATH)

print("=" * 80)
print("DATA QUALITY ANALYSIS")
print("=" * 80)

# 1. Basic statistics
print("\n1. DATASET OVERVIEW")
print("-" * 80)
print(f"Total rows: {len(df)}")
print(f"Total columns: {len(df.columns)}")
print(f"Unique subjects: {df['subject'].nunique()}")
print(f"Samples per subject: {len(df) // df['subject'].nunique()}")

# 2. Missing values
print("\n2. MISSING VALUES")
print("-" * 80)
missing = df.isnull().sum()
if missing.sum() == 0:
    print("✓ No missing values detected")
else:
    print(missing[missing > 0])

# 3. Feature ranges
print("\n3. FEATURE VALUE RANGES")
print("-" * 80)
feature_cols = df.columns[3:]
for col in feature_cols:
    min_val = df[col].min()
    max_val = df[col].max()
    mean_val = df[col].mean()
    std_val = df[col].std()
    print(f"{col:25s} | min: {min_val:8.4f} | max: {max_val:8.4f} | mean: {mean_val:8.4f} | std: {std_val:8.4f}")

# 4. Detect outliers using IQR
print("\n4. OUTLIER DETECTION (IQR method)")
print("-" * 80)
outlier_counts = {}
for col in feature_cols:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    outliers = len(df[(df[col] < lower_bound) | (df[col] > upper_bound)])
    if outliers > 0:
        outlier_counts[col] = outliers

if outlier_counts:
    print("Outliers found in:")
    for col, count in sorted(outlier_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(df)) * 100
        print(f"  {col:25s}: {count:4d} outliers ({pct:5.2f}%)")
else:
    print("✓ No outliers detected")

# 5. Subject balance
print("\n5. SUBJECT DISTRIBUTION")
print("-" * 80)
subject_counts = df['subject'].value_counts()
print(f"Subjects with data:")
print(f"  Min samples: {subject_counts.min()}")
print(f"  Max samples: {subject_counts.max()}")
print(f"  Mean samples: {subject_counts.mean():.0f}")
print(f"  Balance: {'✓ Balanced' if subject_counts.std() < 10 else '✗ Imbalanced'}")

# 6. Feature correlation
print("\n6. FEATURE STATISTICS")
print("-" * 80)
stats = df[feature_cols].describe()
print("\nVariance analysis:")
for col in feature_cols:
    variance = df[col].var()
    mean = df[col].mean()
    cv = (np.sqrt(variance) / mean) * 100  # Coefficient of variation
    print(f"{col:25s} | variance: {variance:10.6f} | CV: {cv:6.2f}%")

# 7. Zero and constant values
print("\n7. ZERO/CONSTANT VALUE CHECK")
print("-" * 80)
zero_cols = {}
for col in feature_cols:
    zero_count = (df[col] == 0).sum()
    if zero_count > 0:
        zero_cols[col] = zero_count

if zero_cols:
    print("Columns with zero values:")
    for col, count in zero_cols.items():
        pct = (count / len(df)) * 100
        print(f"  {col:25s}: {count:4d} zeros ({pct:5.2f}%)")
else:
    print("✓ No zero values detected")

# 8. Recommendations
print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)
print("""
✓ Data Quality Assessment Complete

Next Steps:
1. If outliers exist: Remove extreme values (>2% of data)
2. If imbalanced: Ensure equal samples per subject
3. If zero values: Investigate why and handle appropriately
4. Feature scaling: Normalize features to [0,1] range
5. Cross-validation: Use K-fold (5-10 folds) instead of single train/test split

Command to continue:
  python ml/models/train_model.py  # Retrain with new hyperparameters
""")

print("=" * 80)
