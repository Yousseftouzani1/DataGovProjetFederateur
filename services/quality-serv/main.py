"""
Quality Service - Tâche 8
ISO 25012 Data Quality Metrics Implementation (Mongo Persisted)

Features:
- 6 Quality Dimensions: Completeness, Accuracy, Consistency, Timeliness, Uniqueness, Validity
- Global weighted score
- PDF report generation
- MongoDB Persistence for Reports
"""
import io
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum

import uvicorn
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.database.mongodb import db

# Optional: PDF generation
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ fpdf not installed. Run: pip install fpdf2")

# ====================================================================
# MODELS
# ====================================================================

class QualityGrade(str, Enum):
    A = "A"  # >= 90
    B = "B"  # >= 75
    C = "C"  # >= 60
    D = "D"  # >= 40
    F = "F"  # < 40

class DimensionScore(BaseModel):
    dimension: str
    score: float
    weight: float
    weighted_score: float
    details: Optional[Dict[str, Any]] = None

class QualityReport(BaseModel):
    dataset_id: str
    evaluation_time: str
    dimensions: List[DimensionScore]
    global_score: float
    grade: QualityGrade
    recommendations: List[str]

class EvaluationConfig(BaseModel):
    weights: Optional[Dict[str, float]] = None  # Custom weights per dimension
    date_columns: Optional[List[str]] = None
    max_age_days: int = Field(default=365)
    key_columns: Optional[List[str]] = None
    validation_rules: Optional[Dict[str, List[Any]]] = None  # column -> allowed values
    regex_rules: Optional[Dict[str, str]] = None  # column -> regex pattern

# ====================================================================
# IN-MEMORY STORAGE (Datasets cache only)
# ====================================================================

datasets_store: Dict[str, Dict] = {} # Keeping heavy Cache in memory for performance

# ====================================================================
# ISO 25012 QUALITY DIMENSIONS
# ====================================================================

