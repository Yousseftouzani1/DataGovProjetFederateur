"""
Correction Service V2 - Main API
==================================
Data Quality V2 - Section 8

Complete implementation of automatic inconsistency detection and correction
with ML-based intelligent suggestions, human validation, continuous learning,
and comprehensive reporting.

Features:
- 6 types of inconsistency detection (FORMAT, DOMAIN, REFERENTIAL, TEMPORAL, STATISTICAL, SEMANTIC)
- T5-based ML correction (auto-apply if confidence >= 0.9)
- Human validation workflow
- Continuous learning from validated corrections
- Correction reports with full traceability
- KPI tracking

User Stories:
- US-CORR-01: Automatic inconsistency detection
- US-CORR-02: Custom correction rules (Data Steward)
- US-CORR-03: Correction suggestions with confidence scores
- US-CORR-04: Human validation (Data Annotator)
- US-CORR-05: Learning from validations
- US-CORR-06: Correction reports with traceability
"""

import time
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.database.mongodb import db
from backend.models.detection_engine import DetectionEngine
from backend.models.correction_engine import CorrectionEngine
from backend.models.ml.text_correction_t5 import TextCorrectionT5
from backend.models.validation_manager import ValidationManager, ValidationDecision
from backend.models.learning_engine import LearningEngine
from backend.models.report_generator import ReportGenerator
from backend.models.kpi_tracker import KPITracker
from backend.models.inconsistency import Inconsistency

# =====================================================
# APP INITIALIZATION
# =====================================================

