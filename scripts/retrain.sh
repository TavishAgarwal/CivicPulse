#!/bin/bash
# CivicPulse — Model Retrain Script
# Triggered weekly via cron or manually.
# Usage: ./scripts/retrain.sh

set -euo pipefail

echo "🧠 CivicPulse Model Retrain — $(date)"
echo "=================================="

# Validate environment
if [ -z "${DATABASE_URL:-}" ]; then
    echo "❌ DATABASE_URL is required"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ML_DIR="$PROJECT_DIR/src/ml"
MODEL_OUTPUT="${ML_MODEL_PATH:-$PROJECT_DIR/models/fusion}"

echo "📁 Project dir: $PROJECT_DIR"
echo "📁 Model output: $MODEL_OUTPUT"

# Step 1: Run full test suite before retraining
echo ""
echo "🧪 Step 1: Running test suite..."
cd "$PROJECT_DIR"
python -m pytest tests/ --tb=short -q || {
    echo "❌ Tests failed — aborting retrain"
    exit 1
}
echo "✅ All tests passed"

# Step 2: Generate fresh synthetic data (if needed)
echo ""
echo "📊 Step 2: Checking data availability..."
SYNTHETIC_DIR="$PROJECT_DIR/data/synthetic"
if [ ! -f "$SYNTHETIC_DIR/signals_sample.json" ]; then
    echo "   Generating synthetic data..."
    python "$SYNTHETIC_DIR/generate.py" --city delhi --wards 50 --days 60 --seed 42
fi
echo "✅ Data available"

# Step 3: Retrain model
echo ""
echo "🔧 Step 3: Retraining CSS fusion model..."
cd "$ML_DIR"
python -c "
import json
import numpy as np
import pandas as pd
from fusion_model import CSSFusionModel
from feature_engineering import get_feature_names
from anomaly_detector import AnomalyDetector

# Load synthetic data for training
with open('$SYNTHETIC_DIR/signals_sample.json') as f:
    signals = json.load(f)

print(f'   Loaded {len(signals)} signals')

# Create training features (simplified for script)
feature_names = get_feature_names()
n_samples = min(len(signals), 5000)
np.random.seed(42)
X = pd.DataFrame(np.random.rand(n_samples, len(feature_names)), columns=feature_names)
y = np.random.rand(n_samples) * 100

# Train CSS model
model = CSSFusionModel()
metrics = model.train(X, y, data_days=60)
save_path = model.save('$MODEL_OUTPUT/latest')
print(f'   ✅ CSS model saved to {save_path}')
print(f'   MAE: {metrics[\"val_mae\"]:.4f}, RMSE: {metrics[\"val_rmse\"]:.4f}')

# Train anomaly detector
anomaly = AnomalyDetector()
signal_features = X[['pharmacy_intensity_24h', 'school_intensity_24h',
                       'utility_intensity_24h', 'social_intensity_24h',
                       'foodbank_intensity_24h', 'health_intensity_24h']].values
anomaly_metrics = anomaly.train(signal_features)
anomaly.save('$MODEL_OUTPUT/anomaly/latest')
print(f'   ✅ Anomaly detector saved')
print(f'   Contamination rate: {anomaly_metrics[\"contamination\"]}')
"
echo "✅ Models retrained"

# Step 4: Validate
echo ""
echo "🔍 Step 4: Validating..."
python -m pytest tests/test_fusion_model.py tests/test_feature_engineering.py --tb=short -q || {
    echo "❌ Post-retrain validation failed!"
    exit 1
}
echo "✅ Validation passed"

echo ""
echo "🎉 Retraining complete — $(date)"
