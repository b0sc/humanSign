"""XGBoost training script for keystroke dynamics classification."""

import argparse
import json
from pathlib import Path
from datetime import datetime

import numpy as np
import xgboost as xgb
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
import joblib

from preprocessing import load_dsn_2009, clean_timing_data, split_data, create_synthetic_bot_data
from feature_engineering import prepare_training_data, NUM_FEATURES


def train_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    params: dict = None,
) -> xgb.XGBClassifier:
    """
    Train XGBoost classifier for human vs bot detection.
    """
    default_params = {
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 200,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42,
        'use_label_encoder': False,
    }
    
    if params:
        default_params.update(params)
    
    model = xgb.XGBClassifier(**default_params)
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=True,
    )
    
    return model


def evaluate_model(
    model: xgb.XGBClassifier,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> dict:
    """Evaluate model on test set."""
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'roc_auc': roc_auc_score(y_test, y_proba),
    }
    
    print("\n=== Test Set Evaluation ===")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"ROC AUC:  {metrics['roc_auc']:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Bot', 'Human']))
    
    return metrics


def save_model(model: xgb.XGBClassifier, output_dir: Path, metrics: dict) -> None:
    """Save trained model and metadata."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save XGBoost model
    model_path = output_dir / 'keystroke_model.json'
    model.save_model(model_path)
    print(f"Model saved to: {model_path}")
    
    # Save sklearn wrapper for ONNX export
    joblib_path = output_dir / 'keystroke_model.joblib'
    joblib.dump(model, joblib_path)
    print(f"Joblib model saved to: {joblib_path}")
    
    # Save metadata
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'num_features': NUM_FEATURES,
        'metrics': metrics,
        'params': model.get_params(),
    }
    
    metadata_path = output_dir / 'model_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to: {metadata_path}")


def main():
    parser = argparse.ArgumentParser(description='Train XGBoost keystroke dynamics model')
    parser.add_argument('--data-dir', type=Path, default=Path('data'),
                        help='Directory containing training data')
    parser.add_argument('--output-dir', type=Path, default=Path('models'),
                        help='Directory to save trained model')
    parser.add_argument('--synthetic-ratio', type=float, default=1.0,
                        help='Ratio of synthetic bot samples to human samples')
    args = parser.parse_args()
    
    print("=== HumanSign Model Training ===\n")
    
    # Check for data files
    data_files = list(args.data_dir.glob('*.csv'))
    
    if not data_files:
        print(f"No data files found in {args.data_dir}")
        print("Creating synthetic training data for demonstration...")
        
        # Create synthetic demo data
        np.random.seed(42)
        n_samples = 1000
        
        # Simulate human typing patterns
        human_data = {
            'subject': [f'human_{i}' for i in range(n_samples)],
            'session': [1] * n_samples,
            'is_human': [True] * n_samples,
            'dwell_avg': np.random.normal(100, 30, n_samples),  # ~100ms avg hold
            'flight_avg': np.random.normal(80, 40, n_samples),   # ~80ms avg flight
            'total_keystrokes': np.random.randint(50, 500, n_samples),
            'duration_ms': np.random.uniform(5000, 60000, n_samples),
            'error_rate': np.random.beta(2, 20, n_samples),
        }
        
        # Simulate bot typing patterns (more uniform)
        bot_data = {
            'subject': [f'bot_{i}' for i in range(n_samples)],
            'session': [1] * n_samples,
            'is_human': [False] * n_samples,
            'dwell_avg': np.random.normal(90, 5, n_samples),   # Very uniform
            'flight_avg': np.random.normal(75, 5, n_samples),   # Very uniform  
            'total_keystrokes': np.random.randint(50, 500, n_samples),
            'duration_ms': np.random.uniform(5000, 60000, n_samples),
            'error_rate': np.random.beta(1, 50, n_samples),  # Fewer errors
        }
        
        import pandas as pd
        human_df = pd.DataFrame(human_data)
        bot_df = pd.DataFrame(bot_data)
        df = pd.concat([human_df, bot_df], ignore_index=True)
        
    else:
        print(f"Found data files: {[f.name for f in data_files]}")
        # Load and process real data
        import pandas as pd
        dfs = [load_dsn_2009(f) for f in data_files]
        df = pd.concat(dfs, ignore_index=True)
        df = clean_timing_data(df)
        
        # Add synthetic bot data
        n_human = len(df[df['is_human'] == True])
        n_bots = int(n_human * args.synthetic_ratio)
        bot_df = create_synthetic_bot_data(df[df['is_human'] == True], n_bots)
        df = pd.concat([df, bot_df], ignore_index=True)
    
    print(f"Total samples: {len(df)}")
    print(f"Human samples: {len(df[df['is_human'] == True])}")
    print(f"Bot samples: {len(df[df['is_human'] == False])}")
    
    # Split data
    train_df, val_df, test_df = split_data(df)
    print(f"\nSplit: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    
    # Prepare features
    X_train, y_train = prepare_training_data(train_df)
    X_val, y_val = prepare_training_data(val_df)
    X_test, y_test = prepare_training_data(test_df)
    
    print(f"Feature shape: {X_train.shape}")
    
    # Train model
    print("\n=== Training XGBoost Model ===")
    model = train_model(X_train, y_train, X_val, y_val)
    
    # Evaluate
    metrics = evaluate_model(model, X_test, y_test)
    
    # Save
    save_model(model, args.output_dir, metrics)
    
    print("\n=== Training Complete ===")
    print(f"Run 'python export_onnx.py' to export to ONNX format")


if __name__ == '__main__':
    main()
