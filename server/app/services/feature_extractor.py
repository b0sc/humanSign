"""Feature extraction service for ML pipeline."""

import json
from typing import Any
from uuid import UUID

import numpy as np

from app.db import get_connection, queries
from app.models import ProcessedKeystroke


# Top 20 most common English digraphs
COMMON_DIGRAPHS = [
    "th", "he", "in", "er", "an", "re", "on", "at", "en", "nd",
    "ti", "es", "or", "te", "of", "ed", "is", "it", "al", "ar",
]


class FeatureExtractor:
    """Extract ML features from keystroke data."""

    def extract_features(
        self,
        keystrokes: list[ProcessedKeystroke],
    ) -> dict[str, Any]:
        """
        Extract comprehensive features from a session's keystrokes.
        
        Returns a dictionary of features suitable for ML model input.
        """
        if not keystrokes:
            return self._empty_features()
        
        # Filter to keydown events only for most features
        keydowns = [k for k in keystrokes if k.event_type == 1]
        
        # Extract timing arrays
        dwell_times = [k.dwell_time for k in keystrokes if k.dwell_time is not None]
        flight_times = [k.flight_time for k in keydowns if k.flight_time is not None]
        
        # Basic stats
        features: dict[str, Any] = {
            "total_keystrokes": len(keydowns),
            "duration_ms": self._compute_duration(keystrokes),
        }
        
        # Dwell time features
        if dwell_times:
            features.update({
                "avg_dwell_time": float(np.mean(dwell_times)),
                "std_dwell_time": float(np.std(dwell_times)),
                "min_dwell_time": float(np.min(dwell_times)),
                "max_dwell_time": float(np.max(dwell_times)),
                "median_dwell_time": float(np.median(dwell_times)),
            })
        else:
            features.update({
                "avg_dwell_time": 0.0,
                "std_dwell_time": 0.0,
                "min_dwell_time": 0.0,
                "max_dwell_time": 0.0,
                "median_dwell_time": 0.0,
            })
        
        # Flight time features
        if flight_times:
            features.update({
                "avg_flight_time": float(np.mean(flight_times)),
                "std_flight_time": float(np.std(flight_times)),
                "min_flight_time": float(np.min(flight_times)),
                "max_flight_time": float(np.max(flight_times)),
                "median_flight_time": float(np.median(flight_times)),
            })
        else:
            features.update({
                "avg_flight_time": 0.0,
                "std_flight_time": 0.0,
                "min_flight_time": 0.0,
                "max_flight_time": 0.0,
                "median_flight_time": 0.0,
            })
        
        # WPM calculation
        features["avg_wpm"] = self._compute_wpm(keydowns, features["duration_ms"])
        
        # Error rate (backspace usage)
        backspace_count = sum(1 for k in keydowns if k.key_code == 8)
        features["error_rate"] = backspace_count / max(len(keydowns), 1)
        
        # Pause analysis (gaps > 500ms)
        pauses = [ft for ft in flight_times if ft > 500]
        features["pause_count"] = len(pauses)
        features["avg_pause_duration"] = float(np.mean(pauses)) if pauses else 0.0
        
        # Digraph features
        features["digraph_features"] = self._compute_digraphs(keydowns)
        
        return features

    def _compute_duration(self, keystrokes: list[ProcessedKeystroke]) -> float:
        """Compute session duration in milliseconds."""
        if len(keystrokes) < 2:
            return 0.0
        timestamps = [k.client_timestamp for k in keystrokes]
        return max(timestamps) - min(timestamps)

    def _compute_wpm(self, keydowns: list[ProcessedKeystroke], duration_ms: float) -> float:
        """Compute words per minute (assuming 5 chars = 1 word)."""
        if duration_ms <= 0:
            return 0.0
        chars = len([k for k in keydowns if k.key_char and k.key_char.isalnum()])
        words = chars / 5.0
        minutes = duration_ms / 60000.0
        return words / max(minutes, 0.001)

    def _compute_digraphs(
        self,
        keydowns: list[ProcessedKeystroke],
    ) -> dict[str, float]:
        """Compute average latency for common digraphs."""
        digraph_latencies: dict[str, list[float]] = {dg: [] for dg in COMMON_DIGRAPHS}
        
        for i in range(1, len(keydowns)):
            prev_char = keydowns[i - 1].key_char
            curr_char = keydowns[i].key_char
            flight_time = keydowns[i].flight_time
            
            if prev_char and curr_char and flight_time is not None:
                digraph = (prev_char + curr_char).lower()
                if digraph in digraph_latencies:
                    digraph_latencies[digraph].append(flight_time)
        
        return {
            dg: float(np.mean(times)) if times else 0.0
            for dg, times in digraph_latencies.items()
        }

    def _empty_features(self) -> dict[str, Any]:
        """Return empty features dict for sessions with no keystrokes."""
        return {
            "total_keystrokes": 0,
            "duration_ms": 0.0,
            "avg_dwell_time": 0.0,
            "std_dwell_time": 0.0,
            "min_dwell_time": 0.0,
            "max_dwell_time": 0.0,
            "median_dwell_time": 0.0,
            "avg_flight_time": 0.0,
            "std_flight_time": 0.0,
            "min_flight_time": 0.0,
            "max_flight_time": 0.0,
            "median_flight_time": 0.0,
            "avg_wpm": 0.0,
            "error_rate": 0.0,
            "pause_count": 0,
            "avg_pause_duration": 0.0,
            "digraph_features": {dg: 0.0 for dg in COMMON_DIGRAPHS},
        }

    def features_to_array(self, features: dict[str, Any]) -> np.ndarray:
        """Convert features dict to numpy array for model input."""
        # Fixed order of numeric features
        numeric_features = [
            features["total_keystrokes"],
            features["duration_ms"],
            features["avg_dwell_time"],
            features["std_dwell_time"],
            features["min_dwell_time"],
            features["max_dwell_time"],
            features["median_dwell_time"],
            features["avg_flight_time"],
            features["std_flight_time"],
            features["min_flight_time"],
            features["max_flight_time"],
            features["median_flight_time"],
            features["avg_wpm"],
            features["error_rate"],
            features["pause_count"],
            features["avg_pause_duration"],
        ]
        
        # Add digraph features in fixed order
        for dg in COMMON_DIGRAPHS:
            numeric_features.append(features["digraph_features"].get(dg, 0.0))
        
        return np.array([numeric_features], dtype=np.float32)


# Singleton instance
feature_extractor = FeatureExtractor()
