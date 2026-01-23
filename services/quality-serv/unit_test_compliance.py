
import sys
import os
import pandas as pd
import unittest

# Add service directory to path to allow imports
SERVICE_DIR = os.path.join(os.getcwd(), "services", "quality-serv")
sys.path.append(SERVICE_DIR)

# Mock DB to avoid import errors or side effects if possible
# But since main.py imports it at top level, we rely on its try-except or just let it init
try:
    from main import QualityDimensions, QualityScorer, EvaluationConfig
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print(f"PYTHONPATH: {sys.path}")
    sys.exit(1)

class TestQualityCompliance(unittest.TestCase):
    
    def setUp(self):
        # Mock Data matching the manual test case
        self.data = [
            {"id": 1, "email": "valid@test.com", "phone": "0661123456", "age": 25, "start_date": "2023-01-01", "end_date": "2023-01-10"},
            {"id": 2, "email": None, "phone": "0661123456", "age": 30, "start_date": "2023-01-01", "end_date": "2023-01-10"},
            {"id": 3, "email": "test3@test.com", "phone": "12345", "age": 35, "start_date": "2023-01-01", "end_date": "2023-01-10"},
            {"id": 4, "email": "test4@test.com", "phone": "0661123456", "age": 40, "start_date": "2023-02-01", "end_date": "2023-01-01"},
            {"id": 5, "email": "test5@test.com", "phone": "0661123456", "age": -5, "start_date": "2023-01-01", "end_date": "2023-01-10"},
            {"id": 1, "email": "valid@test.com", "phone": "0661123456", "age": 25, "start_date": "2023-01-01", "end_date": "2023-01-10"},
            {"id": 7, "email": "old@test.com", "phone": "0661123456", "age": 50, "start_date": "2015-01-01", "end_date": "2015-01-10"}
        ]
        self.df = pd.DataFrame(self.data)
        self.dims = QualityDimensions(self.df)
    
    def test_completeness(self):
        # 1 missing value (email) out of 7*6=42 cells.
        # Non-null = 41. (41/42)*100 = 97.62
        res = self.dims.completeness()
        self.assertAlmostEqual(res["score"], 97.62, places=1)
        print(f"✅ Completeness: {res['score']}% (Expected ~97.6%)")

    def test_accuracy(self):
        # Negative age is invalid.
        # Numeric columns: id (7 valid), age (6 valid, 1 invalid).
        # Total numeric checks = 14. Valid = 13.
        # Score = 13/14 = 92.86%
        # Wait, implementation iterates columns.
        # id: 7 valid.
        # age: 7 values, 1 is -5. 6 valid.
        # total validated = 14. total valid = 13.
        res = self.dims.accuracy()
        self.assertAlmostEqual(res["score"], 92.86, places=1)
        print(f"✅ Accuracy: {res['score']}% (Expected ~92.9%)")

    def test_consistency(self):
        # Row 4: start (Feb) > end (Jan). 1 Error.
        # 7 rows checked. 6 consistent.
        # Score: 6/7 = 85.71%
        res = self.dims.consistency()
        self.assertAlmostEqual(res["score"], 85.71, places=1)
        print(f"✅ Consistency: {res['score']}% (Expected ~85.7%)")

    def test_uniqueness(self):
        # Row 6 is specific duplicate of Row 1.
        # Unique rows = 6. Total = 7.
        # Score = 6/7 = 85.71%
        res = self.dims.uniqueness()
        self.assertAlmostEqual(res["score"], 85.71, places=1)
        print(f"✅ Uniqueness: {res['score']}% (Expected ~85.7%)")

    def test_timeliness(self):
        # Row 7 is old (2015).
        # Dates are relative to NOW (2026).
        # 2023 is 3 years old. 2015 is 11 years old.
        # Threshold: 5 years (365*5).
        # Fresh: 2023 dates (12). Old: 2015 dates (2).
        # Score = 12/14 = 85.71%
        res = self.dims.timeliness(max_age_days=365*5)
        print(f"DEBUG TIMELINESS: {res}")
        self.assertAlmostEqual(res["score"], 85.71, places=1)
        print(f"✅ Timeliness: {res['score']}% (Expected ~85.7%)")

    def test_validity(self):
        # Emails: 7 rows. 1 None. 6 Strings.
        # Valid: valid, test3, test4, test5, valid, old. (6 valid).
        # Phone: 7 rows.
        # Valid: 0661... (Row 1,2,4,5,6,7). 6 valid.
        # Invalid: "12345" (Row 3).
        # Total checks: 6 emails + 7 phones = 13?
        # Implementation: vals = df[col].astype(str). None becomes "None".
        # "None" matches email regex? No.
        # So 6 valid emails (if regex matches them).
        # 6 valid phones.
        # Total checks = 7 (email col) + 7 (phone col) = 14.
        # Valid count = 6 (emails) + 6 (phones) = 12.
        # Score = 12/14 = 85.71%
        res = self.dims.validity()
        self.assertAlmostEqual(res["score"], 85.71, places=1)
        print(f"✅ Validity: {res['score']}% (Expected ~85.7%)")

    def test_recommendations(self):
        # Check if recommendations are generated for low scores
        scorer = QualityScorer()
        results = {
            "consistency": {"score": 50.0},
            "accuracy": {"score": 95.0}
        }
        recs = scorer.generate_recommendations(results)
        self.assertTrue(any("Consistency" in r for r in recs))
        print(f"✅ Recommendations Generated: {recs}")

if __name__ == '__main__':
    print("="*60)
    print("🧪 UNIT TEST: ISO 25012 COMPLIANCE")
    print("="*60)
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
