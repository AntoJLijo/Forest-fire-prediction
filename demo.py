import numpy as np
import joblib
from xgboost import Booster, DMatrix

# Load the scaler and model
try:
    scaler = joblib.load("scaler.pkl")
    print("Scaler loaded successfully:", type(scaler))

    model = Booster()
    model.load_model("fire_spread_model.json")
    print("Model loaded successfully:", type(model))
except Exception as e:
    print("Error loading scaler or model:", e)
    exit()

# Test data: a single sample with temperature, RH, wind, rain, wind_direction
sample_data = np.array([[24.96, 70, 3.11, 0.19, 57]])
print("Original sample data:", sample_data)

# Scale the data
try:
    scaled_sample = scaler.transform(sample_data)
    print("Scaled sample data:", scaled_sample)
except Exception as e:
    print("Error during scaling:", e)
    exit()

# Convert scaled data to DMatrix format for prediction
try:
    dmatrix_sample = DMatrix(scaled_sample)
    prediction = model.predict(dmatrix_sample)
    print("Model prediction:", prediction)
except Exception as e:
    print("Error during prediction:", e)
