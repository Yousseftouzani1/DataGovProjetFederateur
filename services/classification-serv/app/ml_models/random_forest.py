
import pickle
import numpy as np
import os

class RandomForestAdapter:
    """
    Expert 2: Statistical Features (Random Forest)
    Distinguishes data types based on shape (entropy, length, digits).
    """
    
    def __init__(self, model_path="saved_models/rf_model.pkl"):
        self.model = None
        if os.path.exists(model_path):
            with open(model_path, "rb") as f:
                self.model = pickle.load(f)
        else:
            print(f"⚠️ Warning: RF Model not found at {model_path}. Training required.")

    def extract_features(self, values: list) -> np.array:
        """
        Extracts [avg_len, digit_ratio, alpha_ratio]
        """
        if not values:
            return np.array([[0, 0, 0]])
            
        str_vals = [str(v) for v in values]
        avg_len = np.mean([len(s) for s in str_vals])
        
        # Join all to calc ratios efficiently
        full_text = "".join(str_vals)
        if len(full_text) == 0: return np.array([[0, 0, 0]])
        
        digits = sum(c.isdigit() for c in full_text)
        alphas = sum(c.isalpha() for c in full_text)
        total = len(full_text)
        
        return np.array([[avg_len, digits/total, alphas/total]])

    def predict(self, values: list) -> dict:
        if not self.model:
            return {"class": None, "confidence": 0.0}
            
        features = self.extract_features(values)
        probs = self.model.predict_proba(features)[0]
        pred_class = np.argmax(probs)
        confidence = probs[pred_class]
        
        return {
            "class": int(pred_class),
            "confidence": float(confidence),
            "source": "RandomForest"
        }
