from fastapi import FastAPI
import joblib
import numpy as np

app = FastAPI()

# Load model and encoders when API starts
model = joblib.load("ml/models/price_model.pkl")
le_region = joblib.load("ml/models/le_region.pkl")
le_type = joblib.load("ml/models/le_type.pkl")

@app.get("/")
def home():
    return {"message": "Airbnb Market Expert API is running!"}

@app.get("/predict")
def predict_price(region: str, property_type: str):
    try:
        region_enc = le_region.transform([region])[0]
        type_enc = le_type.transform([property_type])[0]
        predicted = model.predict([[region_enc, type_enc]])
        return {
            "region": region,
            "property_type": property_type,
            "predicted_price_per_night": round(float(predicted[0]), 2)
        }
    except Exception as e:
        return {"error": str(e)}