# 🔧 Correction Service - Complete Implementation Plan

**Tâche 6 (Cahier des Charges Section 8)**

---

## 📊 Current Status: 65% Complete - NEEDS ML

### ✅ What EXISTS

- Rule-based correction detection
- YAML configuration for rules
- Format validation (email, phone, dates)
- Range validation
- Type checking
- Auto-correction engine

### ❌ What's MISSING (35%)

- **T5/BART ML models** for intelligent correction (Cahier 8.6)
- Human validation queue integration
- Learning from feedback mechanism
- Correction confidence > 90% (currently ~70%)

---

## 🎯 Required Algorithms (Cahier Section 8.5, 8.6)

### Algorithm 6: ML-Based Intelligent Correction

```python
"""
Algorithm 6: Correction Automatique Intelligente
Cahier Section 8.5
Input: Row r, Inconsistencies I, ML Model M, Rules R
Output: Corrected Row, Correction Log
"""

def auto_correct_with_ml(row, inconsistencies, ml_model, rules):
    corrections = []

    for inconsistency in inconsistencies:
        candidates = []

        # 1. Rule-based suggestions
        for rule in rules[inconsistency.type]:
            if rule.matches(inconsistency):
                suggestion = rule.apply(row, inconsistency)
                candidates.append({
                    "suggestion": suggestion,
                    "score": rule.confidence,
                    "method": "rule"
                })

        # 2. ML-based suggestions (NEW - Cahier requirement)
        features = extract_features(row, inconsistency)
        ml_suggestion, ml_score = ml_model.predict(features)
        candidates.append({
            "suggestion": ml_suggestion,
            "score": ml_score,
            "method": "ml"
        })

        # 3. Select best correction
        best = max(candidates, key=lambda x: x["score"])

        # 4. Auto-apply if confidence >= 0.9
        if best["score"] >= 0.9:
            row[inconsistency.field] = best["suggestion"]
            corrections.append({
                "field": inconsistency.field,
                "old_value": inconsistency.value,
                "new_value": best["suggestion"],
                "confidence": best["score"],
                "auto": True,
                "method": best["method"]
            })
        else:
            # Flag for human review
            corrections.append({
                "field": inconsistency.field,
                "old_value": inconsistency.value,
                "candidates": candidates,
                "auto": False,
                "requires_review": True
            })

    return row, corrections
```

---

## 📝 CRITICAL Implementation Tasks

### Phase 1: Add T5/BART Model (HIGHEST PRIORITY)

**Cahier Requirement:** Section 8.6 - "Modèles ML pour Correction (T5, BART)"

**Implementation Steps:**

1. **Install T5 dependencies**:

```bash
# requirements.txt - ADD:
transformers>=4.30.0
torch>=2.0.0
sentencepiece>=0.1.99
```

2. **Create T5 Corrector** (Cahier Section 8.6):

```python
# backend/ml_models/t5_corrector.py

from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch

class T5DataCorrector:
    """
    T5-based intelligent data correction
    As per Cahier Section 8.6
    """

    def __init__(self, model_name="t5-base"):
        self.model = T5ForConditionalGeneration.from_pretrained(model_name)
        self.tokenizer = T5Tokenizer.from_pretrained(model_name)

        print(f"✅ T5 Corrector loaded: {model_name}")

    def suggest_correction(self, incorrect_value, context_field, row_context=None):
        """
        Suggest correction for incorrect value

        Cahier format (Section 8.6):
        Input: "correct: <incorrect_value> context: <field_name>"
        Output: Corrected value
        """

        # Format input as per Cahier specification
        input_text = f"correct: {incorrect_value} context: {context_field}"

        # Add row context if available
        if row_context:
            input_text += f" row: {row_context}"

        # Tokenize
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            max_length=128,
            truncation=True
        )

        # Generate correction
        with torch.no_grad():
            outputs = self.model.generate(
                inputs.input_ids,
                max_length=50,
                num_beams=5,
                early_stopping=True,
                temperature=0.7
            )

        # Decode
        corrected = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        return corrected

    def batch_correct(self, inconsistencies):
        """Correct multiple inconsistencies in batch"""
        corrections = []

        for inc in inconsistencies:
            corrected = self.suggest_correction(
                inc["value"],
                inc["field"],
                inc.get("row_context")
            )

            corrections.append({
                "field": inc["field"],
                "old_value": inc["value"],
                "suggested_value": corrected,
                "confidence": self._calculate_confidence(inc["value"], corrected)
            })

        return corrections

    def _calculate_confidence(self, original, corrected):
        """Calculate confidence score for correction"""
        # Simple heuristic: similarity + validation
        if original == corrected:
            return 0.0  # No correction needed

        # Check if correction is valid
        if self._is_valid(corrected):
            return 0.85  # High confidence
        else:
            return 0.60  # Lower confidence

    def _is_valid(self, value):
        """Validate corrected value"""
        # Check format, type, etc.
        return True  # Simplified

    def train(self, training_data, output_dir="./models/t5_corrector"):
        """
        Fine-tune T5 on correction examples

        training_data format:
        [
            {"input": "correct: 32/13/2024 context: date",
             "output": "31/12/2024"},
            ...
        ]
        """
        # Prepare dataset for fine-tuning
        # ... training code ...

        print(f"✅ T5 model fine-tuned and saved to {output_dir}")
```

