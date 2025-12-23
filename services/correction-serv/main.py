"""
Correction Service - Tâche 6
Automatic Data Inconsistency Detection and Correction

Features:
- Inconsistency detection (format, range, type mismatches)
- YAML-based correction rules
- Auto-correction engine
- Validation queue for human review
- Correction history tracking
"""
import re
import yaml
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
from pathlib import Path

import uvicorn
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ====================================================================
# MODELS
# ====================================================================

class InconsistencyType(str, Enum):
    FORMAT = "format"           # Value doesn't match expected format
    RANGE = "range"             # Value out of valid range
    TYPE = "type"               # Wrong data type
    MISSING = "missing"         # Required value missing
    LOGICAL = "logical"         # Logical contradiction
    DUPLICATE = "duplicate"     # Duplicate value where unique expected

class CorrectionStatus(str, Enum):
    SUGGESTED = "suggested"     # Auto-suggested, not yet applied
    APPLIED = "applied"         # Correction applied
    REJECTED = "rejected"       # Human rejected correction
    PENDING_REVIEW = "pending"  # Needs human validation

class Inconsistency(BaseModel):
    id: str
    column: str
    row_index: int
    original_value: Any
    inconsistency_type: InconsistencyType
    description: str
    suggested_correction: Optional[Any] = None
    confidence: float = Field(ge=0, le=1)
    status: CorrectionStatus = CorrectionStatus.SUGGESTED

class CorrectionRule(BaseModel):
    name: str
    column: Optional[str] = None
    column_pattern: Optional[str] = None  # Regex to match column names
    rule_type: str  # format, range, transform, default
    condition: Optional[Dict] = None
    action: Dict
    priority: int = 0

class DetectionRequest(BaseModel):
    columns: Optional[List[str]] = None
    check_format: bool = True
    check_range: bool = True
    check_type: bool = True
    check_missing: bool = True

class CorrectionRequest(BaseModel):
    inconsistency_ids: Optional[List[str]] = None  # None = apply all
    auto_apply: bool = False  # If True, apply without confirmation

class DetectionResult(BaseModel):
    dataset_id: str
    total_inconsistencies: int
    by_type: Dict[str, int]
    by_column: Dict[str, int]
    inconsistencies: List[Inconsistency]

class CorrectionResult(BaseModel):
    success: bool
    corrections_applied: int
    corrections_rejected: int
    pending_review: int

# ====================================================================
# IN-MEMORY STORAGE
# ====================================================================

datasets_store: Dict[str, Dict] = {}
inconsistencies_store: Dict[str, List[Inconsistency]] = {}  # dataset_id -> list
correction_rules: List[CorrectionRule] = []
correction_history: List[Dict] = []

# ====================================================================
# DEFAULT CORRECTION RULES
# ====================================================================

DEFAULT_RULES = """
rules:
  # Phone number standardization
  - name: standardize_phone_ma
    column_pattern: "phone|tel|telephone|mobile"
    rule_type: format
    condition:
      pattern: "^\\d{10}$"
    action:
      transform: "prefix_212"
      target_format: "+212{value[1:]}"
  
  # Email lowercase
  - name: lowercase_email
    column_pattern: "email|mail|courriel"
    rule_type: transform
    action:
      operation: lowercase
  
  # Date standardization
  - name: standardize_date
    column_pattern: "date|birth|naissance|created|updated"
    rule_type: format
    action:
      target_format: "%Y-%m-%d"
  
  # Name title case
  - name: titlecase_name
    column_pattern: "name|nom|prenom|firstname|lastname"
    rule_type: transform
    action:
      operation: titlecase
  
  # CIN uppercase
  - name: uppercase_cin
    column_pattern: "cin|id_card|carte_identite"
    rule_type: transform
    action:
      operation: uppercase
  
  # Age range validation
  - name: validate_age
    column_pattern: "age"
    rule_type: range
    condition:
      min: 0
      max: 150
    action:
      on_violation: flag
  
  # Percentage range
  - name: validate_percentage
    column_pattern: "percent|pourcent|rate|taux"
    rule_type: range
    condition:
      min: 0
      max: 100
    action:
      on_violation: flag
"""

# ====================================================================
# INCONSISTENCY DETECTOR
# ====================================================================