class QualityDimensions:
    """ISO 25012 Data Quality Model Implementation"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
    
    def completeness(self) -> Dict:
        """Completeness = (Non-null values / Total values) × 100"""
        total_cells = self.df.size
        non_null_cells = self.df.count().sum()
        
        column_scores = {}
        for col in self.df.columns:
            column_scores[col] = round((self.df[col].count() / len(self.df)) * 100, 2)
        
        overall_score = (non_null_cells / total_cells) * 100 if total_cells > 0 else 0
        
        return {
            "score": round(overall_score, 2),
            "details": {
                "total_cells": int(total_cells),
                "non_null_cells": int(non_null_cells),
                "column_scores": column_scores
            }
        }
    
    def accuracy(self, validation_rules: Dict[str, List[Any]] = None, regex_rules: Dict[str, str] = None) -> Dict:
        """Accuracy: Check for business rule violations (e.g. negative prices)"""
        total_validated = 0
        total_valid = 0
        
        # Simple Logic: Numeric columns shouldn't be negative (unless latch/long)
        for col in self.df.columns:
             if pd.api.types.is_numeric_dtype(self.df[col]):
                 non_null = self.df[col].dropna()
                 total_validated += len(non_null)
                 # Rule: value >= 0
                 valid_count = (non_null >= 0).sum()
                 total_valid += int(valid_count)
        
        score = (total_valid / total_validated * 100) if total_validated > 0 else 100.0
        
        return {
            "score": round(score, 2),
            "details": {"validated_cells": total_validated, "valid_cells": total_valid, "invalid_count": total_validated - total_valid}
        }
    
    def consistency(self) -> Dict:
        """Consistency: Check cross-field logic (Start Date < End Date)"""
        issues = 0
        total_checks = 0
        sample_rows = []
        
        # Heuristic: Find Start/End date columns
        cols = [c.lower() for c in self.df.columns]
        start_col = next((c for c in self.df.columns if 'start' in c.lower() or 'begin' in c.lower()), None)
        end_col = next((c for c in self.df.columns if 'end' in c.lower() or 'finish' in c.lower()), None)
        
        if start_col and end_col:
            try:
                # Convert to datetime if needed
                s_dates = pd.to_datetime(self.df[start_col], errors='coerce')
                e_dates = pd.to_datetime(self.df[end_col], errors='coerce')
                
                # Check where Start > End (Consistency Error)
                mask = (s_dates.notna()) & (e_dates.notna())
                total_checks = mask.sum()
                invalid_mask = (s_dates[mask] > e_dates[mask])
                invalid = invalid_mask.sum()
                issues = int(invalid)
                
                # Capture samples
                if issues > 0:
                    sample_indices = self.df[mask][invalid_mask].head(5).index.tolist()
                    sample_rows = self.df.loc[sample_indices].to_dict(orient='records')
                else:
                    sample_rows = []
            except:
                sample_rows = []
                pass
        
        score = 100.0
        if total_checks > 0:
            score = ((total_checks - issues) / total_checks) * 100
            
        return {"score": round(score, 2), "details": {"checks_performed": int(total_checks), "inconsistencies": issues, "samples": sample_rows}}
    
    def timeliness(self, date_columns: List[str] = None, max_age_days: int = 365*5) -> Dict:
        """Timeliness: Data shouldn't be too old (> 5 years)"""
        total_dates = 0
        fresh_dates = 0
        outdated_samples = [] # Initialize list

        cutoff = datetime.now() - timedelta(days=max_age_days)
        
        for col in self.df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                try:
                    dates = pd.to_datetime(self.df[col], errors='coerce').dropna()
                    if len(dates) > 0:
                        total_dates += len(dates)
                        fresh_mask = (dates >= cutoff)
                        fresh_dates += fresh_mask.sum()
                        
                        # Capture samples of old data
                        old_mask = ~fresh_mask
                        if old_mask.any():
                            outdated_indices = dates[old_mask].head(5).index.tolist()
                            # Get original rows for these indices
                            rows = self.df.loc[outdated_indices].to_dict(orient='records')
                            outdated_samples.extend(rows)
                except:
                    continue
        
        # Limit samples to 5 overall
        outdated_samples = outdated_samples[:5]
                    
        score = (fresh_dates / total_dates * 100) if total_dates > 0 else 100.0
        return {"score": round(score, 2), "details": {"total_dates": int(total_dates), "outdated_count": int(total_dates - fresh_dates), "samples": outdated_samples}}
    
    def uniqueness(self, key_columns: List[str] = None) -> Dict:
        """Uniqueness check"""
        if key_columns:
             subset = [c for c in key_columns if c in self.df.columns]
             if subset: unique = len(self.df.drop_duplicates(subset=subset))
             else: unique = len(self.df)
        else:
             unique = len(self.df.drop_duplicates())
             
        score = (unique / len(self.df)) * 100 if len(self.df) > 0 else 100
        return {"score": round(score, 2), "details": {"unique_rows": unique, "duplicate_rows": len(self.df) - unique}}
    
    def validity(self) -> Dict:
        """Validity: Regex check for Email and Phone (Moroccan context)"""
        import re
        total_checks = 0
        valid_count = 0
        invalid_samples = [] # Initialize list

        
        # Simple Regex Patterns
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        phone_pattern_ma = r'^(?:\+212|0)[5-7]\d{8}$' # Moroccan Logic
        
        for col in self.df.columns:
            c_lower = col.lower()
            pattern = None
            if 'email' in c_lower or 'mail' in c_lower:
                pattern = email_pattern
            elif 'phone' in c_lower or 'tel' in c_lower or 'mobile' in c_lower:
                pattern = phone_pattern_ma
            
            if pattern:
                 # Check string values
                 vals = self.df[col].astype(str)
                 matches = vals.str.match(pattern)
                 total_checks += len(vals)
                 valid_count += matches.sum()
                 
                 # Capture invalid samples
                 invalid_mask = ~matches
                 if invalid_mask.any():
                     bad_indices = vals[invalid_mask].head(5).index.tolist()
                     rows = self.df.loc[bad_indices].to_dict(orient='records')
                     # Add metadata about which column failed
                     for r in rows:
                         r["_error_column"] = col
                     invalid_samples.extend(rows)
                     
        invalid_samples = invalid_samples[:5]
        
        score = (valid_count / total_checks * 100) if total_checks > 0 else 100.0
        return {"score": round(score, 2), "details": {"checks": int(total_checks), "invalid_formats": int(total_checks - valid_count), "samples": invalid_samples}}

