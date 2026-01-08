import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODELS = {
    "fr": "cmarkea/distilcamembert-base-sentiment",
    "ar": "MoussaS/AraBERT-sentiment-analysis",
    "en": "distilbert-base-uncased-finetuned-sst-2-english"
}

BASE_DIR = "backend/models"

def download_models():
    for lang, model_name in MODELS.items():
        save_path = os.path.join(BASE_DIR, lang)
        print(f"📥 Downloading {lang} model ({model_name}) to {save_path}...")
        
        if not os.path.exists(save_path):
            os.makedirs(save_path)
            
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            tokenizer.save_pretrained(save_path)
            model.save_pretrained(save_path)
            print(f"✅ {lang} model saved successfully.")
        except Exception as e:
            print(f"❌ Error downloading {lang} model: {e}")

if __name__ == "__main__":
    # Ensure we are in the right directory or absolute paths
    # Assuming run from services/classification-serv/
    download_models()
