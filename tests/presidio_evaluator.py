"""
Presidio Service Evaluator
Calculates Precision, Recall, F1-Score against test dataset
Cahier Section 5.6 - Metrics Evaluation
"""

import pandas as pd
import json
import requests
from typing import Dict, List
from datetime import datetime
import os

class PresidioEvaluator:
    """Evaluate Presidio performance using Cahier formulas"""
    
    def __init__(self, base_url="http://localhost:8003"):
        self.base_url = base_url
        dataset_path = os.path.join(os.path.dirname(__file__), "data", "moroccan_pii_test_dataset.csv")
        
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Test dataset not found: {dataset_path}")
        
        self.dataset = pd.read_csv(dataset_path)
        print(f"✅ Loaded test dataset: {len(self.dataset)} samples")
    
    def evaluate(self) -> Dict:
        """
        Run complete evaluation
        
        Cahier Formulas (Section 5.6):
        - Precision = TP / (TP + FP)
        - Recall = TP / (TP + FN)
        - F1-Score = 2 × (Precision × Recall) / (Precision + Recall)
        - Accuracy = (TP + TN) / (TP + TN + FP + FN)
        """
        print("\n" + "="*70)
        print("PRESIDIO EVALUATION - Cahier Section 5 Metrics")
        print("="*70)
        print(f"\nEvaluating {len(self.dataset)} test cases...")
        
        TP = FP = FN = TN = 0
        results = []
        errors = []
        
        for idx, row in self.dataset.iterrows():
            text = row['text']
            expected = json.loads(row['expected_entities'])
            
            try:
                # Call Presidio API
                response = requests.post(
                    f"{self.base_url}/analyze",
                    json={
                        "text": text,
                        "language": "fr",
                        "score_threshold": 0.5
                    },
                    timeout=5
                )
                
                if response.status_code != 200:
                    errors.append({"index": idx, "error": f"API returned {response.status_code}"})
                    continue
                
                detections = response.json()['detections']
                detected_types = [d['entity_type'] for d in detections]
                
            except requests.exceptions.RequestException as e:
                errors.append({"index": idx, "error": str(e)})
                continue
            
            # Calculate metrics
            expected_set = set(expected)
            detected_set = set(detected_types)
            
            # True Positives: correctly detected entities
            tp = len(expected_set.intersection(detected_set))
            TP += tp
            
            # False Positives: detected but not expected
            fp = len(detected_set - expected_set)
            FP += fp
            
            # False Negatives: expected but not detected
            fn = len(expected_set - detected_set)
            FN += fn
            
            # True Negatives: no PII expected and none detected
            if len(expected) == 0 and len(detected_types) == 0:
                TN += 1
            
            # Store result
            is_correct = expected_set == detected_set
            results.append({
                "index": idx,
                "text": text[:60] + "..." if len(text) > 60 else text,
                "expected": expected,
                "detected": detected_types,
                "correct": is_correct,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "category": row.get('category', 'unknown')
            })
            
            # Progress indicator
            if (idx + 1) % 50 == 0:
                print(f"  Processed {idx + 1}/{len(self.dataset)} samples...")
        
        # Calculate final metrics using Cahier formulas
        precision = TP / (TP + FP) if (TP + FP) > 0 else 0
        recall = TP / (TP + FN) if (TP + FN) > 0 else 0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = (TP + TN) / (TP + TN + FP + FN) if (TP + TN + FP + FN) > 0 else 0
        
        metrics = {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "accuracy": accuracy,
            "TP": TP,
            "FP": FP,
            "FN": FN,
            "TN": TN,
            "total_tests": len(self.dataset),
            "correct_predictions": sum(1 for r in results if r['correct']),
            "errors": errors,
            "results": results
        }
        
        # Print summary
        self._print_summary(metrics)
        
        return metrics
    
    def _print_summary(self, metrics):
        """Print evaluation summary"""
        print(f"\n{'='*70}")
        print("METRICS SUMMARY")
        print(f"{'='*70}")
        
        print(f"\n📊 Confusion Matrix:")
        print(f"┌─────────────────┬──────────┬──────────┐")
        print(f"│                 │ Positive │ Negative │")
        print(f"├─────────────────┼──────────┼──────────┤")
        print(f"│ Actual Positive │ TP: {metrics['TP']:4d} │ FN: {metrics['FN']:4d} │")
        print(f"│ Actual Negative │ FP: {metrics['FP']:4d} │ TN: {metrics['TN']:4d} │")
        print(f"└─────────────────┴──────────┴──────────┘")
        
        print(f"\n📈 Performance Metrics (Cahier Section 5.6):")
        print(f"┌─────────────┬──────────┬──────────┬────────┐")
        print(f"│ Metric      │ Value    │ Target   │ Status │")
        print(f"├─────────────┼──────────┼──────────┼────────┤")
        
        precision_status = "✅ PASS" if metrics['precision'] >= 0.90 else "❌ FAIL"
        recall_status = "✅ PASS" if metrics['recall'] >= 0.85 else "❌ FAIL"
        f1_status = "✅ PASS" if metrics['f1_score'] >= 0.87 else "❌ FAIL"
        
        print(f"│ Precision   │ {metrics['precision']:6.2%}   │ > 90%    │ {precision_status} │")
        print(f"│ Recall      │ {metrics['recall']:6.2%}   │ > 85%    │ {recall_status} │")
        print(f"│ F1-Score    │ {metrics['f1_score']:6.2%}   │ > 87%    │ {f1_status} │")
        print(f"│ Accuracy    │ {metrics['accuracy']:6.2%}   │ -        │ -      │")
        print(f"└─────────────┴──────────┴──────────┴────────┘")
        
        # Overall status
        all_passed = metrics['precision'] >= 0.90 and metrics['recall'] >= 0.85 and metrics['f1_score'] >= 0.87
        
        print(f"\n{'='*70}")
        if all_passed:
            print("🎉 CAHIER COMPLIANCE: PASS - All targets met!")
        else:
            print("⚠️  CAHIER COMPLIANCE: FAIL - Improvements needed")
        print(f"{'='*70}")
        
        if metrics['errors']:
            print(f"\n⚠️  {len(metrics['errors'])} API errors occurred during evaluation")
    
    def generate_report(self) -> str:
        """Generate comprehensive Markdown evaluation report"""
        metrics = self.evaluate()
        
        # Per-category metrics
        category_stats = self._calculate_category_metrics(metrics['results'])
        
        # Failed cases
        failed_cases = [r for r in metrics['results'] if not r['correct']][:20]
        
        report = f"""# Presidio Service - Evaluation Report

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Dataset:** {metrics['total_tests']} Moroccan PII test samples  
**Cahier Section:** 5.6 - Metrics Evaluation

---

## ✅ Cahier des Charges Compliance

### Overall Metrics

| Metric | Value | Target (Cahier) | Status |
|--------|-------|-----------------|--------|
| **Precision** | **{metrics['precision']:.2%}** | **> 90%** | **{'✅ PASS' if metrics['precision'] >= 0.90 else '❌ FAIL'}** |
| **Recall** | **{metrics['recall']:.2%}** | **> 85%** | **{'✅ PASS' if metrics['recall'] >= 0.85 else '❌ FAIL'}** |
| **F1-Score** | **{metrics['f1_score']:.2%}** | **> 87%** | **{'✅ PASS' if metrics['f1_score'] >= 0.87 else '❌ FAIL'}** |
| **Accuracy** | **{metrics['accuracy']:.2%}** | - | - |

---

## 📊 Confusion Matrix

```
                Predicted Positive    Predicted Negative
Actual Positive      TP: {metrics['TP']:4d}           FN: {metrics['FN']:4d}
Actual Negative      FP: {metrics['FP']:4d}           TN: {metrics['TN']:4d}
```

**Formulas Used (Cahier Section 5.6):**
- Precision = TP / (TP + FP) = {metrics['TP']} / ({metrics['TP']} + {metrics['FP']}) = {metrics['precision']:.4f}
- Recall = TP / (TP + FN) = {metrics['TP']} / ({metrics['TP']} + {metrics['FN']}) = {metrics['recall']:.4f}
- F1-Score = 2 × (P × R) / (P + R) = {metrics['f1_score']:.4f}

---

## 📈 Test Dataset Statistics

- **Total Samples:** {metrics['total_tests']}
- **Correct Predictions:** {metrics['correct_predictions']} ({metrics['correct_predictions']/metrics['total_tests']*100:.1f}%)
- **Incorrect Predictions:** {len(failed_cases)} ({len(failed_cases)/metrics['total_tests']*100:.1f}%)
- **API Errors:** {len(metrics['errors'])}

---

## 📋 Performance by Category

{category_stats}

---

## ❌ Failed Cases (First 20)

{self._format_failed_cases(failed_cases)}

---

## 🎯 Recommendation

"""
        
        if metrics['precision'] >= 0.90 and metrics['recall'] >= 0.85 and metrics['f1_score'] >= 0.87:
            report += """✅ **PRODUCTION READY**

All Cahier des Charges targets met! The Presidio service demonstrates:
- Excellent precision (> 90%) - low false positive rate
- Strong recall (> 85%) - captures most PII entities
- Balanced F1-Score (> 87%) - optimal precision-recall trade-off

**Approved for production deployment.**
"""
        else:
            report += """⚠️ **IMPROVEMENT NEEDED**

Current performance does not meet all Cahier targets. Recommendations:
1. Review failed cases to identify patterns
2. Tune confidence thresholds
3. Enhance recognizer patterns
4. Add more context-aware rules
5. Re-evaluate after improvements
"""
        
        # Save report
        report_dir = os.path.join(os.path.dirname(__file__), "reports")
        os.makedirs(report_dir, exist_ok=True)
        
        report_file = os.path.join(report_dir, "presidio_evaluation_report.md")
        with open(report_file, "w", encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n✅ Report saved: {report_file}")
        
        # Also save metrics as JSON
        metrics_file = os.path.join(report_dir, "presidio_metrics.json")
        with open(metrics_file, "w", encoding='utf-8') as f:
            json.dump({
                "precision": metrics['precision'],
                "recall": metrics['recall'],
                "f1_score": metrics['f1_score'],
                "accuracy": metrics['accuracy'],
                "confusion_matrix": {
                    "TP": metrics['TP'],
                    "FP": metrics['FP'],
                    "FN": metrics['FN'],
                    "TN": metrics['TN']
                },
                "total_tests": metrics['total_tests'],
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"✅ Metrics JSON saved: {metrics_file}")
        
        return report
    
    def _calculate_category_metrics(self, results):
        """Calculate metrics per category"""
        categories = {}
        
        for r in results:
            cat = r['category']
            if cat not in categories:
                categories[cat] = {'total': 0, 'correct': 0}
            
            categories[cat]['total'] += 1
            if r['correct']:
                categories[cat]['correct'] += 1
        
        table = "| Category | Total | Correct | Accuracy |\\n"
        table += "|----------|-------|---------|----------|\\n"
        
        for cat, stats in sorted(categories.items()):
            accuracy = stats['correct'] / stats['total'] * 100 if stats['total'] > 0 else 0
            table += f"| {cat} | {stats['total']} | {stats['correct']} | {accuracy:.1f}% |\\n"
        
        return table
    
    def _format_failed_cases(self, failed_cases):
        """Format failed cases for report"""
        if not failed_cases:
            return "_No failed cases_ ✅"
        
        output = "| # | Text | Expected | Detected | Error |\\n"
        output += "|---|------|----------|----------|-------|\\n"
        
        for i, case in enumerate(failed_cases[:20], 1):
            expected = ', '.join(case['expected']) if case['expected'] else 'None'
            detected = ', '.join(case['detected']) if case['detected'] else 'None'
            
            if case['fp'] > 0 and case['fn'] > 0:
                error = f"FP:{case['fp']}, FN:{case['fn']}"
            elif case['fp'] > 0:
                error = f"False Positive ({case['fp']})"
            elif case['fn'] > 0:
                error = f"False Negative ({case['fn']})"
            else:
                error = "Other"
            
            output += f"| {i} | {case['text']} | {expected} | {detected} | {error} |\\n"
        
        return output

if __name__ == "__main__":
    try:
        evaluator = PresidioEvaluator()
        report = evaluator.generate_report()
        print("\n" + "="*70)
        print("EVALUATION COMPLETE!")
        print("="*70)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\\nPlease run generate_test_dataset.py first!")
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to Presidio service")
        print("\\nPlease ensure Presidio service is running on http://localhost:8003")
