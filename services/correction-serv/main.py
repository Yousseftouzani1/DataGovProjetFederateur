from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime
import uuid

from database.mongodb import db
from models.detection_engine import DetectionEngine
from models.correction_engine import CorrectionEngine
from models.learning import LearningEngine
from models.inconsistency import Inconsistency

# =====================================================
# APP INITIALIZATION
# =====================================================

app = FastAPI(
    title="Correction Service – Data Quality V2",
    description="Automatic Detection, Correction and Learning of Data Inconsistencies",
    version="1.0.0"
)

detection_engine = DetectionEngine()
correction_engine = CorrectionEngine()
learning_engine = LearningEngine()

# =====================================================
# API SCHEMAS
# =====================================================

class DetectRequest(BaseModel):
    row: Dict[str, Any]


class DetectResponse(BaseModel):
    inconsistencies: List[Inconsistency]


class CorrectRequest(BaseModel):
    row: Dict[str, Any]


class CorrectionResult(BaseModel):
    field: str
    old_value: Any
    new_value: Any | None = None
    confidence: float | None = None
    auto: bool
    status: str
    source: str | None = None
    candidates: List[Dict[str, Any]] | None = None


class CorrectResponse(BaseModel):
    corrected_row: Dict[str, Any]
    corrections: List[CorrectionResult]


class ValidateRequest(BaseModel):
    correction: Dict[str, Any]
    decision: str = Field(..., description="ACCEPTED | REJECTED | MODIFIED")


# =====================================================
# HEALTH
# =====================================================

@app.get("/health")
def health():
    return {
        "service": "Correction Service",
        "status": "UP",
        "timestamp": datetime.utcnow().isoformat()
    }

# =====================================================
# 1️⃣ DETECT — US-CORR-01
# =====================================================

@app.post("/detect", response_model=DetectResponse)
def detect(request: DetectRequest):
    inconsistencies = detection_engine.detect(request.row)
    return DetectResponse(inconsistencies=inconsistencies)

# =====================================================
# 2️⃣ DETECT + CORRECT — US-CORR-02 / 03
# =====================================================

@app.post("/correct", response_model=CorrectResponse)
def correct(request: CorrectRequest):
    inconsistencies = detection_engine.detect(request.row)

    corrected_row, corrections = correction_engine.correct(
        row=request.row,
        inconsistencies=inconsistencies
    )

    # Traçabilité – corrections en attente de validation
    if db:
        for corr in corrections:
            db.pending_corrections.insert_one({
                "id": str(uuid.uuid4()),
                "row_before": request.row,
                "row_after": corrected_row,
                "correction": corr,
                "created_at": datetime.utcnow()
            })

    return CorrectResponse(
        corrected_row=corrected_row,
        corrections=corrections
    )

# =====================================================
# 3️⃣ VALIDATE — US-CORR-04 / 05
# =====================================================

@app.post("/validate")
def validate(request: ValidateRequest):
    decision = request.decision.upper()
    if decision not in {"ACCEPTED", "REJECTED", "MODIFIED"}:
        raise HTTPException(status_code=400, detail="Invalid decision")

    validation_record = {
        **request.correction,
        "decision": decision,
        "validated_at": datetime.utcnow()
    }

    # Apprentissage supervisé
    learning_engine.learn_from_validation(validation_record)

    # Traçabilité
    if db:
        db.validated_corrections.insert_one(validation_record)

    return {
        "status": "OK",
        "decision": decision,
        "message": "Validation processed successfully"
    }

# =====================================================
# 4️⃣ LEARNING EXPORT — US-CORR-06
# =====================================================

@app.get("/learning/export")
def export_learning():
    return learning_engine.export_learning_state()