# ====================================================================
# QUALITY SCORER
# ====================================================================

class QualityScorer:
    """Calculate global quality score with weighted dimensions"""
    
    DEFAULT_WEIGHTS = {
        "completeness": 0.20, "accuracy": 0.25, "consistency": 0.15,
        "timeliness": 0.10, "uniqueness": 0.15, "validity": 0.15
    }
    
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS
        total = sum(self.weights.values())
        self.weights = {k: v/total for k, v in self.weights.items()}
    
    def calculate_global_score(self, dimension_scores: Dict[str, float]) -> float:
        global_score = 0.0
        for dim, score in dimension_scores.items():
            global_score += self.weights.get(dim, 0) * score
        return round(global_score, 2)
    
    def get_grade(self, score: float) -> QualityGrade:
        if score >= 90: return QualityGrade.A
        elif score >= 75: return QualityGrade.B
        elif score >= 60: return QualityGrade.C
        elif score >= 40: return QualityGrade.D
        else: return QualityGrade.F
    
    def generate_recommendations(self, dimension_results: Dict[str, Dict]) -> List[str]:
        recommendations = []
        for dim, result in dimension_results.items():
            if result["score"] < 90:
                recommendations.append(f"Improve {dim} (Current: {result['score']}%)")
        if not recommendations:
            recommendations.append("All dimensions look good.")
        return recommendations

# ====================================================================
# PDF REPORT GENERATOR
# ====================================================================

class PDFReportGenerator:
    """Generate PDF quality reports"""
    
    def generate(self, report: QualityReport, dataset_name: str = "Dataset") -> bytes:
        if not PDF_AVAILABLE:
            raise HTTPException(500, "PDF generation not available.")
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"Quality Report: {dataset_name}", ln=True, align='C')
        pdf.set_font("Arial", "", 12)
        pdf.ln(10)
        pdf.cell(0, 10, f"Grade: {report.grade.value} ({report.global_score}%)", ln=True)
        pdf.ln(5)
        
        for dim in report.dimensions:
            pdf.cell(0, 10, f"{dim.dimension}: {dim.score}%", ln=True)
            
        return pdf.output(dest='S').encode('latin-1')

# ====================================================================
# FASTAPI APP
# ====================================================================

app = FastAPI(
    title="Quality Service",
    description="Tâche 8 - ISO 25012 Data Quality Metrics (Mongo Persisted)",
    version="2.1.0"
)

