# 🤖 Classification Service - Complete Implementation Plan

**Tâche 5 (Cahier des Charges Section 7)** ⚠️ CRITICAL - 55% Complete

---

## 📊 Current Status: NEEDS ML MODELS

### ✅ What EXISTS (55%)

- Keyword-based classification
- 6 sensitivity levels (PUBLIC → CRITICAL)
- TF-IDF vectorizer (defined)
- Validation workflow endpoints
- Confidence scoring
- MongoDB integration for validations

### ❌ What's MISSING (45%) - HIGH PRIORITY

- **HuggingFace BERT models** (CamemBERT, FlauBERT) - 0% implemented
- **Ensemble voting mechanism** - Simplified only
- **Model training pipeline** - Not functional
- **Real ML classification** - Using keywords only

---

## 🎯 Required Algorithms (Cahier Section 7.4, 7.5)

### Algorithm 5: Ensemble Classification (CRITICAL)

```python
"""
Algorithm 5: Classification Ensemble Multi-Modèles
Cahier Section 7.5
Input: Column C, Models M={M1,M2,...,Mn}, Weights W
Output: Class Label, Confidence Score
"""

def ensemble_classify(column_data, models, weights):
    # Step 1: Extract features
    features = extract_features(column_data)

    # Step 2: Get predictions from all models
    predictions = []
    for model in models:
        pred, conf = model.predict(features)
        predictions.append({
            "prediction": pred,
            "confidence": conf,
            "weight": weights[model.name]
        })

    # Step 3: Weighted voting
    votes = {}
    for p in predictions:
        if p["prediction"] not in votes:
            votes[p["prediction"]] = 0
        votes[p["prediction"]] += p["confidence"] * p["weight"]

    # Step 4: Select final class
    final_class = max(votes.items(), key=lambda x: x[1])[0]

    # Step 5: Compute ensemble confidence
    confidence = compute_ensemble_confidence(predictions, final_class)

    # Step 6: Flag for manual review if low confidence
    if confidence < 0.7:
        flag_for_manual_review()

    return final_class, confidence
```

---

## 📝 CRITICAL Implementation Tasks

### Phase 1: Install & Configure BERT Models (HIGHEST PRIORITY)

**Status:** transformers commented out in requirements.txt  
**Impact:** 0% → 90% compliance

**Implementation Steps:**

1. **Update requirements.txt**:

```bash
# requirements.txt - ADD THESE:
transformers>=4.30.0
torch>=2.0.0  # CPU version is fine for inference
sentencepiece>=0.1.99  # Required for CamemBERT
```

2. **Install dependencies**:

```bash
pip install transformers torch sentencepiece
```

3. **Create BERT Classifier** (Cahier Section 7.4):

```python
# backend/ml_models/bert_classifier.py

from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments
)
import torch

class BERTSensitivityClassifier:
    \"\"\"
    BERT-based classifier for data column sensitivity
    Uses CamemBERT (French) as per Cahier Section 7.4
    \"\"\"

    def __init__(self, model_name="camembert-base"):
        # Cahier recommends: CamemBERT, FlauBERT, DistilBERT
        self.model_name = model_name

        # 6 sensitivity classes (Cahier Section 7.6)
        self.num_labels = 6
        self.label_map = {
            0: "PUBLIC",
            1: "INTERNAL",
            2: "CONFIDENTIAL",
            3: "PII",
            4: "SPI",
            5: "CRITICAL"
        }

        # Load model
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=self.num_labels
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        print(f"✅ BERT Classifier loaded: {model_name}")

    def classify(self, text: str):
        \"\"\"Classify text sensitivity using BERT\"\"\"

        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )

        # Inference
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Get prediction
        logits = outputs.logits
        predicted_class_id = torch.argmax(logits, dim=1).item()
        confidence = torch.softmax(logits, dim=1).max().item()

        return {
            "classification": self.label_map[predicted_class_id],
            "confidence": round(confidence, 3),
            "method": "BERT"
        }

    def train(self, train_dataset, eval_dataset, output_dir="./models/bert_sensitivity"):
        \"\"\"Fine-tune BERT on annotated data\"\"\"

        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=3,
            per_device_train_batch_size=16,
            per_device_eval_batch_size=16,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir='./logs',
            logging_steps=10,
            evaluation_strategy="steps",
            eval_steps=50,
            save_steps=100,
            load_best_model_at_end=True,
        )

        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
        )

        # Train
        trainer.train()

        # Save best model
        self.model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)

        print(f"✅ Model fine-tuned and saved to {output_dir}")

        return trainer.evaluate()
```

