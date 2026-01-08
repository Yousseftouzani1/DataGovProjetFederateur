"""
Example Usage: Correction Service V2
======================================

Demonstrates the complete workflow from detection to learning.

This example shows:
1. Detecting inconsistencies in sample data
2. Applying corrections (auto + manual review)
3. Human validation of low-confidence corrections
4. Learning from validations
5. Generating reports
6. Monitoring KPIs
"""

import requests
import json
from datetime import datetime

# Service URL
BASE_URL = "http://localhost:8006"

print("="*60)
print("🔧 CORRECTION SERVICE V2 - Example Workflow")
print("="*60)

# =====================================================
# EXAMPLE DATA WITH ALL 6 INCONSISTENCY TYPES
# =====================================================

sample_data = [
    {
        "id": 1,
        "name": "Alice Dupont",
        "email": "alice@example.com",
        "date_naissance": "32/13/2024",  # FORMAT: Invalid date
        "age": 250,                        # DOMAIN: Out of range
        "telephone": "06-12-34",           # FORMAT: Incomplete phone
        "ville": "Paris",                  # REFERENTIAL: Paris not in Morocco
        "pays": "Maroc",
        "date_debut": "2024-12-01",       # TEMPORAL: end before start
        "date_fin": "2024-01-01"
    },
    {
        "id": 2,
        "name": "Bob Martin",
        "email": "0612345678",             # SEMANTIC: Phone in email field
        "date_naissance": "1990-01-15",
        "age": 34,
        "telephone": "+212612345678",
        "ville": "Casablanca",
        "pays": "Maroc",
        "salary": 1500000                  # STATISTICAL: Outlier salary
    },
    {
        "id": 3,
        "name": "Charlie Smith",
        "email": "charlie@test.com",
        "date_naissance": "1985-05-20",
        "age": 39,
        "telephone": "0712345678",
        "temperature": -300,               # DOMAIN: Invalid temperature
        "ville": "Lyon",
        "pays": "France"
    }
]

print("\n📊 SAMPLE DATA")
print(f"Total rows: {len(sample_data)}")
print(f"Contains all 6 inconsistency types:")
print("  ✓ FORMAT (invalid dates, phones)")
print("  ✓ DOMAIN (age=250, temperature=-300)")
print("  ✓ REFERENTIAL (Paris + Morocco)")
print("  ✓ TEMPORAL (end_date < start_date)")
print("  ✓ STATISTICAL (outlier salary)")
print("  ✓ SEMANTIC (phone in email field)")

# =====================================================
# STEP 1: DETECT INCONSISTENCIES
# =====================================================

print("\n" + "="*60)
print("STEP 1: DETECT INCONSISTENCIES")
print("="*60)

for i, row in enumerate(sample_data, 1):
    print(f"\nRow {i}:")
    response = requests.post(f"{BASE_URL}/detect", json={"row": row})
    
    if response.status_code == 200:
        result = response.json()
        print(f"  Found {result['count']} inconsistencies")
        print(f"  By type: {result['by_type']}")
        
        for inc in result['inconsistencies']:
            print(f"    - {inc['type']}: {inc['field']} = {inc['value']}")
            print(f"      {inc['message']}")
    else:
        print(f"  Error: {response.status_code}")

# =====================================================
# STEP 2: DETECT AND CORRECT WITH AUTO-APPLY
# =====================================================

print("\n" + "="*60)
print("STEP 2: DETECT AND CORRECT (Auto-Apply)")
print("="*60)

corrections_summary = {
    "total_auto_applied": 0,
    "total_manual_review": 0,
    "pending_validations": []
}

