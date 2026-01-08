import sys
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# Mock data for initial training
# In production, this would be a large dataset from MongoDB or external sources
TRAINING_DATA = [
    ("Ma CIN est AB123456", "PERSONAL_IDENTITY"),
    ("Mon RIB est 123456789012345678901234", "FINANCIAL_DATA"),
    ("الرقم الوطني الخاص بي هو AB123456", "PERSONAL_IDENTITY"),
    ("Voici mon dossier médical", "MEDICAL_DATA"),
    ("Email: test@example.com", "CONTACT_INFO"),
    ("Téléphone: 0612345678", "CONTACT_INFO"),
    ("Je travaille chez ENSIAS", "PROFESSIONAL_INFO"),
    ("Salaire mensuel: 10000 DH", "FINANCIAL_DATA"),
    ("Code Massar: R123456789", "PERSONAL_IDENTITY"),
    ("Numéro CNSS: 123456789", "PROFESSIONAL_INFO"),
]

def train_baseline_model(model_dir: str = "backend/models"):
    """Train a simple TF-IDF + Naive Bayes model as baseline"""
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)

    texts = [item[0] for item in TRAINING_DATA]
    labels = [item[1] for item in TRAINING_DATA]

    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    nb_model = MultinomialNB()

    X = vectorizer.fit_transform(texts)
    nb_model.fit(X, labels)

    joblib.dump(vectorizer, os.path.join(model_dir, "vectorizer.joblib"))
    joblib.dump(nb_model, os.path.join(model_dir, "nb_model.joblib"))
    
    print(f"✅ Baseline model trained on {len(texts)} samples and saved to {model_dir}")

if __name__ == "__main__":
    train_baseline_model()
