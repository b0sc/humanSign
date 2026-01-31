import sys
from pathlib import Path
import joblib

# Setup path
PROJECT_ROOT = Path.cwd()
sys.path.insert(0, str(PROJECT_ROOT / "ml"))

def check_mapping():
    artifacts_dir = PROJECT_ROOT / "ml" / "models" / "artifacts"
    encoder_path = artifacts_dir / "label_encoder.pkl"
    
    if not encoder_path.exists():
        print(f"Error: {encoder_path} not found")
        return

    try:
        le = joblib.load(encoder_path)
        print("Label Encoder Classes:")
        for i, label in enumerate(le.classes_):
            print(f"Class {i}: {label}")
            
        print("\nClasses for 's002':")
        if 's002' in le.classes_:
            idx = le.transform(['s002'])[0]
            print(f"s002 is Class {idx}")
        else:
            print("s002 not found in encoder classes")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_mapping()