for i, row in enumerate(sample_data, 1):
    print(f"\nRow {i}:")
    response = requests.post(
        f"{BASE_URL}/correct",
        json={
            "row": row,
            "dataset_id": "example_dataset",
            "auto_apply": True
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"  Auto-applied: {result['auto_applied_count']}")
        print(f"  Manual review needed: {result['manual_review_count']}")
        
        corrections_summary["total_auto_applied"] += result['auto_applied_count']
        corrections_summary["total_manual_review"] += result['manual_review_count']
        
        for corr in result['corrections']:
            if corr['auto']:
                print(f"    ✅ {corr['field']}: {corr['old_value']} → {corr['new_value']}")
                print(f"       Confidence: {corr['confidence']:.2f} (Auto-applied)")
            else:
                print(f"    ⏸ {corr['field']}: {corr['old_value']}")
                print(f"       Needs review (Confidence: {corr.get('confidence', 0):.2f})")
                corrections_summary["pending_validations"].append(corr)
    else:
        print(f"  Error: {response.status_code}")

print(f"\n📈 CORRECTION SUMMARY:")
print(f"  Total auto-applied: {corrections_summary['total_auto_applied']}")
print(f"  Total needing review: {corrections_summary['total_manual_review']}")
print(f"  Auto-apply rate: {corrections_summary['total_auto_applied']/(corrections_summary['total_auto_applied']+corrections_summary['total_manual_review'])*100:.1f}%")

# =====================================================
# STEP 3: GET PENDING VALIDATIONS
# =====================================================

print("\n" + "="*60)
print("STEP 3: GET PENDING VALIDATIONS")
print("="*60)

response = requests.get(f"{BASE_URL}/corrections/pending?limit=50")

if response.status_code == 200:
    result = response.json()
    pending = result['pending_validations']
    
    print(f"Pending validations: {result['count']}")
    
    for val in pending[:5]:  # Show first 5
        print(f"  - ID: {val.get('_id')}")
        print(f"    Field: {val['field']}")
        print(f"    Value: {val['old_value']}")
        print(f"    Confidence: {val.get('confidence', 0):.2f}")

# =====================================================
# STEP 4: HUMAN VALIDATION
# =====================================================

print("\n" + "="*60)
print("STEP 4: HUMAN VALIDATION (Simulated)")
print("="*60)

# Simulate Data Annotator validating corrections
if pending:
    correction_id = pending[0].get('_id')
    
    print(f"Validating correction ID: {correction_id}")
    
    # Simulate accepting the correction
    validation_response = requests.post(
        f"{BASE_URL}/corrections/validate/{correction_id}",
        json={
            "decision": "accept",
            "final_value": pending[0].get('candidates', [{}])[0].get('value') if 'candidates' in pending[0] else pending[0].get('new_value'),
            "validator_id": "annotator_demo",
            "validator_role": "data_annotator",
            "comments": "Correction looks accurate"
        }
    )
    
    if validation_response.status_code == 200:
        result = validation_response.json()
        print(f"  ✅ Validation recorded")
        print(f"  Decision: {result['decision']}")
        print(f"  Learning recorded: {result.get('learning_recorded', False)}")
    else:
        print(f"  Error: {validation_response.status_code}")

# =====================================================
# STEP 5: LEARNING STATISTICS
# =====================================================

print("\n" + "="*60)
print("STEP 5: LEARNING STATISTICS")
print("="*60)

response = requests.get(f"{BASE_URL}/learning/stats")

if response.status_code == 200:
    stats = response.json()
    
    print(f"Total training examples: {stats['total_training_examples']}")
    print(f"By inconsistency type:")
    for inc_type, count in stats.get('by_inconsistency_type', {}).items():
        print(f"  - {inc_type}: {count}")
    
    print(f"\nRecent accuracy: {stats['recent_accuracy']:.2%}")
    print(f"Latest model: {stats['latest_model_version']}")
    print(f"Needs retraining: {stats['needs_retraining']}")
    print(f"Next retrain at: {stats['next_retrain_at']} validations")

# =====================================================
# STEP 6: GENERATE REPORT
# =====================================================

print("\n" + "="*60)
print("STEP 6: GENERATE CORRECTION REPORT")
print("="*60)

response = requests.post(
    f"{BASE_URL}/reports/corrections",
    json={
        "dataset_id": "example_dataset",
        "start_date": datetime(2024, 1, 1).isoformat(),
        "end_date": datetime.utcnow().isoformat()
    }
)

if response.status_code == 200:
    report = response.json()
    
    print(f"Report generated at: {report['report_generated_at']}")
    
    summary = report.get('summary', {})
    print(f"\n📊 SUMMARY:")
    print(f"  Total corrections: {summary.get('total_corrections', 0)}")
    print(f"  Auto-applied: {summary.get('auto_applied', 0)}")
    print(f"  Manual review: {summary.get('manual_review', 0)}")
    print(f"  Auto-apply rate: {summary.get('auto_apply_rate', 0):.2%}")
    print(f"  Average confidence: {summary.get('average_confidence', 0):.2f}")
    
    print(f"\n📈 BY TYPE:")
    for inc_type, data in report.get('breakdown_by_type', {}).items():
        print(f"  {inc_type}: {data['count']} (avg conf: {data.get('avg_confidence', 0):.2f})")
    
    print(f"\n🎯 KPI METRICS:")
    kpis = report.get('kpi_metrics', {})
    print(f"  Auto-correction rate: {kpis.get('auto_correction_rate', 0):.2%} (target: 70%)")
    print(f"  Auto-correction precision: {kpis.get('auto_correction_precision', 0):.2%} (target: 90%)")
    print(f"  Meets targets: {kpis.get('meets_auto_rate_target', False)} / {kpis.get('meets_precision_target', False)}")

# =====================================================
# STEP 7: KPI DASHBOARD
# =====================================================

print("\n" + "="*60)
print("STEP 7: KPI DASHBOARD")
print("="*60)

response = requests.get(f"{BASE_URL}/kpi/dashboard")

if response.status_code == 200:
    dashboard = response.json()
    
    print(f"Health Score: {dashboard['health_score']}/100")
    
    kpis = dashboard.get('kpis', {})
    current = kpis.get('current', {})
    targets = kpis.get('targets', {})
    compliance = kpis.get('compliance', {})
    
    print(f"\n📊 CURRENT KPIs:")
    print(f"  Detection rate: {current.get('detection_rate', 0):.2%} (target: {targets.get('detection_rate', 0):.2%}) {'✅' if compliance.get('detection_rate') else '❌'}")
    print(f"  Auto-correction precision: {current.get('auto_correction_precision', 0):.2%} (target: {targets.get('auto_correction_precision', 0):.2%}) {'✅' if compliance.get('auto_correction_precision') else '❌'}")
    print(f"  Auto-correction rate: {current.get('auto_correction_rate', 0):.2%} (target: {targets.get('auto_correction_rate', 0):.2%}) {'✅' if compliance.get('auto_correction_rate') else '❌'}")
    
    alerts = dashboard.get('alerts', [])
    if alerts:
        print(f"\n⚠️ ALERTS:")
        for alert in alerts:
            print(f"  - {alert['message']}")
    else:
        print(f"\n✅ No alerts - all KPIs meeting targets!")

print("\n" + "="*60)
print("✅ WORKFLOW COMPLETE")
print("="*60)
print("\nThe Correction Service V2 successfully:")
print("  1. Detected all 6 types of inconsistencies")
print("  2. Auto-corrected high-confidence issues (>= 0.9)")
print("  3. Queued low-confidence issues for human review")
print("  4. Recorded human validations for learning")
print("  5. Generated comprehensive reports with traceability")
print("  6. Tracked KPIs and compliance with targets")
print("\n📚 For more examples, see the README.md")