@app.middleware("http")
async def set_root_path(request: Request, call_next):
    root_path = request.headers.get("x-forwarded-prefix")
    if root_path:
        request.scope["root_path"] = root_path
    response = await call_next(request)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    count = 0
    if db is not None:
        count = await db.quality_reports.count_documents({})
    return {
        "service": "Quality Service",
        "status": "running",
        "db_connected": db is not None,
        "total_evaluations": count
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/stats")
async def get_stats():
    """Get aggregate quality statistics for the dashboard"""
    if db is None:
        return {"average_score": 0, "total_evaluations": 0}
    
    try:
        pipeline = [
            {"$group": {
                "_id": None, 
                "avg_score": {"$avg": "$global_score"},
                "total_evals": {"$sum": 1}
            }}
        ]
        cursor = db.quality_reports.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        
        if result:
            return {
                "average_score": round(result[0]["avg_score"], 1),
                "total_evaluations": result[0]["total_evals"]
            }
        return {"average_score": 0, "total_evaluations": 0}
    except Exception as e:
        return {"error": str(e), "average_score": 0, "total_evaluations": 0}

@app.post("/evaluate/{dataset_id}", response_model=QualityReport)
async def evaluate_quality(dataset_id: str, config: EvaluationConfig = None):
    """Evaluate dataset quality against ISO 25012 dimensions"""
    import requests as req
    import traceback
    import os
    
    # Use Environment Variable for URL (Docker vs Localhost)
    CLEANING_URL = os.getenv("CLEANING_SERVICE_URL", "http://localhost:8004")
    
    print(f"🔍 Evaluating dataset {dataset_id}")
    
    try:
        # Auto-fetch from cleaning-service if not in cache
        if dataset_id not in datasets_store:
            try:
                # Try to fetch dataset from cleaning-service (Corrected Endpoint)
                resp = req.get(f"{CLEANING_URL}/api/v1/cleaning/dataset/{dataset_id}/json", timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    df = pd.DataFrame(data.get("data", []))
                    datasets_store[dataset_id] = {
                        "df": df,
                        "filename": data.get("filename", "auto_loaded"),
                        "upload_time": datetime.now().isoformat()
                    }
                    print(f"✅ Auto-loaded dataset {dataset_id} from cleaning-service")
                else:
                    raise HTTPException(404, f"Dataset not found in cache or cleaning-service (status: {resp.status_code})")
            except Exception as e:
                print(f"⚠️ Could not auto-fetch dataset: {e}")
                raise HTTPException(404, f"Dataset not found in cache. Error: {str(e)}")
        
        if config is None: config = EvaluationConfig()
        
        df = datasets_store[dataset_id]["df"]
        dims = QualityDimensions(df)
        scorer = QualityScorer(weights=config.weights)
        
        # Evaluate dimensions
        dimension_results = {
            "completeness": dims.completeness(),
            "accuracy": dims.accuracy(),
            "consistency": dims.consistency(),
            "timeliness": dims.timeliness(),
            "uniqueness": dims.uniqueness(),
            "validity": dims.validity()
        }
        
        # Calculate scores
        dimension_scores = {dim: result["score"] for dim, result in dimension_results.items()}
        global_score = scorer.calculate_global_score(dimension_scores)
        grade = scorer.get_grade(global_score)
        recommendations = scorer.generate_recommendations(dimension_results)
        
        dimensions = []
        for dim, result in dimension_results.items():
            weight = scorer.weights.get(dim, 0)
            dimensions.append(DimensionScore(
                dimension=dim,
                score=result["score"],
                weight=weight,
                weighted_score=round(weight * result["score"], 2),
                details=result.get("details")
            ))
        
        report = QualityReport(
            dataset_id=dataset_id,
            evaluation_time=datetime.now().isoformat(),
            dimensions=dimensions,
            global_score=global_score,
            grade=grade,
            recommendations=recommendations
        )
        
        # Persist report to MongoDB
        if db is not None:
            await db.quality_reports.insert_one(report.dict())
            
            # Log audit event for quality evaluation
            await db.audit_logs.insert_one({
                "service": "QUALITY",
                "action": "QUALITY_EVALUATION",
                "user": "system",  # TODO: Get from token
                "status": "INFO" if global_score >= 60 else "WARNING",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "dataset_id": dataset_id,
                    "global_score": global_score,
                    "grade": grade.value,
                    "recommendations_count": len(recommendations)
                }
            })
        
        return report

    except Exception as e:
        print(f"❌ Evaluation Error: {e}")
        traceback.print_exc()
        raise HTTPException(500, f"Evaluation Failed: {str(e)}")

@app.get("/report/{dataset_id}")
async def get_report(dataset_id: str):
    """Get latest report for dataset"""
    if db is not None:
        doc = await db.quality_reports.find_one({"dataset_id": dataset_id}, sort=[("evaluation_time", -1)])
        if doc: return QualityReport(**doc)
    
    raise HTTPException(404, "Report not found")

@app.get("/report/{dataset_id}/detailed")
async def get_detailed_report(dataset_id: str):
    """
    Get detailed breakdown for RGPD/ISO Compliance Audits.
    Includes row-level samples of quality issues.
    """
    if db is None:
        raise HTTPException(503, "Database not connected")
        
    doc = await db.quality_reports.find_one({"dataset_id": dataset_id}, sort=[("evaluation_time", -1)])
    if not doc:
        raise HTTPException(404, "Report not found")
        
    report = QualityReport(**doc)
    
    # 1. RGPD Compliance Indicators
    rgpd_compliance = {
        "integrity_check": "PASS" if any(d.dimension == "accuracy" and d.score >= 90 for d in report.dimensions) else "WARN",
        "minimization_check": "PASS" if any(d.dimension == "uniqueness" and d.score >= 95 for d in report.dimensions) else "FAIL",
        "storage_limitation": "PASS" if any(d.dimension == "timeliness" and d.score >= 90 for d in report.dimensions) else "WARN",
        "overall_status": "COMPLIANT" if report.global_score >= 85 else "NON_COMPLIANT"
    }
    
    # 2. Detailed Issues List (Flattened for UI Table)
    detailed_issues = []
    
    for dim in report.dimensions:
        if dim.details and "samples" in dim.details:
            for sample in dim.details["samples"]:
                detailed_issues.append({
                    "dimension": dim.dimension,
                    "issue_type": "Data Quality Violation",
                    "row_data": sample,
                    "remediation": f"Fix {dim.dimension} rule violation"
                })

    return {
        "dataset_id": dataset_id,
        "evaluation_iso_standard": "ISO 25012",
        "evaluation_date": report.evaluation_time,
        "global_quality_score": report.global_score,
        "rgpd_compliance_status": rgpd_compliance,
        "quality_dimensions_breakdown": report.dimensions,
        "audit_trail_samples": detailed_issues
    }

@app.get("/report/{dataset_id}/pdf")
async def get_pdf_report(dataset_id: str):
    """Download PDF quality report"""
    # Fetch report from DB
    report_data = None
    if db is not None:
        report_data = await db.quality_reports.find_one({"dataset_id": dataset_id}, sort=[("evaluation_time", -1)])
    
    if not report_data:
        raise HTTPException(404, "Report not found. Run /evaluate first.")
        
    report = QualityReport(**report_data)
    filename = datasets_store.get(dataset_id, {}).get("filename", "dataset")
    
    generator = PDFReportGenerator()
    pdf_bytes = generator.generate(report, dataset_name=filename)
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=quality_report_{dataset_id[:8]}.pdf"}
    )

