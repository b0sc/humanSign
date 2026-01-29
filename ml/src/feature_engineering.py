"""Feature engineering for keystroke dynamics ML model."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any


# Top 20 common English digraphs for feature extraction
COMMON_DIGRAPHS = [
    'th', 'he', 'in', 'er', 'an', 're', 'on', 'at', 'en', 'nd',
    'ti', 'es', 'or', 'te', 'of', 'ed', 'is', 'it', 'al', 'ar',
]

# Feature names for model input
FEATURE_NAMES = [
    # Basic stats (16 features)
    'total_keystrokes',
    'duration_ms',
    'avg_dwell_time',
    'std_dwell_time',
    'min_dwell_time',
    'max_dwell_time',
    'median_dwell_time',
    'avg_flight_time',
    'std_flight_time',
    'min_flight_time',
    'max_flight_time',
    'median_flight_time',
    'avg_wpm',
    'error_rate',
    'pause_count',
    'avg_pause_duration',
] + [f'digraph_{dg}' for dg in COMMON_DIGRAPHS]  # 20 digraph features

NUM_FEATURES = len(FEATURE_NAMES)


def compute_basic_stats(
    dwell_times: np.ndarray,
    flight_times: np.ndarray,
    total_keystrokes: int,
    duration_ms: float,
) -> Dict[str, float]:
    """Compute basic statistical features from timing arrays."""
    features = {
        'total_keystrokes': total_keystrokes,
        'duration_ms': duration_ms,
    }
    
    # Dwell time stats
    if len(dwell_times) > 0:
        features['avg_dwell_time'] = float(np.mean(dwell_times))
        features['std_dwell_time'] = float(np.std(dwell_times))
        features['min_dwell_time'] = float(np.min(dwell_times))
        features['max_dwell_time'] = float(np.max(dwell_times))
        features['median_dwell_time'] = float(np.median(dwell_times))
    else:
        features['avg_dwell_time'] = 0.0
        features['std_dwell_time'] = 0.0
        features['min_dwell_time'] = 0.0
        features['max_dwell_time'] = 0.0
        features['median_dwell_time'] = 0.0
    
    # Flight time stats
    if len(flight_times) > 0:
        features['avg_flight_time'] = float(np.mean(flight_times))
        features['std_flight_time'] = float(np.std(flight_times))
        features['min_flight_time'] = float(np.min(flight_times))
        features['max_flight_time'] = float(np.max(flight_times))
        features['median_flight_time'] = float(np.median(flight_times))
    else:
        features['avg_flight_time'] = 0.0
        features['std_flight_time'] = 0.0
        features['min_flight_time'] = 0.0
        features['max_flight_time'] = 0.0
        features['median_flight_time'] = 0.0
    
    return features


def compute_wpm(total_keystrokes: int, duration_ms: float) -> float:
    """Compute words per minute (assuming 5 chars = 1 word)."""
    if duration_ms <= 0:
        return 0.0
    words = total_keystrokes / 5.0
    minutes = duration_ms / 60000.0
    return words / max(minutes, 0.001)


def compute_pauses(flight_times: np.ndarray, threshold_ms: float = 500.0) -> Dict[str, float]:
    """Compute pause features (gaps > threshold)."""
    pauses = flight_times[flight_times > threshold_ms]
    return {
        'pause_count': len(pauses),
        'avg_pause_duration': float(np.mean(pauses)) if len(pauses) > 0 else 0.0,
    }


def features_to_array(features: Dict[str, Any]) -> np.ndarray:
    """Convert features dict to numpy array in fixed order."""
    values = []
    for name in FEATURE_NAMES:
        if name.startswith('digraph_'):
            dg = name[8:]  # Remove 'digraph_' prefix
            values.append(features.get('digraph_features', {}).get(dg, 0.0))
        else:
            values.append(features.get(name, 0.0))
    return np.array(values, dtype=np.float32)


def extract_features_from_session(
    dwell_times: np.ndarray,
    flight_times: np.ndarray,
    digraph_latencies: Dict[str, List[float]],
    total_keystrokes: int,
    duration_ms: float,
    error_rate: float = 0.0,
) -> Dict[str, Any]:
    """Extract all features from a session's timing data."""
    features = compute_basic_stats(dwell_times, flight_times, total_keystrokes, duration_ms)
    features['avg_wpm'] = compute_wpm(total_keystrokes, duration_ms)
    features['error_rate'] = error_rate
    features.update(compute_pauses(flight_times))
    
    # Digraph features
    digraph_features = {}
    for dg in COMMON_DIGRAPHS:
        latencies = digraph_latencies.get(dg, [])
        digraph_features[dg] = float(np.mean(latencies)) if latencies else 0.0
    features['digraph_features'] = digraph_features
    
    return features


def prepare_training_data(
    df: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Prepare features and labels from processed DataFrame.
    
    Args:
        df: DataFrame with timing columns and 'is_human' label
        
    Returns:
        X: Feature matrix (n_samples, n_features)
        y: Labels (n_samples,)
    """
    feature_rows = []
    labels = []
    
    # Get all timing columns
    dwell_cols = [c for c in df.columns if 'dwell' in c.lower()]
    flight_cols = [c for c in df.columns if 'flight' in c.lower() or 'dd' in c.lower()]
    
    for _, row in df.iterrows():
        # Extract timing arrays
        dwell_times = np.array([row[c] for c in dwell_cols if pd.notna(row[c])])
        flight_times = np.array([row[c] for c in flight_cols if pd.notna(row[c])])
        
        if len(dwell_times) < 5:
            continue
        
        # Compute features
        features = extract_features_from_session(
            dwell_times=dwell_times,
            flight_times=flight_times,
            digraph_latencies={},  # Not available in preprocessed data
            total_keystrokes=int(row.get('total_keystrokes', len(dwell_times))),
            duration_ms=float(row.get('duration_ms', np.sum(dwell_times) + np.sum(flight_times))),
            error_rate=float(row.get('error_rate', 0.0)),
        )
        
        feature_rows.append(features_to_array(features))
        labels.append(1 if row['is_human'] else 0)
    
    return np.array(feature_rows), np.array(labels)


if __name__ == '__main__':
    print(f"Feature engineering module loaded")
    print(f"Number of features: {NUM_FEATURES}")
    print(f"Feature names: {FEATURE_NAMES}")
