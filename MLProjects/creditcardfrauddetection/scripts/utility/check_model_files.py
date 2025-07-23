import os

# Define file paths
model_path = os.path.join("D:", "Study", "AILearning", "MLProjects", "creditcardfrauddetection", "data", "models", "fraud_model.joblib")
scaler_path = os.path.join("D:", "Study", "AILearning", "MLProjects", "creditcardfrauddetection", "data", "models", "scaler.joblib")

# Check if files exist
print(f"Checking if model file exists: {model_path}")
print(f"File exists: {os.path.exists(model_path)}")
print(f"File size: {os.path.getsize(model_path)} bytes")

print(f"\nChecking if scaler file exists: {scaler_path}")
print(f"File exists: {os.path.exists(scaler_path)}")
print(f"File size: {os.path.getsize(scaler_path)} bytes")
