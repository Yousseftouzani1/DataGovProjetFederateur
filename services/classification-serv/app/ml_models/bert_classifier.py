
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
import os

class BertClassifierAdapter:
    """
    Expert 3: Semantic Features (CamemBERT)
    Understands context (e.g., 'President').
    """
    
    def __init__(self, model_dir="saved_models/bert_classifier"):
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        if os.path.exists(model_dir):
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)
                self.model.to(self.device)
                self.model.eval()
            except Exception as e:
                print(f"⚠️ Error loading BERT: {e}")
        else:
            print(f"⚠️ Warning: BERT Model not found at {model_dir}. Fine-tuning required.")

    def predict(self, text_samples: list) -> dict:
        if not self.model or not self.tokenizer:
            return {"class": None, "confidence": 0.0}
            
        # Use the first few non-empty samples or join them? 
        # For simplicity/speed, let's take exact text if it's column name + samples
        # Ideally we classify based on column name AND samples. 
        # Here we just join top 3 samples.
        input_text = " ".join([str(v) for v in text_samples[:3]])
        
        inputs = self.tokenizer(input_text, return_tensors="pt", truncation=True, max_length=64, padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
        conf, pred_class = torch.max(probs, dim=1)
        
        return {
            "class": int(pred_class.item()),
            "confidence": float(conf.item()),
            "source": "CamemBERT"
        }