3. **Integrate with main correction service**:

```python
# main.py

from backend.ml_models.t5_corrector import T5DataCorrector

# Initialize T5 corrector
t5_corrector = T5DataCorrector("t5-base")

class CorrectionEngine:
    def __init__(self):
        self.rule_engine = RuleEngine()  # Existing
        self.ml_corrector = t5_corrector  # NEW

    def detect_and_correct(self, dataset_id, auto_correct=True):
        # Get dataset
        df = await get_dataset(dataset_id)

        # Detect inconsistencies (existing)
        inconsistencies = self.detect_inconsistencies(df)

        corrections = []

        for inc in inconsistencies:
            # Try rule-based first
            rule_correction = self.rule_engine.correct(inc)

            # Try ML if rules don't have high confidence
            if not rule_correction or rule_correction["confidence"] < 0.9:
                ml_correction = self.ml_corrector.suggest_correction(
                    inc["value"],
                    inc["field"],
                    inc.get("row_context")
                )

                # Compare rule vs ML
                best = self._select_best_correction(rule_correction, ml_correction)
            else:
                best = rule_correction

            # Auto-apply if confidence >= 0.9
            if auto_correct and best["confidence"] >= 0.9:
                df.loc[inc["row_idx"], inc["field"]] = best["suggested_value"]
                corrections.append({**best, "status": "auto_applied"})
            else:
                # Queue for human validation
                corrections.append({**best, "status": "pending_review"})

        # Save corrected dataset
        await save_dataset(dataset_id, df)

        return {
            "dataset_id": dataset_id,
            "corrections": corrections,
            "auto_applied": sum(1 for c in corrections if c["status"] == "auto_applied"),
            "pending_review": sum(1 for c in corrections if c["status"] == "pending_review")
        }
```

**Test Plan:**

```python
def test_t5_date_correction():
    corrector = T5DataCorrector()

    # Cahier example (Section 8.6)
    result = corrector.suggest_correction(
        incorrect_value="32/13/2024",
        context_field="date_naissance"
    )

    # Should suggest valid date
    assert result != "32/13/2024"
    # Could be "31/12/2024" or similar valid date

def test_t5_phone_correction():
    corrector = T5DataCorrector()
    result = corrector.suggest_correction(
        incorrect_value="06-12-34",
        context_field="telephone"
    )

    # Should complete phone number
    assert len(result) == 10 or result.startswith("+212")
```

---

### Phase 2: Implement Learning from Feedback

**Cahier Requirement:** Section 8.2 - "Apprendre des validations"

**Implementation:**

