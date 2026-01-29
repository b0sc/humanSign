"""Export trained XGBoost model to ONNX format."""

import argparse
from pathlib import Path

import numpy as np
import joblib
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
import onnx
import onnxruntime as ort

from feature_engineering import NUM_FEATURES, FEATURE_NAMES


def export_to_onnx(
    model_path: Path,
    output_path: Path,
    validate: bool = True,
) -> None:
    """
    Convert XGBoost model to ONNX format.
    
    Args:
        model_path: Path to saved joblib model
        output_path: Path for ONNX output
        validate: Whether to validate the exported model
    """
    print(f"Loading model from: {model_path}")
    model = joblib.load(model_path)
    
    # Define input type (batch_size, num_features)
    initial_type = [('float_input', FloatTensorType([None, NUM_FEATURES]))]
    
    print(f"Converting to ONNX (features: {NUM_FEATURES})...")
    onnx_model = convert_sklearn(
        model,
        initial_types=initial_type,
        target_opset=12,  # Good compatibility
        options={'zipmap': False},  # Don't use zipmap for probabilities
    )
    
    # Save ONNX model
    output_path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save_model(onnx_model, str(output_path))
    print(f"ONNX model saved to: {output_path}")
    
    # Validate
    if validate:
        validate_onnx_model(output_path, model)


def validate_onnx_model(onnx_path: Path, original_model) -> None:
    """Validate ONNX model produces same outputs as original."""
    print("\n=== Validating ONNX Model ===")
    
    # Load ONNX model
    session = ort.InferenceSession(str(onnx_path))
    input_name = session.get_inputs()[0].name
    
    # Create test input
    np.random.seed(42)
    test_input = np.random.rand(5, NUM_FEATURES).astype(np.float32)
    
    # Get original predictions
    original_proba = original_model.predict_proba(test_input)
    
    # Get ONNX predictions
    onnx_outputs = session.run(None, {input_name: test_input})
    onnx_proba = onnx_outputs[1]  # Second output is probabilities
    
    # Compare
    max_diff = np.max(np.abs(original_proba - onnx_proba))
    print(f"Max probability difference: {max_diff:.6f}")
    
    if max_diff < 0.01:
        print("✓ ONNX model validated successfully!")
    else:
        print("⚠ Warning: ONNX outputs differ from original model")
    
    # Print model info
    print(f"\nONNX Model Info:")
    print(f"  Input: {input_name} {session.get_inputs()[0].shape}")
    for i, output in enumerate(session.get_outputs()):
        print(f"  Output {i}: {output.name} {output.shape}")


def test_inference_speed(onnx_path: Path, n_iterations: int = 1000) -> None:
    """Benchmark ONNX inference speed."""
    import time
    
    print(f"\n=== Inference Speed Test ({n_iterations} iterations) ===")
    
    session = ort.InferenceSession(str(onnx_path))
    input_name = session.get_inputs()[0].name
    
    # Warm up
    test_input = np.random.rand(1, NUM_FEATURES).astype(np.float32)
    for _ in range(10):
        session.run(None, {input_name: test_input})
    
    # Benchmark
    start = time.perf_counter()
    for _ in range(n_iterations):
        session.run(None, {input_name: test_input})
    elapsed = time.perf_counter() - start
    
    avg_ms = (elapsed / n_iterations) * 1000
    print(f"Average inference time: {avg_ms:.3f} ms")
    print(f"Throughput: {n_iterations / elapsed:.0f} predictions/sec")


def main():
    parser = argparse.ArgumentParser(description='Export XGBoost model to ONNX')
    parser.add_argument('--model-path', type=Path, default=Path('models/keystroke_model.joblib'),
                        help='Path to trained joblib model')
    parser.add_argument('--output-path', type=Path, default=Path('models/keystroke_model.onnx'),
                        help='Path for ONNX output')
    parser.add_argument('--no-validate', action='store_true',
                        help='Skip validation')
    parser.add_argument('--benchmark', action='store_true',
                        help='Run inference speed benchmark')
    args = parser.parse_args()
    
    print("=== ONNX Export ===\n")
    
    if not args.model_path.exists():
        print(f"Error: Model file not found: {args.model_path}")
        print("Run 'python train_xgboost.py' first to train a model")
        return
    
    export_to_onnx(args.model_path, args.output_path, validate=not args.no_validate)
    
    if args.benchmark:
        test_inference_speed(args.output_path)
    
    print("\n=== Export Complete ===")
    print(f"ONNX model ready for inference at: {args.output_path}")


if __name__ == '__main__':
    main()
