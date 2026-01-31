"""
Train model with K-fold cross-validation for better generalization
"""
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import StratifiedKFold
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

PROJECT_ROOT = Path(__file__).resolve().parent

DATASET_PATH = (
    PROJECT_ROOT
    / "ml"
    / "models"
    / "humansign_phase1_final_dataset.csv"
)

def train_xgboost_with_kfold():
    """Train XGBoost model with K-fold cross-validation."""
    
    # Load data
    df = pd.read_csv(DATASET_PATH)
    print(f"Dataset shape: {df.shape}")
    
    # Prepare features and target
    TARGET_COL = "subject"
    DROP_COLUMNS = ["subject", "sessionIndex", "rep"]
    
    X = df.drop(columns=DROP_COLUMNS)
    y = df[TARGET_COL]
    
    print(f"X shape: {X.shape}")
    print(f"Number of unique subjects: {y.nunique()}\n")
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    # Setup K-fold cross-validation
    kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    print("=" * 80)
    print("K-FOLD CROSS-VALIDATION (5 Folds)")
    print("=" * 80)
    
    fold_results = []
    best_model = None
    best_accuracy = 0
    
    for fold, (train_idx, test_idx) in enumerate(kfold.split(X, y_encoded), 1):
        print(f"\nFold {fold}/5")
        print("-" * 80)
        
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y_encoded[train_idx], y_encoded[test_idx]
        
        print(f"Train: {X_train.shape}, Test: {X_test.shape}")
        
        # Train model
        model = XGBClassifier(
            n_estimators=1000,
            max_depth=4,
            learning_rate=0.01,
            subsample=0.7,
            colsample_bytree=0.7,
            colsample_bylevel=0.7,
            gamma=2,
            min_child_weight=3,
            alpha=0.5,
            lambda_=1.0,
            random_state=42,
            n_jobs=-1,
            objective="multi:softprob",
            eval_metric="mlogloss",
            verbosity=0
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        fold_results.append({
            'fold': fold,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1
        })
        
        print(f"Accuracy:  {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall:    {recall:.4f}")
        print(f"F1-Score:  {f1:.4f}")
        
        # Keep best model
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_model = model
    
    # Summary
    print("\n" + "=" * 80)
    print("CROSS-VALIDATION SUMMARY")
    print("=" * 80)
    
    results_df = pd.DataFrame(fold_results)
    print(f"\nMean Accuracy:  {results_df['accuracy'].mean():.4f} (+/- {results_df['accuracy'].std():.4f})")
    print(f"Mean Precision: {results_df['precision'].mean():.4f} (+/- {results_df['precision'].std():.4f})")
    print(f"Mean Recall:    {results_df['recall'].mean():.4f} (+/- {results_df['recall'].std():.4f})")
    print(f"Mean F1-Score:  {results_df['f1'].mean():.4f} (+/- {results_df['f1'].std():.4f})")
    
    # Retrain on full dataset with best model config
    print(f"\nRetraining on full dataset with best hyperparameters...")
    final_model = XGBClassifier(
        n_estimators=1000,
        max_depth=4,
        learning_rate=0.01,
        subsample=0.7,
        colsample_bytree=0.7,
        colsample_bylevel=0.7,
        gamma=2,
        min_child_weight=3,
        alpha=0.5,
        lambda_=1.0,
        random_state=42,
        n_jobs=-1,
        objective="multi:softprob",
        eval_metric="mlogloss",
        verbosity=0
    )
    
    final_model.fit(X, y_encoded)
    
    # Save artifacts
    ARTIFACT_DIR = PROJECT_ROOT / "ml" / "models" / "artifacts"
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    
    joblib.dump(final_model, str(ARTIFACT_DIR / "humansign_model.pkl"))
    joblib.dump(label_encoder, str(ARTIFACT_DIR / "label_encoder.pkl"))
    joblib.dump(X.columns.tolist(), str(ARTIFACT_DIR / "feature_list.pkl"))
    
    print("✓ Model artifacts saved successfully")
    print(f"  - Model: {ARTIFACT_DIR / 'humansign_model.pkl'}")
    print(f"  - Encoder: {ARTIFACT_DIR / 'label_encoder.pkl'}")
    print(f"  - Features: {ARTIFACT_DIR / 'feature_list.pkl'}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    train_xgboost_with_kfold()
