
import os
import pickle
import pandas as pd
import numpy as np
import torch
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments, DataCollatorWithPadding
from datasets import Dataset

# ==========================================
# CONFIGURATION
# ==========================================
MODEL_NAME = "almanach/camembert-base" # French BERT
LABELS = {
    0: "PUBLIC",
    1: "INTERNAL",
    2: "CONFIDENTIAL",
    3: "PII",
    4: "SPI",
    5: "CRITICAL"
}
NUM_LABELS = len(LABELS)
OUTPUT_DIR = "./saved_models"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==========================================
# 1. SYNTHETIC DATA GENERATION (Since no real data provided yet)
# ==========================================
def generate_training_data():
    """
    Generates a synthetic dataset to TRAIN the models.
    Satisfies US-CLASS-03: 'Developer must train the model'.
    Enhanced with more diversity to reduce overfitting.
    """
    data = []
    
    # helper to add multiple items
    def add_items(items, label):
        for text in items:
            # simple feature extraction for simulation
            avg_len = len(text)
            digits = sum(c.isdigit() for c in text)
            digit_ratio = digits / len(text) if len(text) > 0 else 0
            alphas = sum(c.isalpha() for c in text)
            alpha_ratio = alphas / len(text) if len(text) > 0 else 0
            data.append((text, label, avg_len, digit_ratio, alpha_ratio))

    # 0: PUBLIC (General text, cities, descriptions)
    public_texts = [
        "Casablanca", "Rabat", "Marrakech", "Tanger", "Agadir", "Fes", "Meknes",
        "Rue des fleurs", "Avenue Mohammed V", "Boulevard Zerktouni",
        "Description du produit", "Article de presse", "Météo du jour",
        "Publicité", "Information générale", "Open Data", "Statistiques annuelles",
        "Recensement de la population", "Le ciel est bleu", "Tourisme au Maroc",
        "La gare de Casa Port", "Restaurant ouvert", "Menu du jour"
    ]
    add_items(public_texts, 0)

    # 1: INTERNAL (Project codes, internal memos)
    internal_texts = [
        "EMP-8822", "PRJ-Alpha", "Project Beta", "Internal Memo", "Compte rendu réunion",
        "Meeting notes", "Draft v1", "Version 2.0", "Ticket JIRA-123", "Bug report",
        "Feature request", "Deployment logs", "Server status", "API Gateway",
        "Backend service", "Frontend config", "DevOps pipeline"
    ]
    add_items(internal_texts, 1)

    # 2: CONFIDENTIAL (Budgets, strategy, passwords)
    confidential_texts = [
        "Budget 2026", "Stratégie marketing", "Plan financier", "Secret commercial",
        "Mot de passe admin", "Clé privée", "Access Token", "Contrat confidentiel",
        "Salaire des cadres", "Offre de rachat", "Fusion acquisition",
        "Audit interne", "Rapport de vulnérabilité", "Non Disclosure Agreement", "NDA Signed"
    ]
    add_items(confidential_texts, 2)

    # 3: PII (Personal Identifiers)
    pii_texts = [
        "Mohammed Alami", "Fatima Ezzahra", "Youssef Bennani", "Karim Tazi",
        "John Doe", "Jane Smith", "Alice Wonderland",
        "test@gmail.com", "contact@entreprise.ma", "rh@ocp.ma", "support@cih.ma",
        "0661223344", "0700112233", "+212612345678", "0522445566",
        "Adresse domicile", "Mon numéro de téléphone", "Email personnel"
    ]
    add_items(pii_texts, 3)

    # 4: SPI (Sensitive Personal Info - Religion, Politics, Health)
    spi_texts = [
        "Musulman", "Chrétien", "Juif", "Athée",
        "Parti de l'Istiqlal", "PJD", "PAM", "Socialiste", "Communiste",
        "Diabétique", "Enceinte", "Maladie cardiaque", "Handicapé",
        "Syndicat", "Orientation sexuelle", "Origine ethnique"
    ]
    add_items(spi_texts, 4)

    # 5: CRITICAL (IDs, Bank details)
    critical_texts = [
        "AB123456", "BE897654", "EE112233", "CIN Maroc",
        "FR76 1234 5678 9012 3456 7890 12", "MA64 1234 5678 9012 3456 7890 12",
        "Numero carte bancaire", "CVV 123", "Code PIN 0000",
        "Passport 123456789", "Permis de conduire"
    ]
    add_items(critical_texts, 5)

    # Augment data slightly to prevent instant overfit on small set
    # but not just dumb multiplication of the same 5 items
    # We rely on the diversity above.
    # We duplicates the list 10 times instead of 50 to balance epoch training
    data = data * 10
    
    df = pd.DataFrame(data, columns=["text", "label", "avg_len", "digit_ratio", "alpha_ratio"])
    return df

# ==========================================
# 2. RANDOM FOREST TRAINING (Statistical Features)
# ==========================================
def train_random_forest(df):
    print("🌲 Training Random Forest on Statistical Features...")
    X = df[["avg_len", "digit_ratio", "alpha_ratio"]]
    y = df["label"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    
    y_pred = rf_model.predict(X_test)
    print("Random Forest F1 Score:", f1_score(y_test, y_pred, average='weighted'))
    
    # Save Model
    with open(f"{OUTPUT_DIR}/rf_model.pkl", "wb") as f:
        pickle.dump(rf_model, f)
    print("✅ Random Forest Saved.")

# ==========================================
# 3. BERT FINE-TUNING (Semantic Features)
# ==========================================
def preprocess_function(examples, tokenizer):
    return tokenizer(examples["text"], truncation=True, padding=True, max_length=64)

def train_bert(df):
    print("🤖 Fine-Tuning CamemBERT on Semantic Features...")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=NUM_LABELS)
    
    # Prepare Data
    dataset = Dataset.from_pandas(df[["text", "label"]])
    dataset = dataset.train_test_split(test_size=0.2)
    
    tokenized_datasets = dataset.map(lambda x: preprocess_function(x, tokenizer), batched=True)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    
    training_args = TrainingArguments(
        output_dir="./bert_results",
        eval_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=3,
        weight_decay=0.01,
        save_strategy="no", # Save space
        logging_steps=10
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["test"],
        tokenizer=tokenizer,
        data_collator=data_collator,
    )
    
    trainer.train()
    
    # Save Fine-Tuned Model
    model.save_pretrained(f"{OUTPUT_DIR}/bert_classifier")
    tokenizer.save_pretrained(f"{OUTPUT_DIR}/bert_classifier")
    print("✅ BERT Model Saved.")

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    print("🚀 Starting Training Process (CDC Requirement)...")
    df = generate_training_data()
    
    train_random_forest(df)
    train_bert(df)
    
    print("\n🎉 Training Complete! Models ready for Ensemble.")