class InconsistencyDetector:
    """Detect data inconsistencies using rules and patterns"""
    
    # Common format patterns
    FORMAT_PATTERNS = {
        "email": r'^[\w\.-]+@[\w\.-]+\.\w+$',
        "phone_ma": r'^(\+212|0)[5-7]\d{8}$',
        "phone_international": r'^\+\d{10,15}$',
        "date_dmy": r'^\d{2}[/\-]\d{2}[/\-]\d{4}$',
        "date_ymd": r'^\d{4}[/\-]\d{2}[/\-]\d{2}$',
        "cin_ma": r'^[A-Z]{1,2}\d{5,8}$',
        "iban_ma": r'^MA\d{24}$',
        "url": r'^https?://[\w\.-]+',
        "cnss": r'^\d{9,12}$',
    }
    
    def __init__(self, df: pd.DataFrame, rules: List[CorrectionRule] = None):
        self.df = df
        self.rules = rules or []
        self.inconsistencies: List[Inconsistency] = []
    
    def detect_format_issues(self, column: str) -> List[Inconsistency]:
        """Detect format inconsistencies based on column name patterns"""
        issues = []
        col_lower = column.lower()
        
        # Find applicable pattern
        pattern = None
        pattern_name = None
        for name, regex in self.FORMAT_PATTERNS.items():
            if name.replace("_", "") in col_lower.replace("_", ""):
                pattern = regex
                pattern_name = name
                break
        
        if not pattern or self.df[column].dtype not in ['object', 'string']:
            return issues
        
        for idx, value in self.df[column].items():
            if pd.isna(value):
                continue
            
            str_value = str(value)
            if not re.match(pattern, str_value):
                issues.append(Inconsistency(
                    id=str(uuid.uuid4()),
                    column=column,
                    row_index=int(idx),
                    original_value=value,
                    inconsistency_type=InconsistencyType.FORMAT,
                    description=f"Value '{str_value}' doesn't match {pattern_name} format",
                    suggested_correction=self._suggest_format_fix(str_value, pattern_name),
                    confidence=0.7
                ))
        
        return issues
    
    def _suggest_format_fix(self, value: str, pattern_name: str) -> Optional[str]:
        """Suggest format correction"""
        if pattern_name == "phone_ma":
            digits = re.sub(r'\D', '', value)
            if len(digits) == 9:
                return f"+212{digits}"
            elif len(digits) == 10 and digits.startswith("0"):
                return f"+212{digits[1:]}"
            elif len(digits) == 12 and digits.startswith("212"):
                return f"+{digits}"
        
        elif pattern_name == "email":
            # Suggest lowercase
            return value.lower().strip()
        
        elif pattern_name == "cin_ma":
            # Suggest uppercase
            return value.upper().strip()
        
        return None
    
    def detect_range_issues(self, column: str) -> List[Inconsistency]:
        """Detect out-of-range values"""
        issues = []
        
        if not pd.api.types.is_numeric_dtype(self.df[column]):
            return issues
        
        col_lower = column.lower()
        
        # Define expected ranges based on column name
        ranges = {
            "age": (0, 150),
            "percent": (0, 100),
            "pourcent": (0, 100),
            "rate": (0, 100),
            "score": (0, 100),
            "temperature": (-50, 60),
            "year": (1900, 2100),
            "month": (1, 12),
            "day": (1, 31),
        }
        
        min_val, max_val = None, None
        for pattern, (low, high) in ranges.items():
            if pattern in col_lower:
                min_val, max_val = low, high
                break
        
        if min_val is None:
            # Use statistical range (mean ± 3*std)
            mean = self.df[column].mean()
            std = self.df[column].std()
            if std > 0:
                min_val = mean - 4 * std
                max_val = mean + 4 * std
            else:
                return issues
        
        for idx, value in self.df[column].items():
            if pd.isna(value):
                continue
            
            if value < min_val or value > max_val:
                issues.append(Inconsistency(
                    id=str(uuid.uuid4()),
                    column=column,
                    row_index=int(idx),
                    original_value=value,
                    inconsistency_type=InconsistencyType.RANGE,
                    description=f"Value {value} outside expected range [{min_val}, {max_val}]",
                    suggested_correction=None,  # Can't auto-fix range issues
                    confidence=0.8
                ))
        
        return issues
    
    def detect_type_issues(self, column: str) -> List[Inconsistency]:
        """Detect type mismatches"""
        issues = []
        col_lower = column.lower()
        
        # Expected types based on column name
        expected_numeric = ["age", "price", "amount", "quantity", "count", "total", "salary", "score"]
        expected_date = ["date", "time", "created", "updated", "birth", "naissance"]
        
        for pattern in expected_numeric:
            if pattern in col_lower:
                # Should be numeric
                if not pd.api.types.is_numeric_dtype(self.df[column]):
                    # Try to find non-numeric values
                    for idx, value in self.df[column].items():
                        if pd.isna(value):
                            continue
                        try:
                            float(value)
                        except (ValueError, TypeError):
                            issues.append(Inconsistency(
                                id=str(uuid.uuid4()),
                                column=column,
                                row_index=int(idx),
                                original_value=value,
                                inconsistency_type=InconsistencyType.TYPE,
                                description=f"Expected numeric value, got: {type(value).__name__}",
                                suggested_correction=self._try_numeric_conversion(value),
                                confidence=0.6
                            ))
                break
        
        return issues
    
    def _try_numeric_conversion(self, value: Any) -> Optional[float]:
        """Try to extract numeric value"""
        if value is None:
            return None
        
        str_val = str(value)
        # Remove common non-numeric characters
        cleaned = re.sub(r'[^\d\.\-]', '', str_val)
        
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    def detect_missing_required(self, required_columns: List[str] = None) -> List[Inconsistency]:
        """Detect missing values in required columns"""
        issues = []
        
        # If not specified, consider ID-like columns as required
        if required_columns is None:
            required_columns = []
            for col in self.df.columns:
                col_lower = col.lower()
                if any(kw in col_lower for kw in ["id", "key", "code", "cin", "email"]):
                    required_columns.append(col)
        
        for col in required_columns:
            if col not in self.df.columns:
                continue
            
            missing_mask = self.df[col].isna()
            for idx in self.df[missing_mask].index:
                issues.append(Inconsistency(
                    id=str(uuid.uuid4()),
                    column=col,
                    row_index=int(idx),
                    original_value=None,
                    inconsistency_type=InconsistencyType.MISSING,
                    description=f"Required value missing in column '{col}'",
                    confidence=1.0
                ))
        
        return issues
    
    def detect_all(self, request: DetectionRequest = None) -> List[Inconsistency]:
        """Run all detection methods"""
        if request is None:
            request = DetectionRequest()
        
        columns = request.columns or self.df.columns.tolist()
        all_issues = []
        
        for col in columns:
            if col not in self.df.columns:
                continue
            
            if request.check_format:
                all_issues.extend(self.detect_format_issues(col))
            
            if request.check_range:
                all_issues.extend(self.detect_range_issues(col))
            
            if request.check_type:
                all_issues.extend(self.detect_type_issues(col))
        
        if request.check_missing:
            all_issues.extend(self.detect_missing_required())
        
        self.inconsistencies = all_issues
        return all_issues