app = FastAPI(
    title="Correction Service V2 – Data Quality",
    description="Automatic Detection, Correction and Learning of Data Inconsistencies",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine instances
detection_engine = None
correction_engine = None
validation_manager = None
learning_engine = None
report_generator = None
kpi_tracker = None
t5_corrector = None

@app.on_event("startup")
async def startup():
    """Initialize all engines on startup - OPTIMIZED FOR PERFORMANCE"""
    global detection_engine, correction_engine, validation_manager
    global learning_engine, report_generator, kpi_tracker, t5_corrector
    
    print("="*60)
    print("🔧 CORRECTION SERVICE V2 - Data Quality")
    print("⚡ Performance Optimized Edition")
    print("="*60)
    
    # Import model cache for optimized ML operations
    from backend.models.model_cache import ModelCache
    
    # Initialize core engines (lightweight, no ML yet)
    print("📦 Initializing core engines...")
    detection_engine = DetectionEngine()
    correction_engine = CorrectionEngine()
    print("✅ Core engines ready")
    
    # Initialize T5 model with lazy loading (only when first needed)
    # This significantly reduces startup time
    print("🔄 T5 model will be lazy-loaded on first correction request")
    t5_corrector = None  # Will be loaded by ModelCache when needed
    
    # Initialize database-backed engines if MongoDB available
    if db is not None:
        validation_manager = ValidationManager(db)
        learning_engine = LearningEngine(db, None)  # T5 will be injected later
        report_generator = ReportGenerator(db)
        kpi_tracker = KPITracker(db)
        print("✅ All engines initialized with MongoDB")
        print("📊 Database collections ready")
    else:
        print("⚠️ Running without MongoDB - some features limited")
        print("💡 Set MONGODB_URI in .env to enable full features")
    
    print("✅ Correction Service V2 ready")
    print("⚡ Optimizations active:")
    print("   - Lazy T5 model loading")
    print("   - Prediction caching")
    print("   - Batch processing")
    print("   - Async database operations")
    print("="*60)
    print(f"🌐 API: http://localhost:8006")
    print(f"📚 Docs: http://localhost:8006/docs")
    print("="*60)

# =====================================================
# MODELS
# =====================================================

class DetectRequest(BaseModel):
    """Request to detect inconsistencies in a row"""
    row: Dict[str, Any]
    dataset_id: Optional[str] = None

class DetectResponse(BaseModel):
    """Response with detected inconsistencies"""
    inconsistencies: List[Inconsistency]
    count: int
    by_type: Dict[str, int]

class CorrectRequest(BaseModel):
    """Request to detect and correct inconsistencies"""
    row: Dict[str, Any]
    dataset_id: Optional[str] = None
    auto_apply: bool = True  # Auto-apply if confidence >= 0.9

class CorrectionDetail(BaseModel):
    """Single correction detail"""
    field: str
    old_value: Any
    new_value: Optional[Any] = None
    confidence: Optional[float] = None
    auto: bool
    status: str
    source: Optional[str] = None
    candidates: Optional[List[Dict[str, Any]]] = None

class CorrectResponse(BaseModel):
    """Response with corrected row and correction log"""
    corrected_row: Dict[str, Any]
    corrections: List[CorrectionDetail]
    auto_applied_count: int
    manual_review_count: int

class ValidateRequest(BaseModel):
    """Request to validate a correction"""
    decision: ValidationDecision
    final_value: Any
    comments: Optional[str] = None
    validator_id: str
    validator_role: str = "data_annotator"

class BatchValidateRequest(BaseModel):
    """Request to validate multiple corrections"""
    validations: List[Dict[str, Any]]
    validator_id: str
    validator_role: str = "data_annotator"

class ReportRequest(BaseModel):
    """Request to generate correction report"""
    dataset_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

# =====================================================
# HEALTH & STATUS  
# =====================================================

@app.get("/")
async def root():
    """Service information"""
    stats = {}
    
    if db:
        stats["total_corrections"] = await db.correction_validations.count_documents({})
        stats["training_examples"] = await db.correction_training_data.count_documents({})
    
    return {
        "service": "Correction Service V2",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "6 types of inconsistency detection",
            "T5-based ML correction",
            "Human validation workflow",
            "Continuous learning",
            "Comprehensive reporting",
            "KPI tracking"
        ],
        "stats": stats,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
def health():
    """Health check"""
    # Check if T5 model is loaded (via cache)
    from backend.models.model_cache import ModelCache
    
    return {
        "status": "healthy",
        "t5_model_loaded": ModelCache._t5_model is not None,
        "database_connected": db is not None,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/performance")
async def get_performance_stats():
    """
    Get performance statistics and cache efficiency
    
    Shows ML model cache hit rates and optimization metrics
    """
    from backend.models.model_cache import ModelCache
    
    cache_stats = ModelCache.get_stats()
    
    perf_stats = {
        "ml_cache": cache_stats,
        "optimizations": {
            "lazy_model_loading": True,
            "prediction_caching": True,
            "batch_processing": True,
            "async_operations": True
        }
    }
    
    # Add database performance if available
    if kpi_tracker:
        db_perf = await kpi_tracker.get_performance_stats(days=1)
        perf_stats["processing_performance"] = db_perf
    
    return perf_stats


# =====================================================
# DETECTION - US-CORR-01
# =====================================================

@app.post("/detect", response_model=DetectResponse)
def detect_inconsistencies(request: DetectRequest):
    """
    Detect inconsistencies in a data row
    
    Detects all 6 types of inconsistencies:
    - FORMAT: Invalid dates, emails, phones,etc.
    - DOMAIN: Out-of-range values (age=250, temperature=-300)
    - REFERENTIAL: Invalid combinations (Paris + Morocco)
    - TEMPORAL: Date ordering issues
    - STATISTICAL: Outliers
    - SEMANTIC: Type mismatches (email contains phone)
    """
    inconsistencies = detection_engine.detect(request.row)
    
    # Breakdown by type
    by_type = {}
    for inc in inconsistencies:
        inc_type = inc.type
        by_type[inc_type] = by_type.get(inc_type, 0) + 1
    
    return DetectResponse(
        inconsistencies=inconsistencies,
        count=len(inconsistencies),
        by_type=by_type
    )

# =====================================================
# CORRECTION - US-CORR-02, US-CORR-03
# =====================================================

@app.post("/correct", response_model=CorrectResponse)
async def correct_inconsistencies(request: CorrectRequest, background_tasks: BackgroundTasks):
    """
    Detect and correct inconsistencies with intelligent suggestions
    
    Algorithm 6 (Section 8.5):
    1. Detect inconsistencies
    2. Generate rule-based correction candidates
    3. Generate ML-based candidates (T5)
    4. Select best candidate
    5. Auto-apply if confidence >= 0.9
    6. Queue for human review if confidence < 0.9
    """
    start_time = time.time()
    
    # Step 1: Detect inconsistencies
    inconsistencies = detection_engine.detect(request.row)
    
    if not inconsistencies:
        return CorrectResponse(
            corrected_row=request.row,
            corrections=[],
            auto_applied_count=0,
            manual_review_count=0
        )
    
    # Step 2-5: Correct using Algorithm 6
    corrected_row, corrections = correction_engine.correct(
        row=request.row,
        inconsistencies=inconsistencies
    )
    
    # Apply auto-corrections if requested
    auto_applied = 0
    manual_review = 0
    
    for corr in corrections:
        if corr.get("auto", False) and request.auto_apply:
            auto_applied += 1
        elif corr.get("status") == "REQUIRES_REVIEW":
            manual_review += 1
            
            # Add to validation queue
            if validation_manager:
                await validation_manager.queue.add_to_queue(
                    correction={
                        **corr,
                        "dataset_id": request.dataset_id,
                        "row_context": request.row
                    },
                    priority=5
                )
    
    # Track processing time (KPI)
    processing_time = time.time() - start_time
    
    if kpi_tracker:
        background_tasks.add_task(
            kpi_tracker.track_processing_time,
            num_rows=1,
            processing_time_seconds=processing_time,
            dataset_id=request.dataset_id
        )
    
    return CorrectResponse(
        corrected_row=corrected_row,
        corrections=[CorrectionDetail(**c) for c in corrections],
        auto_applied_count=auto_applied,
        manual_review_count=manual_review
    )

# =====================================================
# VALIDATION - US-CORR-04
# =====================================================

@app.get("/corrections/pending")
async def get_pending_corrections(
    validator_id: Optional[str] = None,
    limit: int = 50,
    min_confidence: float = 0.0,
    max_confidence: float = 0.9
):
    """
    Get corrections awaiting human validation
    
    Returns corrections with confidence < 0.9 that need review
    """
    if not validation_manager:
        raise HTTPException(500, "Validation manager not initialized")
    
    pending = await validation_manager.queue.get_pending(
        validator_id=validator_id,
        limit=limit,
        min_confidence=min_confidence,
        max_confidence=max_confidence
    )
    
    return {
        "pending_validations": pending,
        "count": len(pending)
    }

@app.post("/corrections/validate/{correction_id}")
async def validate_correction(
    correction_id: str,
    request: ValidateRequest,
    background_tasks: BackgroundTasks
):
    """
    Validate a correction (accept, reject, or modify)
    
    Creates training example for continuous learning
    """
    if not validation_manager:
        raise HTTPException(500, "Validation manager not initialized")
    
    result = await validation_manager.validate_correction(
        correction_id=correction_id,
        decision=request.decision,
        final_value=request.final_value,
        validator_id=request.validator_id,
        validator_role=request.validator_role,
        comments=request.comments
    )
    
    # Trigger learning in background
    if learning_engine:
        background_tasks.add_task(
            learning_engine.record_validation,
            correction_id,
            result
        )
    
    return result

@app.post("/corrections/batch-validate")
async def batch_validate_corrections(
    request: BatchValidateRequest,
    background_tasks: BackgroundTasks
):
    """
    Validate multiple corrections in batch
    
    Efficient for bulk validation by Data Annotators
    """
    if not validation_manager:
        raise HTTPException(500, "Validation manager not initialized")
    
    result = await validation_manager.batch_validate(
        validations=request.validations,
        validator_id=request.validator_id,
        validator_role=request.validator_role
    )
    
    return result

@app.get("/validation/stats")
async def get_validation_stats(
    validator_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    Get validation statistics
    
    Track validator performance and activity
    """
    if not validation_manager:
        raise HTTPException(500, "Validation manager not initialized")
    
    stats = await validation_manager.get_validation_stats(
        validator_id=validator_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return stats

# =====================================================
# LEARNING - US-CORR-05
# =====================================================

@app.get("/learning/stats")
async def get_learning_stats():
    """
    Get continuous learning statistics
    
    Shows:
    - Total training examples
    - Breakdown by inconsistency type
    - Recent accuracy
    - Model version info
    - Retraining status
    """
    if not learning_engine:
        raise HTTPException(500, "Learning engine not initialized")
    
    stats = await learning_engine.get_learning_stats()
    return stats

@app.post("/learning/retrain")
async def retrain_model(
    num_epochs: int = 3,
    force: bool = False
):
    """
    Trigger T5 model retraining
    
    Args:
        num_epochs: Number of training epochs
        force: Force retraining even if threshold not reached
        
    Note: This may take several minutes
    """
    if not learning_engine:
        raise HTTPException(500, "Learning engine not initialized")
    
    result = await learning_engine.retrain_model(
        num_epochs=num_epochs,
        force=force
    )
    
    return result

@app.get("/learning/accuracy-trend")
async def get_accuracy_trend(months: int = 6):
    """
    Get monthly accuracy improvement trend
    
    KPI Target: +5% accuracy per month
    """
    if not learning_engine:
        raise HTTPException(500, "Learning engine not initialized")
    
    trend = await learning_engine.get_accuracy_trend(months=months)
    return trend

# =====================================================
# REPORTING - US-CORR-06
# =====================================================

@app.post("/reports/corrections")
async def generate_correction_report(request: ReportRequest):
    """
    Generate comprehensive correction report with traceability
    
    Includes:
    - Summary statistics
    - Breakdown by type and field
    - Confidence distributions
    - Timeline
    - Validator contributions
    - Correction details
    - KPI metrics
    """
    if not report_generator:
        raise HTTPException(500, "Report generator not initialized")
    
    report = await report_generator.generate_correction_report(
        dataset_id=request.dataset_id,
        start_date=request.start_date,
        end_date=request.end_date
    )
    
    return report

@app.post("/reports/export")
async def export_report(
    report_data: Dict[str, Any],
    format: str = "json",
    output_path: Optional[str] = None
):
    """
    Export report to file
    
    Formats: json, excel
    """
    if not report_generator:
        raise HTTPException(500, "Report generator not initialized")
    
    result = await report_generator.export_report(
        report=report_data,
        format=format,
        output_path=output_path
    )
    
    return result

# =====================================================
# KPI TRACKING - Section 8.7
# =====================================================

@app.get("/kpi/summary")
async def get_kpi_summary(
    dataset_id: Optional[str] = None,
    days: int = 30
):
    """
    Get KPI summary
    
    KPIs (Section 8.7):
    - Detection rate > 95%
    - Auto-correction precision > 90%
    - Auto-correction rate > 70%
    - Processing time < 5s per 1000 rows
    - Monthly accuracy improvement +5%
    """
    if not kpi_tracker:
        raise HTTPException(500, "KPI tracker not initialized")
    
    summary = await kpi_tracker.get_kpi_summary(
        dataset_id=dataset_id,
        days=days
    )
    
    return summary

@app.get("/kpi/dashboard")
async def get_kpi_dashboard():
    """
    Get comprehensive KPI dashboard with alerts
    
    Returns:
    - Health score (0-100)
    - All KPIs with compliance status
    - Performance metrics
    - Alerts for KPIs not meeting targets
    """
    if not kpi_tracker:
        raise HTTPException(500, "KPI tracker not initialized")
    
    dashboard = await kpi_tracker.get_dashboard_metrics()
    return dashboard

@app.post("/kpi/snapshot")
async def record_kpi_snapshot(
    dataset_id: Optional[str] = None,
    custom_metrics: Optional[Dict[str, float]] = None
):
    """
    Record a KPI snapshot for tracking
    """
    if not kpi_tracker:
        raise HTTPException(500, "KPI tracker not initialized")
    
    snapshot = await kpi_tracker.record_kpi_snapshot(
        dataset_id=dataset_id,
        custom_metrics=custom_metrics
    )
    
    return snapshot

# =====================================================
# RULES MANAGEMENT - US-CORR-02
# =====================================================

@app.get("/rules")
def get_correction_rules():
    """
    Get all correction rules
    
    Rules are defined in correction_rules.yaml
    Managed by Data Stewards
    """
    from backend.models.rules_loader import load_rules
    
    rules = load_rules()
    
    return {
        "rules": rules,
        "source": "correction_rules.yaml"
    }

@app.post("/rules/reload")
def reload_correction_rules():
    """
    Reload correction rules from YAML
    
    Force reload to pick up changes made by Data Stewards
    """
    from backend.models.rules_loader import load_rules
    
    rules = load_rules(force_reload=True)
    
    # Reinitialize engines with new rules
    global detection_engine, correction_engine
    detection_engine = DetectionEngine()
    correction_engine = CorrectionEngine()
    
    return {
        "status": "reloaded",
        "message": "Correction rules reloaded successfully"
    }

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔧 CORRECTION SERVICE V2 - Data Quality")
    print("="*60)
    uvicorn.run("main:app", host="0.0.0.0", port=8006, reload=True)