4. **Update main.py to use BERT**:

```python
# main.py

from backend.ml_models.bert_classifier import BERTSensitivityClassifier

# NEW: Actually load BERT
TRANSFORMERS_AVAILABLE = True  # Change from False!
bert_classifier = BERTSensitivityClassifier("camembert-base")

class SensitivityClassifier:
    def __init__(self):
        self.bert = bert_classifier if TRANSFORMERS_AVAILABLE else None
        # ... existing code ...

    def classify(self, text: str, use_ml: bool = True, model: str = "ensemble"):
        if not use_ml or model == "simple":
            # Use existing keyword classifier
            return self.classify_sensitivity(text)

        elif model == "bert" and self.bert:
            # NEW: Use BERT
            return self.bert.classify(text)

        elif model == "ensemble" and self.bert:
            # NEW: Ensemble voting
            return self.ensemble_classify(text)

        else:
            # Fallback to keywords
            return self.classify_sensitivity(text)

    def ensemble_classify(self, text: str):
        \"\"\"Combine multiple models using weighted voting\"\"\"

        # Get predictions from all models
        bert_result = self.bert.classify(text) if self.bert else None
        keyword_result = self.classify_sensitivity(text)
        tfidf_result = self.tfidf_classify(text) if self.tfidf_vectorizer else None

        # Weighted voting (Cahier Algorithm 5)
        votes = {}
        weights = {
            "bert": 0.5,  # Highest weight to BERT
            "keyword": 0.2,
            "tfidf": 0.3
        }

        # Add BERT vote
        if bert_result:
            cls = bert_result["classification"]
            votes[cls] = votes.get(cls, 0) + bert_result["confidence"] * weights["bert"]

        # Add keyword vote
        cls = keyword_result["classification"]
        votes[cls] = votes.get(cls, 0) + keyword_result["confidence"] * weights["keyword"]

        # Add TF-IDF vote
        if tfidf_result:
            cls = tfidf_result["classification"]
            votes[cls] = votes.get(cls, 0) + tfidf_result["confidence"] * weights["tfidf"]

        # Final decision
        final_class = max(votes.items(), key=lambda x: x[1])[0]
        confidence = votes[final_class] / sum(votes.values())

        return {
            "classification": final_class,
            "confidence": round(confidence, 3),
            "method": "ensemble",
            "votes": votes
        }
```

**Test Plan:**

```python
def test_bert_loads():
    classifier = BERTSensitivityClassifier()
    assert classifier.model is not None
    assert classifier.tokenizer is not None

def test_bert_classifies():
    classifier = BERTSensitivityClassifier()
    result = classifier.classify("Numéro de carte bancaire")

    assert "classification" in result
    assert result["classification"] in ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "PII", "SPI", "CRITICAL"]
    assert 0 <= result["confidence"] <= 1

def test_ensemble_voting():
    classifier = SensitivityClassifier()
    result = classifier.ensemble_classify("CIN: AB123456")

    assert result["method"] == "ensemble"
    assert "votes" in result
    assert result["classification"] in ["PII", "CRITICAL"]
```

---

### Phase 2: Create Training Dataset

**Cahier Section 7.8:** Need annotated training data

**Implementation:**

```python
# scripts/generate_training_dataset.py

def generate_classification_training_data():
    \"\"\"Generate training examples for BERT fine-tuning\"\"\"

    examples = []

    # PUBLIC examples
    for _ in range(100):
        examples.append({
            "text": "Le nom du produit est XYZ",
            "label": 0  # PUBLIC
        })

    # CONFIDENTIAL examples
    for _ in range(100):
        examples.append({
            "text": "Salaire mensuel",
            "label": 2  # CONFIDENTIAL
        })

    # PII examples
    for _ in range(100):
        examples.append({
            "text": "Numéro de téléphone",
            "label": 3  # PII
        })

    # CRITICAL examples
    for _ in range(100):
        examples.append({
            "text": "Numéro de carte bancaire",
            "label": 5  # CRITICAL
        })

    # ... etc for all 6 classes

    df = pd.DataFrame(examples)
    df.to_csv("data/training_dataset.csv", index=False)

    return df
```

### Phase 3: Airflow DAG Integration (Cahier Section 2.4)