# ====================================================================
# AUTO CORRECTOR
# ====================================================================

class AutoCorrector:
    """Apply corrections to data"""
    
    def __init__(self, df: pd.DataFrame, rules: List[CorrectionRule] = None):
        self.df = df.copy()
        self.rules = rules or []
        self.corrections_made = []
    
    def apply_correction(self, inconsistency: Inconsistency) -> bool:
        """Apply a single correction"""
        if inconsistency.suggested_correction is None:
            return False
        
        try:
            col = inconsistency.column
            idx = inconsistency.row_index
            
            old_value = self.df.at[idx, col]
            new_value = inconsistency.suggested_correction
            
            self.df.at[idx, col] = new_value
            
            self.corrections_made.append({
                "inconsistency_id": inconsistency.id,
                "column": col,
                "row_index": idx,
                "old_value": old_value,
                "new_value": new_value,
                "timestamp": datetime.now().isoformat()
            })
            
            inconsistency.status = CorrectionStatus.APPLIED
            return True
        
        except Exception as e:
            inconsistency.status = CorrectionStatus.REJECTED
            return False
    
    def apply_rule_corrections(self, column: str) -> int:
        """Apply rule-based corrections to a column"""
        corrections_count = 0
        
        for rule in self.rules:
            # Check if rule applies to this column
            if rule.column and rule.column != column:
                continue
            if rule.column_pattern:
                if not re.search(rule.column_pattern, column, re.IGNORECASE):
                    continue
            
            # Apply transformation
            action = rule.action
            
            if action.get("operation") == "lowercase":
                if self.df[column].dtype == 'object':
                    old_values = self.df[column].copy()
                    self.df[column] = self.df[column].str.lower()
                    corrections_count += (old_values != self.df[column]).sum()
            
            elif action.get("operation") == "uppercase":
                if self.df[column].dtype == 'object':
                    old_values = self.df[column].copy()
                    self.df[column] = self.df[column].str.upper()
                    corrections_count += (old_values != self.df[column]).sum()
            
            elif action.get("operation") == "titlecase":
                if self.df[column].dtype == 'object':
                    old_values = self.df[column].copy()
                    self.df[column] = self.df[column].str.title()
                    corrections_count += (old_values != self.df[column]).sum()
            
            elif action.get("operation") == "strip":
                if self.df[column].dtype == 'object':
                    old_values = self.df[column].copy()
                    self.df[column] = self.df[column].str.strip()
                    corrections_count += (old_values != self.df[column]).sum()
        
        return corrections_count
    
    def apply_all_suggestions(self, inconsistencies: List[Inconsistency]) -> Tuple[int, int]:
        """Apply all suggested corrections"""
        applied = 0
        rejected = 0
        
        for inc in inconsistencies:
            if inc.suggested_correction is not None and inc.confidence >= 0.7:
                if self.apply_correction(inc):
                    applied += 1
                else:
                    rejected += 1
            else:
                inc.status = CorrectionStatus.PENDING_REVIEW
        
        return applied, rejected
    
    def get_corrected_df(self) -> pd.DataFrame:
        return self.df

