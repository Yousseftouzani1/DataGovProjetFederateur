"""
Quality Service - Tâche 8
ISO 25012 Data Quality Metrics Implementation

Features:
- 6 Quality Dimensions: Completeness, Accuracy, Consistency, Timeliness, Uniqueness, Validity
- Global weighted score
- PDF report generation
- Quality thresholds and grading
"""
import io
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum

import uvicorn
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

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
# IN-MEMORY STORAGE (shared with cleaning-serv in production)
# ====================================================================

datasets_store: Dict[str, Dict] = {}
reports_store: Dict[str, QualityReport] = {}

# ====================================================================
# ISO 25012 QUALITY DIMENSIONS
# ====================================================================

class QualityDimensions:
    """
    ISO 25012 Data Quality Model Implementation
    
    Dimensions:
    1. Completeness - Degree to which data has values for all attributes
    2. Accuracy - Degree of correctness and precision
    3. Consistency - Degree of coherence and absence of contradictions
    4. Timeliness - Degree to which data is sufficiently up-to-date
    5. Uniqueness - Degree to which there is no duplicated data
    6. Validity - Degree to which data conforms to defined format/rules
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
    
    def completeness(self) -> Dict:
        """
        Completeness = (Non-null values / Total values) × 100
        Measures the percentage of non-missing data
        """
        total_cells = self.df.size
        non_null_cells = self.df.count().sum()
        
        # Per-column completeness
        column_scores = {}
        for col in self.df.columns:
            col_total = len(self.df)
            col_non_null = self.df[col].count()
            column_scores[col] = round((col_non_null / col_total) * 100, 2)
        
        overall_score = (non_null_cells / total_cells) * 100 if total_cells > 0 else 0
        
        return {
            "score": round(overall_score, 2),
            "details": {
                "total_cells": int(total_cells),
                "non_null_cells": int(non_null_cells),
                "null_cells": int(total_cells - non_null_cells),
                "column_scores": column_scores,
                "worst_columns": sorted(column_scores.items(), key=lambda x: x[1])[:3]
            }
        }
    
    def accuracy(self, validation_rules: Dict[str, List[Any]] = None,
                 regex_rules: Dict[str, str] = None) -> Dict:
        """
        Accuracy = (Valid values / Total non-null values) × 100
        Measures correctness against defined rules
        """
        import re
        
        total_validated = 0
        total_valid = 0
        column_accuracy = {}
        
        # Default validation: check numeric columns for reasonable ranges
        for col in self.df.columns:
            if pd.api.types.is_numeric_dtype(self.df[col]):
                # Check for realistic values (not negative when shouldn't be)
                non_null = self.df[col].dropna()
                total_validated += len(non_null)
                
                # Simple accuracy: check if values are within mean ± 3*std
                if len(non_null) > 0:
                    mean = non_null.mean()
                    std = non_null.std()
                    if std > 0:
                        valid = ((non_null >= mean - 3*std) & (non_null <= mean + 3*std)).sum()
                    else:
                        valid = len(non_null)
                    total_valid += valid
                    column_accuracy[col] = round((valid / len(non_null)) * 100, 2)
        
        # Apply custom validation rules
        if validation_rules:
            for col, allowed_values in validation_rules.items():
                if col in self.df.columns:
                    non_null = self.df[col].dropna()
                    total_validated += len(non_null)
                    valid = non_null.isin(allowed_values).sum()
                    total_valid += valid
                    column_accuracy[col] = round((valid / len(non_null)) * 100, 2) if len(non_null) > 0 else 100
        
        # Apply regex rules
        if regex_rules:
            for col, pattern in regex_rules.items():
                if col in self.df.columns:
                    non_null = self.df[col].dropna().astype(str)
                    total_validated += len(non_null)
                    valid = non_null.str.match(pattern, na=False).sum()
                    total_valid += valid
                    column_accuracy[col] = round((valid / len(non_null)) * 100, 2) if len(non_null) > 0 else 100
        
        overall_score = (total_valid / total_validated) * 100 if total_validated > 0 else 100
        
        return {
            "score": round(overall_score, 2),
            "details": {
                "total_validated": total_validated,
                "total_valid": total_valid,
                "column_accuracy": column_accuracy
            }
        }
    
    def consistency(self) -> Dict:
        """
        Consistency = Check for logical contradictions
        Examples: birth_date < today, start_date < end_date, age matches birth_date
        """
        issues = []
        consistency_score = 100.0
        
        # Check for common consistency patterns
        columns_lower = {c.lower(): c for c in self.df.columns}
        
        # Date range checks
        date_pairs = [
            ("start_date", "end_date"),
            ("date_debut", "date_fin"),
            ("created_at", "updated_at"),
            ("birth_date", "death_date")
        ]
        
        for start_col, end_col in date_pairs:
            start_actual = columns_lower.get(start_col.replace("_", ""))
            end_actual = columns_lower.get(end_col.replace("_", ""))
            
            if start_actual and end_actual:
                try:
                    start_dates = pd.to_datetime(self.df[start_actual], errors='coerce')
                    end_dates = pd.to_datetime(self.df[end_actual], errors='coerce')
                    
                    # Both non-null
                    valid_mask = start_dates.notna() & end_dates.notna()
                    if valid_mask.sum() > 0:
                        inconsistent = (start_dates > end_dates) & valid_mask
                        if inconsistent.sum() > 0:
                            issues.append(f"{start_actual} > {end_actual}: {inconsistent.sum()} rows")
                            consistency_score -= (inconsistent.sum() / valid_mask.sum()) * 20
                except:
                    pass
        
        # Check for impossible values
        for col in self.df.columns:
            col_lower = col.lower()
            
            # Age should be reasonable
            if "age" in col_lower and pd.api.types.is_numeric_dtype(self.df[col]):
                invalid_age = ((self.df[col] < 0) | (self.df[col] > 150)).sum()
                if invalid_age > 0:
                    issues.append(f"{col}: {invalid_age} impossible ages")
                    consistency_score -= (invalid_age / len(self.df)) * 10
            
            # Percentage should be 0-100
            if "percent" in col_lower or "pourcent" in col_lower:
                if pd.api.types.is_numeric_dtype(self.df[col]):
                    invalid = ((self.df[col] < 0) | (self.df[col] > 100)).sum()
                    if invalid > 0:
                        issues.append(f"{col}: {invalid} values outside 0-100 range")
                        consistency_score -= (invalid / len(self.df)) * 10
        
        return {
            "score": round(max(0, consistency_score), 2),
            "details": {
                "issues_found": len(issues),
                "issues": issues[:10]  # Limit to 10
            }
        }
    
    def timeliness(self, date_columns: List[str] = None, max_age_days: int = 365) -> Dict:
        """
        Timeliness = (Recent records / Total records) × 100
        Measures how up-to-date the data is
        """
        if date_columns is None:
            # Auto-detect date columns
            date_columns = []
            for col in self.df.columns:
                col_lower = col.lower()
                if any(kw in col_lower for kw in ["date", "time", "created", "updated", "timestamp"]):
                    date_columns.append(col)
        
        if not date_columns:
            # No date columns found, assume 100% timely
            return {
                "score": 100.0,
                "details": {"message": "No date columns to evaluate"}
            }
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        total_dated = 0
        total_recent = 0
        column_timeliness = {}
        
        for col in date_columns:
            if col not in self.df.columns:
                continue
            
            try:
                dates = pd.to_datetime(self.df[col], errors='coerce')
                non_null = dates.dropna()
                
                if len(non_null) > 0:
                    recent = (non_null >= cutoff_date).sum()
                    total_dated += len(non_null)
                    total_recent += recent
                    column_timeliness[col] = round((recent / len(non_null)) * 100, 2)
            except:
                pass
        
        overall_score = (total_recent / total_dated) * 100 if total_dated > 0 else 100
        
        return {
            "score": round(overall_score, 2),
            "details": {
                "max_age_days": max_age_days,
                "cutoff_date": cutoff_date.isoformat(),
                "total_dated_records": total_dated,
                "recent_records": total_recent,
                "column_timeliness": column_timeliness
            }
        }
    
    def uniqueness(self, key_columns: List[str] = None) -> Dict:
        """
        Uniqueness = (Unique records / Total records) × 100
        Measures absence of data duplication
        """
        total_rows = len(self.df)
        
        if key_columns:
            # Check uniqueness on specific key columns
            subset = [c for c in key_columns if c in self.df.columns]
            if subset:
                unique_rows = len(self.df.drop_duplicates(subset=subset))
            else:
                unique_rows = len(self.df.drop_duplicates())
        else:
            unique_rows = len(self.df.drop_duplicates())
        
        duplicate_count = total_rows - unique_rows
        
        # Per-column uniqueness
        column_uniqueness = {}
        for col in self.df.columns:
            unique_vals = self.df[col].nunique()
            total_non_null = self.df[col].count()
            if total_non_null > 0:
                column_uniqueness[col] = round((unique_vals / total_non_null) * 100, 2)
        
        overall_score = (unique_rows / total_rows) * 100 if total_rows > 0 else 100
        
        return {
            "score": round(overall_score, 2),
            "details": {
                "total_rows": total_rows,
                "unique_rows": unique_rows,
                "duplicate_rows": duplicate_count,
                "key_columns": key_columns or "all",
                "column_uniqueness": column_uniqueness
            }
        }
    
    def validity(self, expected_dtypes: Dict[str, str] = None) -> Dict:
        """
        Validity = (Valid format values / Total values) × 100
        Measures conformance to defined syntax/format
        """
        import re
        
        # Common format patterns
        FORMAT_PATTERNS = {
            "email": r'^[\w\.-]+@[\w\.-]+\.\w+$',
            "phone": r'^[\+]?[\d\s\-\(\)]{8,}$',
            "date_dmy": r'^\d{2}[/\-]\d{2}[/\-]\d{4}$',
            "date_ymd": r'^\d{4}[/\-]\d{2}[/\-]\d{2}$',
            "cin_ma": r'^[A-Z]{1,2}\d{5,8}$',
            "iban_ma": r'^MA\d{24}$',
            "url": r'^https?://[\w\.-]+\.\w+',
        }
        
        total_validated = 0
        total_valid = 0
        column_validity = {}
        
        for col in self.df.columns:
            col_lower = col.lower()
            
            # Auto-detect format based on column name
            pattern = None
            for pattern_name, regex in FORMAT_PATTERNS.items():
                if pattern_name.replace("_", "") in col_lower.replace("_", ""):
                    pattern = regex
                    break
            
            if pattern and self.df[col].dtype == 'object':
                non_null = self.df[col].dropna().astype(str)
                total_validated += len(non_null)
                valid = non_null.str.match(pattern, na=False).sum()
                total_valid += valid
                column_validity[col] = round((valid / len(non_null)) * 100, 2) if len(non_null) > 0 else 100
        
        # If no format validation was needed, check dtype validity
        if total_validated == 0:
            total_validated = self.df.size
            total_valid = self.df.notna().sum().sum()  # At least valid if not null
        
        overall_score = (total_valid / total_validated) * 100 if total_validated > 0 else 100
        
        return {
            "score": round(min(100, overall_score), 2),
            "details": {
                "formats_checked": list(column_validity.keys()),
                "column_validity": column_validity
            }
        }

# ====================================================================
# QUALITY SCORER
# ====================================================================

class QualityScorer:
    """Calculate global quality score with weighted dimensions"""
    
    DEFAULT_WEIGHTS = {
        "completeness": 0.20,
        "accuracy": 0.25,
        "consistency": 0.15,
        "timeliness": 0.10,
        "uniqueness": 0.15,
        "validity": 0.15
    }
    
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS
        # Normalize weights
        total = sum(self.weights.values())
        self.weights = {k: v/total for k, v in self.weights.items()}
    
    def calculate_global_score(self, dimension_scores: Dict[str, float]) -> float:
        """
        Global Score = Σ(weight_i × score_i)
        """
        global_score = 0.0
        for dim, score in dimension_scores.items():
            weight = self.weights.get(dim, 0)
            global_score += weight * score
        return round(global_score, 2)
    
    def get_grade(self, score: float) -> QualityGrade:
        """Convert score to letter grade"""
        if score >= 90:
            return QualityGrade.A
        elif score >= 75:
            return QualityGrade.B
        elif score >= 60:
            return QualityGrade.C
        elif score >= 40:
            return QualityGrade.D
        else:
            return QualityGrade.F
    
    def generate_recommendations(self, dimension_results: Dict[str, Dict]) -> List[str]:
        """Generate improvement recommendations based on scores"""
        recommendations = []
        
        for dim, result in dimension_results.items():
            score = result["score"]
            
            if dim == "completeness" and score < 90:
                recommendations.append(f"📊 Improve data completeness: Fill missing values or remove incomplete records (current: {score}%)")
            
            if dim == "accuracy" and score < 90:
                recommendations.append(f"✅ Validate data accuracy: Review and correct inaccurate values (current: {score}%)")
            
            if dim == "consistency" and score < 90:
                issues = result.get("details", {}).get("issues", [])
                if issues:
                    recommendations.append(f"🔄 Fix inconsistencies: {issues[0]} (current: {score}%)")
            
            if dim == "timeliness" and score < 80:
                recommendations.append(f"⏰ Update stale data: Many records exceed the freshness threshold (current: {score}%)")
            
            if dim == "uniqueness" and score < 95:
                dups = result.get("details", {}).get("duplicate_rows", 0)
                if dups > 0:
                    recommendations.append(f"🔁 Remove duplicates: {dups} duplicate records found (current: {score}%)")
            
            if dim == "validity" and score < 90:
                recommendations.append(f"📝 Fix format issues: Some values don't match expected formats (current: {score}%)")
        
        if not recommendations:
            recommendations.append("✨ Great job! All quality dimensions are above acceptable thresholds.")
        
        return recommendations[:5]  # Limit to top 5

# ====================================================================
# PDF REPORT GENERATOR
# ====================================================================

class PDFReportGenerator:
    """Generate PDF quality reports"""
    
    def generate(self, report: QualityReport, dataset_name: str = "Dataset") -> bytes:
        if not PDF_AVAILABLE:
            raise HTTPException(500, "PDF generation not available. Install fpdf2.")
        
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font("Arial", "B", 20)
        pdf.cell(0, 15, "Data Quality Report", ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, f"Dataset: {dataset_name}", ln=True, align="C")
        pdf.cell(0, 8, f"Generated: {report.evaluation_time}", ln=True, align="C")
        pdf.ln(10)
        
        # Global Score Box
        pdf.set_font("Arial", "B", 16)
        grade_colors = {
            QualityGrade.A: (0, 150, 0),
            QualityGrade.B: (100, 180, 0),
            QualityGrade.C: (200, 150, 0),
            QualityGrade.D: (200, 100, 0),
            QualityGrade.F: (200, 0, 0)
        }
        r, g, b = grade_colors.get(report.grade, (0, 0, 0))
        pdf.set_text_color(r, g, b)
        pdf.cell(0, 12, f"Global Score: {report.global_score}% (Grade {report.grade.value})", ln=True, align="C")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)
        
        # Dimensions Table
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Quality Dimensions (ISO 25012)", ln=True)
        pdf.set_font("Arial", "", 11)
        
        # Table header
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(60, 8, "Dimension", 1, 0, "C", True)
        pdf.cell(30, 8, "Score", 1, 0, "C", True)
        pdf.cell(30, 8, "Weight", 1, 0, "C", True)
        pdf.cell(40, 8, "Weighted", 1, 1, "C", True)
        
        for dim in report.dimensions:
            # Color based on score
            if dim.score >= 90:
                pdf.set_fill_color(200, 255, 200)
            elif dim.score >= 70:
                pdf.set_fill_color(255, 255, 200)
            else:
                pdf.set_fill_color(255, 200, 200)
            
            pdf.cell(60, 8, dim.dimension.capitalize(), 1, 0, "L", True)
            pdf.cell(30, 8, f"{dim.score}%", 1, 0, "C", True)
            pdf.cell(30, 8, f"{dim.weight*100:.0f}%", 1, 0, "C", True)
            pdf.cell(40, 8, f"{dim.weighted_score:.2f}", 1, 1, "C", True)
        
        pdf.ln(10)
        
        # Recommendations
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Recommendations", ln=True)
        pdf.set_font("Arial", "", 11)
        
        for rec in report.recommendations:
            pdf.multi_cell(0, 8, f"• {rec}")
        
        return pdf.output(dest='S').encode('latin-1')

# ====================================================================
# FASTAPI APP
# ====================================================================

app = FastAPI(
    title="Quality Service",
    description="Tâche 8 - ISO 25012 Data Quality Metrics",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "service": "Quality Service",
        "version": "2.0.0",
        "status": "running",
        "pdf_available": PDF_AVAILABLE,
        "dimensions": ["completeness", "accuracy", "consistency", "timeliness", "uniqueness", "validity"]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# ====================================================================
# QUALITY ENDPOINTS
# ====================================================================

@app.post("/evaluate/{dataset_id}", response_model=QualityReport)
def evaluate_quality(dataset_id: str, config: EvaluationConfig = None):
    """Evaluate dataset quality against ISO 25012 dimensions"""
    if dataset_id not in datasets_store:
        raise HTTPException(404, "Dataset not found")
    
    if config is None:
        config = EvaluationConfig()
    
    df = datasets_store[dataset_id]["df"]
    dims = QualityDimensions(df)
    scorer = QualityScorer(weights=config.weights)
    
    # Evaluate all dimensions
    dimension_results = {
        "completeness": dims.completeness(),
        "accuracy": dims.accuracy(
            validation_rules=config.validation_rules,
            regex_rules=config.regex_rules
        ),
        "consistency": dims.consistency(),
        "timeliness": dims.timeliness(
            date_columns=config.date_columns,
            max_age_days=config.max_age_days
        ),
        "uniqueness": dims.uniqueness(key_columns=config.key_columns),
        "validity": dims.validity()
    }
    
    # Calculate scores
    dimension_scores = {dim: result["score"] for dim, result in dimension_results.items()}
    global_score = scorer.calculate_global_score(dimension_scores)
    grade = scorer.get_grade(global_score)
    recommendations = scorer.generate_recommendations(dimension_results)
    
    # Build dimension list with details
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
    
    # Store report
    reports_store[dataset_id] = report
    
    return report

@app.get("/evaluate/{dataset_id}/dimension/{dimension}")
def evaluate_single_dimension(dataset_id: str, dimension: str):
    """Evaluate a single quality dimension"""
    if dataset_id not in datasets_store:
        raise HTTPException(404, "Dataset not found")
    
    valid_dimensions = ["completeness", "accuracy", "consistency", "timeliness", "uniqueness", "validity"]
    if dimension not in valid_dimensions:
        raise HTTPException(400, f"Invalid dimension. Choose from: {valid_dimensions}")
    
    df = datasets_store[dataset_id]["df"]
    dims = QualityDimensions(df)
    
    method = getattr(dims, dimension)
    result = method()
    
    return {
        "dataset_id": dataset_id,
        "dimension": dimension,
        **result
    }

@app.get("/report/{dataset_id}/pdf")
def get_pdf_report(dataset_id: str):
    """Download PDF quality report"""
    if dataset_id not in reports_store:
        raise HTTPException(404, "Report not found. Run /evaluate first.")
    
    report = reports_store[dataset_id]
    filename = datasets_store.get(dataset_id, {}).get("filename", "dataset")
    
    generator = PDFReportGenerator()
    pdf_bytes = generator.generate(report, dataset_name=filename)
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=quality_report_{dataset_id[:8]}.pdf"}
    )

@app.get("/dimensions")
def list_dimensions():
    """List available quality dimensions with descriptions"""
    return {
        "dimensions": {
            "completeness": "Degree to which data has values for all attributes",
            "accuracy": "Degree of correctness and precision",
            "consistency": "Degree of coherence and absence of contradictions",
            "timeliness": "Degree to which data is sufficiently up-to-date",
            "uniqueness": "Degree to which there is no duplicated data",
            "validity": "Degree to which data conforms to defined format/rules"
        },
        "default_weights": QualityScorer.DEFAULT_WEIGHTS
    }

# ====================================================================
# UTILITY ENDPOINTS
# ====================================================================

@app.post("/upload")
async def upload_for_quality(file: bytes = None):
    """Upload dataset for quality evaluation (alias for cleaning-serv)"""
    return {"message": "Please use cleaning-serv /upload endpoint first, then use the dataset_id here"}

@app.post("/datasets/{dataset_id}/register")
def register_dataset(dataset_id: str, data: Dict):
    """Register a dataset from another service"""
    import pandas as pd
    
    if "records" in data:
        df = pd.DataFrame(data["records"])
    elif "df" in data:
        df = pd.DataFrame(data["df"])
    else:
        raise HTTPException(400, "Provide 'records' or 'df' in request body")
    
    datasets_store[dataset_id] = {
        "df": df,
        "filename": data.get("filename", "registered_dataset"),
        "upload_time": datetime.now().isoformat(),
        "size_bytes": 0
    }
    
    return {"status": "registered", "dataset_id": dataset_id, "rows": len(df)}

# ====================================================================
# MAIN
# ====================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📊 QUALITY SERVICE - Tâche 8 (ISO 25012)")
    print("="*60)
    print(f"PDF Generation: {'✅ Available' if PDF_AVAILABLE else '❌ Not installed'}")
    print("="*60 + "\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8008, reload=True)
