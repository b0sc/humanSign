"""Model evaluation utilities."""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
import json

import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    roc_curve,
    confusion_matrix,
    classification_report,
)

from feature_engineering import FEATURE_NAMES


def evaluate_model(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray,
) -> Dict[str, float]:
    """Compute comprehensive evaluation metrics."""
    return {
        'accuracy': accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred),
        'recall': recall_score(y_true, y_pred),
        'f1': f1_score(y_true, y_pred),
        'roc_auc': roc_auc_score(y_true, y_proba),
    }


def plot_roc_curve(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    output_path: Path,
) -> None:
    """Plot and save ROC curve."""
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    auc = roc_auc_score(y_true, y_proba)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, 'b-', label=f'ROC (AUC = {auc:.3f})')
    plt.plot([0, 1], [0, 1], 'k--', label='Random')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve - Human vs Bot Classification')
    plt.legend(loc='lower right')
    plt.grid(True, alpha=0.3)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"ROC curve saved to: {output_path}")


def plot_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    output_path: Path,
) -> None:
    """Plot and save confusion matrix."""
    cm = confusion_matrix(y_true, y_pred)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='Blues',
        xticklabels=['Bot', 'Human'],
        yticklabels=['Bot', 'Human'],
    )
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title('Confusion Matrix')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Confusion matrix saved to: {output_path}")


def plot_feature_importance(
    model,
    output_path: Path,
    top_n: int = 20,
) -> None:
    """Plot feature importance from XGBoost model."""
    importance = model.feature_importances_
    
    # Get top N features
    indices = np.argsort(importance)[-top_n:]
    top_features = [FEATURE_NAMES[i] for i in indices]
    top_importance = importance[indices]
    
    plt.figure(figsize=(10, 8))
    plt.barh(range(len(top_features)), top_importance)
    plt.yticks(range(len(top_features)), top_features)
    plt.xlabel('Feature Importance (Gain)')
    plt.title(f'Top {top_n} Important Features')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Feature importance saved to: {output_path}")


def generate_report(
    metrics: Dict[str, float],
    output_path: Path,
) -> None:
    """Generate evaluation report."""
    report = {
        'metrics': metrics,
        'interpretation': {
            'accuracy': f"Model correctly classifies {metrics['accuracy']*100:.1f}% of samples",
            'roc_auc': f"AUC of {metrics['roc_auc']:.3f} indicates {'excellent' if metrics['roc_auc'] > 0.9 else 'good' if metrics['roc_auc'] > 0.8 else 'moderate'} discrimination",
            'precision': f"When predicting human, correct {metrics['precision']*100:.1f}% of the time",
            'recall': f"Detects {metrics['recall']*100:.1f}% of actual human typing",
        },
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Evaluation report saved to: {output_path}")


if __name__ == '__main__':
    print("Evaluation module loaded successfully")
