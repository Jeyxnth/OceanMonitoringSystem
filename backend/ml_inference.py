import joblib
import pandas as pd
import os

# Placeholder for the user's ML model
# When the user provides 'bloom_model.pkl', it will be loaded here.
MODEL_PATH = "bloom_model.pkl"

class BloomModel:
    def __init__(self):
        self.model = None
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
            except Exception as e:
                print(f"Error loading model: {e}")
        else:
            print("ML model not found. Using simulation logic for inference.")

    def predict(self, features):
        """
        features: dict with keys like 'sst', 'salinity', 'nitrate', 'do', 'turbidity'
        """
        if self.model:
            # Actual model prediction
            df = pd.DataFrame([features])
            prob = self.model.predict_proba(df)[0][1] # Assuming binary classifier (1: bloom)
            pred = "High" if prob > 0.66 else "Medium" if prob > 0.33 else "Low"
            return {"probability": round(prob * 100, 1), "prediction": pred}
        else:
            # Robust simulation logic based on common oceanographic triggers
            # SST > 29°C is a major factor
            # Nitrate > 50 µmol/L is high
            # Salinity < 34 PSU (freshwater influx) often triggers blooms
            
            sst = features.get('sst', 28.0)
            nitrate = features.get('nitrate', 25.0)
            salinity = features.get('salinity', 34.5)
            do = features.get('do', 7.0)
            
            score = 0
            if sst > 30: score += 40
            elif sst > 28: score += 20
            
            if nitrate > 60: score += 40
            elif nitrate > 30: score += 20
            
            if salinity < 33: score += 15 # Runoff indicator
            
            if do < 5: score += 15 # Hypoxic indicators often correlate with active blooms
            
            # Normalize to 0-100
            prob = min(100, max(0, score))
            pred = "High" if prob > 66 else "Medium" if prob > 33 else "Low"
            
            return {"probability": float(prob), "prediction": pred}

# Singleton instance
model_service = BloomModel()