@app.post("/datasets/{dataset_id}/register")
async def register_dataset(dataset_id: str, data: Dict):
    """Register a dataset from another service"""
    import pandas as pd
    
    if "records" in data:
        df = pd.DataFrame(data["records"])
    elif "df" in data:
        # Assuming df passed as dict-records or compatible
        df = pd.DataFrame(data["df"])
    else:
        raise HTTPException(400, "Provide 'records' in request body")
    
    datasets_store[dataset_id] = {
        "df": df,
        "filename": data.get("filename", "registered_dataset"),
        "upload_time": datetime.now().isoformat()
    }
    
    return {"status": "registered", "dataset_id": dataset_id, "rows": len(df)}

@app.post("/thresholds")
async def update_thresholds(weights: Dict[str, float]):
    """
    US-QUAL-04: Configure ISO 25012 dimensionality weights.
    """
    if db is not None:
        await db.quality_config.update_one(
            {"_id": "weights"},
            {"$set": {"weights": weights}},
            upsert=True
        )
        return {"status": "success", "message": "Quality thresholds updated", "new_weights": weights}
    return {"status": "error", "message": "Database not available"}

@app.get("/thresholds")
async def get_thresholds():
    """
    US-QUAL-05: Get Current ISO Config
    """
    if db is not None:
         doc = await db.quality_config.find_one({"_id": "weights"})
         if doc: return doc["weights"]
    return QualityScorer.DEFAULT_WEIGHTS

if __name__ == "__main__":
    print(f"\\n" + "="*60)
    print(f"📊 QUALITY SERVICE (MONGO) - Tâche 8")
    print(f"="*60)
    uvicorn.run("main:app", host="0.0.0.0", port=8008, reload=True)