# ====================================================================
# FASTAPI APP
# ====================================================================

app = FastAPI(
    title="Correction Service",
    description="Tâche 6 - Automatic Data Inconsistency Detection and Correction",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load default rules on startup
@app.on_event("startup")
async def load_default_rules():
    global correction_rules
    try:
        rules_data = yaml.safe_load(DEFAULT_RULES)
        for rule_dict in rules_data.get("rules", []):
            correction_rules.append(CorrectionRule(**rule_dict))
        print(f"✅ Loaded {len(correction_rules)} correction rules")
    except Exception as e:
        print(f"⚠️ Failed to load rules: {e}")

@app.get("/")
def root():
    return {
        "service": "Correction Service",
        "version": "2.0.0",
        "status": "running",
        "rules_loaded": len(correction_rules)
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# ====================================================================
# DETECTION ENDPOINTS
# ====================================================================

@app.post("/detect/{dataset_id}", response_model=DetectionResult)
def detect_inconsistencies(dataset_id: str, request: DetectionRequest = None):
    """Detect inconsistencies in dataset"""
    if dataset_id not in datasets_store:
        raise HTTPException(404, "Dataset not found")
    
    df = datasets_store[dataset_id]["df"]
    detector = InconsistencyDetector(df, correction_rules)
    
    inconsistencies = detector.detect_all(request)
    
    # Store for later correction
    inconsistencies_store[dataset_id] = inconsistencies
    
    # Build summary
    by_type = {}
    by_column = {}
    for inc in inconsistencies:
        by_type[inc.inconsistency_type.value] = by_type.get(inc.inconsistency_type.value, 0) + 1
        by_column[inc.column] = by_column.get(inc.column, 0) + 1
    
    return DetectionResult(
        dataset_id=dataset_id,
        total_inconsistencies=len(inconsistencies),
        by_type=by_type,
        by_column=by_column,
        inconsistencies=inconsistencies[:100]  # Limit response
    )

@app.get("/inconsistencies/{dataset_id}")
def get_inconsistencies(dataset_id: str, status: Optional[str] = None, limit: int = 100):
    """Get stored inconsistencies for dataset"""
    if dataset_id not in inconsistencies_store:
        return {"inconsistencies": [], "total": 0}
    
    incs = inconsistencies_store[dataset_id]
    
    if status:
        incs = [i for i in incs if i.status.value == status]
    
    return {
        "inconsistencies": incs[:limit],
        "total": len(incs)
    }

# ====================================================================
# CORRECTION ENDPOINTS
# ====================================================================

@app.post("/correct/{dataset_id}", response_model=CorrectionResult)
def apply_corrections(dataset_id: str, request: CorrectionRequest = None):
    """Apply corrections to dataset"""
    if dataset_id not in datasets_store:
        raise HTTPException(404, "Dataset not found")
    
    if request is None:
        request = CorrectionRequest()
    
    df = datasets_store[dataset_id]["df"]
    inconsistencies = inconsistencies_store.get(dataset_id, [])
    
    if not inconsistencies:
        return CorrectionResult(
            success=True,
            corrections_applied=0,
            corrections_rejected=0,
            pending_review=0
        )
    
    # Filter by IDs if specified
    if request.inconsistency_ids:
        to_correct = [i for i in inconsistencies if i.id in request.inconsistency_ids]
    else:
        to_correct = inconsistencies
    
    corrector = AutoCorrector(df, correction_rules)
    
    if request.auto_apply:
        applied, rejected = corrector.apply_all_suggestions(to_correct)
    else:
        # Only apply high-confidence corrections
        high_conf = [i for i in to_correct if i.confidence >= 0.8]
        applied, rejected = corrector.apply_all_suggestions(high_conf)
    
    # Update dataset
    datasets_store[dataset_id]["df"] = corrector.get_corrected_df()
    
    # Add to history
    correction_history.extend(corrector.corrections_made)
    
    pending = sum(1 for i in to_correct if i.status == CorrectionStatus.PENDING_REVIEW)
    
    return CorrectionResult(
        success=True,
        corrections_applied=applied,
        corrections_rejected=rejected,
        pending_review=pending
    )

@app.post("/correct/{dataset_id}/auto")
def auto_correct_all(dataset_id: str):
    """Auto-apply all high-confidence corrections"""
    return apply_corrections(dataset_id, CorrectionRequest(auto_apply=True))

@app.post("/validate/{dataset_id}/{inconsistency_id}")
def validate_correction(dataset_id: str, inconsistency_id: str, approve: bool):
    """Manually validate or reject a correction"""
    if dataset_id not in inconsistencies_store:
        raise HTTPException(404, "No inconsistencies found for dataset")
    
    for inc in inconsistencies_store[dataset_id]:
        if inc.id == inconsistency_id:
            if approve and inc.suggested_correction:
                # Apply the correction
                df = datasets_store[dataset_id]["df"]
                corrector = AutoCorrector(df)
                corrector.apply_correction(inc)
                datasets_store[dataset_id]["df"] = corrector.get_corrected_df()
                return {"status": "approved", "correction_applied": True}
            else:
                inc.status = CorrectionStatus.REJECTED
                return {"status": "rejected"}
    
    raise HTTPException(404, "Inconsistency not found")

# ====================================================================
# RULES ENDPOINTS
# ====================================================================

@app.get("/rules")
def list_rules():
    """List all correction rules"""
    return {"rules": [r.dict() for r in correction_rules]}

@app.post("/rules")
def add_rule(rule: CorrectionRule):
    """Add a new correction rule"""
    correction_rules.append(rule)
    return {"status": "added", "total_rules": len(correction_rules)}

@app.get("/history")
def get_correction_history(limit: int = 100):
    """Get correction history"""
    return {"history": correction_history[-limit:], "total": len(correction_history)}

# ====================================================================
# DATASET MANAGEMENT
# ====================================================================

@app.post("/datasets/{dataset_id}/register")
def register_dataset(dataset_id: str, data: Dict):
    """Register a dataset from another service"""
    if "records" in data:
        df = pd.DataFrame(data["records"])
    else:
        raise HTTPException(400, "Provide 'records' in request body")
    
    datasets_store[dataset_id] = {
        "df": df,
        "filename": data.get("filename", "registered"),
        "upload_time": datetime.now().isoformat()
    }
    
    return {"status": "registered", "dataset_id": dataset_id}

# ====================================================================
# MAIN
# ====================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔧 CORRECTION SERVICE - Tâche 6")
    print("="*60)
    uvicorn.run("main:app", host="0.0.0.0", port=8006, reload=True)