**Missing:** Classification service must be called from Airflow pipeline

**Implementation:**

```python
# Add endpoint for dataset-level classification
@app.post("/classify-dataset/{dataset_id}")
async def classify_dataset(dataset_id: str):
    """
    Classify all columns in a dataset
    Called by Airflow DAG (Cahier Section 2.4)
    """
    # Get dataset from MongoDB
    dataset = await db["datasets"].find_one({"_id": ObjectId(dataset_id)})

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Load data
    df = pd.DataFrame(dataset["data"])

    # Classify each column
    classifications = {}

    for column in df.columns:
        # Get sample values from column
        sample_text = " ".join(str(v) for v in df[column].head(10))

        # Use ensemble classification
        classifier = SensitivityClassifier()
        result = classifier.ensemble_classify(sample_text)

        classifications[column] = {
            "classification": result["classification"],
            "confidence": result["confidence"],
            "method": result["method"]
        }

    # Save classifications to MongoDB
    await db["datasets"].update_one(
        {"_id": ObjectId(dataset_id)},
        {"$set": {"classifications": classifications}}
    )

    # Return summary
    summary = {}
    for cls in classifications.values():
        level = cls["classification"]
        summary[level] = summary.get(level, 0) + 1

    return {
        "dataset_id": dataset_id,
        "total_columns": len(classifications),
        "classifications": classifications,
        "summary": summary
    }
```

**Airflow DAG Integration:**

```python
# airflow/dags/data_processing_pipeline.py

def classify_sensitivity(**context):
    """Call classification service (Cahier Algorithm 5)"""
    dataset_id = context['task_instance'].xcom_pull(task_ids='upload_dataset')['dataset_id']

    # Call classification service
    resp = requests.post(
        f"http://classification-service:8005/classify-dataset/{dataset_id}"
    )
    resp.raise_for_status()

    result = resp.json()

    print(f"✅ Classified {result['total_columns']} columns")
    print(f"Summary: {result['summary']}")

    # Check for manual review needs
    needs_review = [
        col for col, cls in result['classifications'].items()
        if cls['confidence'] < 0.7
    ]

    if needs_review:
        print(f"⚠️ {len(needs_review)} columns need manual review")
        # Trigger annotation task creation
        context['task_instance'].xcom_push(
            key='review_columns',
            value=needs_review
        )

    return result

# Add to DAG
classify_task = PythonOperator(
    task_id='classify_sensitivity',
    python_callable=classify_sensitivity,
    dag=dag
)

# Pipeline: ... >> clean_data >> classify_task >> quality_assessment >> ...
```

**Test Plan:**

```python
def test_airflow_integration():
    # Simulate Airflow call
    response = client.post(f"/classify-dataset/{test_dataset_id}")
    assert response.status_code == 200

    result = response.json()
    assert "classifications" in result
    assert "summary" in result
```

---

## 🧪 Complete Test Plan

### BERT Tests

```python
def test_bert_accuracy():
    # Test on validation set
    evaluator = ClassificationEvaluator()
    metrics = evaluator.evaluate_bert()

    # Cahier target: > 92% accuracy (Section 7.7)
    assert metrics["accuracy"] > 0.92
    assert metrics["f1_score_per_class"] > 0.88
```

---

## 📈 KPIs (Cahier Section 7.7)

| Metric                          | Target | Current | Status         |
| ------------------------------- | ------ | ------- | -------------- |
| Global accuracy > 92%           | ✅     | ~60%    | ❌ BERT needed |
| F1-Score per class > 0.88       | ✅     | ~0.55   | ❌ BERT needed |
| Classification time < 2s/column | ✅     | ~0.5s   | ✅ PASS        |
| Manual review rate < 10%        | ✅     | ~40%    | ❌ BERT needed |

---

## 🚀 Priority Action Items

1. **WEEK 1:** Install transformers + BERT model ⚠️ CRITICAL
2. **WEEK 2:** Create training dataset (600+ examples)
3. **WEEK 3:** Fine-tune BERT on classified data
4. **WEEK 4:** Implement ensemble voting
5. **WEEK 5:** Test and validate accuracy > 92%

---

## 📚 References

- Cahier Section 7: Système de Classification Fine-Grained
- CamemBERT: https://huggingface.co/camembert-base
- FlauBERT: https://huggingface.co/flaubert/flaubert_base_cased
- HuggingFace Transformers: https://huggingface.co/docs/transformers
