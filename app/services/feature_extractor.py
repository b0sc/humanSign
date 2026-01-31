from typing import Dict, List, Any
from app.schemas.verification import KeystrokeEvent

class FeatureExtractor:
    """Extracts keystroke dynamics features from raw keystroke data."""
    
    @staticmethod
    def extract_from_keystroke_events(events: List[KeystrokeEvent]) -> Dict[str, Any]:
        """
        Extract ML features from keystroke events.
        
        Args:
            events: List of keystroke timing events
            
        Returns:
            Dictionary of extracted features matching training dataset
        """
        from app.pipeline.aggregate import aggregate_features

        if not events:
            raise ValueError("No keystroke events provided")
        
        # Sort events by timestamp just in case
        events = sorted(events, key=lambda x: x.timestamp)
        
        # 1. Extract raw timing sequences
        hold_times = []
        dd_times = []
        ud_times = []
        
        for i in range(len(events)):
            current_event = events[i]
            
            # Hold time (Dwell)
            if current_event.duration > 0:
                hold_times.append(current_event.duration)
            
            # Latencies (requires next event)
            if i < len(events) - 1:
                next_event = events[i + 1]
                
                # Down-Down: Time from current Press to next Press
                dd_val = next_event.timestamp - current_event.timestamp
                dd_times.append(dd_val)
                
                # Up-Down: Time from current Release (timestamp+duration) to next Press
                # Note: Can be negative if rollover typing occurs
                current_release = current_event.timestamp + current_event.duration
                ud_val = next_event.timestamp - current_release
                ud_times.append(ud_val)
        
        # 2. Convert timings to seconds (Training data is in seconds, e.g. 0.1s)
        # We collected data in ms, so divide by 1000.
        timings = {
            "hold": [t / 1000.0 for t in hold_times],
            "dd": [t / 1000.0 for t in dd_times],
            "ud": [t / 1000.0 for t in ud_times]
        }
        
        # Use the central aggregation logic to get all 25+ features
        features = aggregate_features(timings)
        
        # Add metadata features
        features["keystroke_count"] = len(events)
        features["total_time"] = (events[-1].timestamp - events[0].timestamp) / 1000.0 if events else 0
        
        return features

    # Helper methods _safe_mean, _safe_std, _safe_cv can be removed as they are 
    # replaced by app.pipeline.aggregate logic, but keeping them if needed for compatibility
    # or other imports. For this file, they are now unused.