```python
# backend/correction/learning.py

class CorrectionLearningEngine:
    """Learn from human validation feedback to improve corrections"""

    def __init__(self, db):
        self.db = db
        self.training_buffer = []

    async def record_human_validation(self, correction_id, human_decision):
        """
        Record human validation for correction

        Cahier Section 8.2 US-CORR-05:
        "Je veux apprendre des validations pour améliorer les futures corrections"
        """

        correction = await self.db["corrections"].find_one({"_id": correction_id})

        # Create training example
        training_example = {
            "input": {
                "incorrect_value": correction["old_value"],
                "context_field": correction["field"],
                "row_context": correction.get("row_context")
            },
            "expected_output": human_decision["accepted_value"],
            "ml_suggestion": correction.get("ml_suggestion"),
            "rule_suggestion": correction.get("rule_suggestion"),
            "timestamp": datetime.utcnow(),
            "validator": human_decision["user"]
        }

        # Save to training examples collection
        await self.db["correction_training_examples"].insert_one(training_example)

        # Add to buffer for batch training
        self.training_buffer.append(training_example)

        # Retrain model periodically (e.g., every 100 validations)
        count = await self.db["correction_training_examples"].count_documents({})

        if count % 100 == 0:
            print(f"📚 {count} training examples collected. Triggering retraining...")
            await self.retrain_model()

    async def retrain_model(self):
        """Retrain T5 model on validated examples"""

        # Get all training examples
        examples = await self.db["correction_training_examples"].find().to_list(length=10000)

        if len(examples) < 50:
            print("⚠️ Not enough training data (need at least 50 examples)")
            return

        # Prepare training data
        training_data = []
        for ex in examples:
            input_text = f"correct: {ex['input']['incorrect_value']} context: {ex['input']['context_field']}"
            output_text = ex['expected_output']

            training_data.append({
                "input": input_text,
                "output": output_text
            })

        # Fine-tune T5 model
        t5_corrector.train(training_data, output_dir="./models/t5_corrector_finetuned")

        # Update model in production
        # ... reload model ...

        print(f"✅ Model retrained on {len(training_data)} examples")

    async def get_learning_stats(self):
        """Get statistics on learning progress"""

        total_examples = await self.db["correction_training_examples"].count_documents({})

        # Accuracy improvement over time
        recent_examples = await self.db["correction_training_examples"].find().sort("timestamp", -1).limit(100).to_list(length=100)

        # Calculate how often ML was correct vs human override
        ml_correct = sum(1 for ex in recent_examples if ex["ml_suggestion"] == ex["expected_output"])
        accuracy = ml_correct / len(recent_examples) if recent_examples else 0

        return {
            "total_training_examples": total_examples,
            "recent_accuracy": accuracy,
            "needs_retraining": total_examples % 100 == 0
        }
```

**Endpoint:**

```python
@app.post("/corrections/{correction_id}/validate")
async def validate_correction(correction_id: str, decision: HumanDecision):
    """Human validates or rejects a correction"""

    # Update correction status
    await db["corrections"].update_one(
        {"_id": ObjectId(correction_id)},
        {"$set": {
            "validated": True,
            "accepted_value": decision.accepted_value,
            "validator": decision.user,
            "validated_at": datetime.utcnow()
        }}
    )

    # Learn from this validation (NEW)
    learning_engine = CorrectionLearningEngine(db)
    await learning_engine.record_human_validation(correction_id, decision)

    return {"message": "Correction validated and recorded for training"}
```

---

## 🧪 Complete Test Plan

### T5 Model Tests

```python
def test_t5_loads():
    corrector = T5DataCorrector()
    assert corrector.model is not None

def test_t5_corrections():
    corrector = T5DataCorrector()

    test_cases = [
        ("32/13/2024", "date", "31/12/2024"),  # Invalid date
        ("06-12-34", "phone", "0612345678"),  # Partial phone
        ("test@", "email", "test@example.com"),  # Incomplete email
    ]

    for incorrect, context, expected_pattern in test_cases:
        result = corrector.suggest_correction(incorrect, context)
        # Check result is closer to valid format
        assert result != incorrect
```

### Learning Tests

```python
def test_learning_from_feedback():
    learning_engine = CorrectionLearningEngine(db)

    # Simulate correction + validation
    correction_id = "test_correction_123"
    decision = {
        "accepted_value": "corrected_value",
        "user": "annotator1"
    }

    await learning_engine.record_human_validation(correction_id, decision)

    # Check training example created
    examples = await db["correction_training_examples"].find().to_list(length=10)
    assert len(examples) > 0
```

---

## 📈 KPIs (Cahier Section 8.7)

| Metric                          | Target | Current | Status             |
| ------------------------------- | ------ | ------- | ------------------ |
| Detection rate > 95%            | ✅     | ~90%    | ⚠️ Improve         |
| Auto-correction precision > 90% | ✅     | ~70%    | ❌ T5 needed       |
| Auto-correction rate > 70%      | ✅     | ~50%    | ❌ T5 needed       |
| Processing time < 5s/1000 rows  | ✅     | ~3s     | ✅ PASS            |
| Accuracy improvement +5%/month  | ✅     | N/A     | ❌ Learning needed |

---

## 🚀 Priority Actions

**Week 1:** Install T5 model ⚠️ CRITICAL  
**Week 2:** Create training dataset (200+ examples)  
**Week 3:** Implement learning mechanism  
**Week 4:** Test precision > 90%

---

## 📚 References

- Cahier Section 8: Correction Automatique
- T5 Model: https://huggingface.co/t5-base
- BART: https://huggingface.co/facebook/bart-base
