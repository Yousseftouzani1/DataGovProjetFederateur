from typing import List, Dict, Optional
from enum import Enum
from pydantic import BaseModel, Field

class SensitivityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"

class AnalyzeRequest(BaseModel):
    text: str = Field(..., description="Texte à analyser", min_length=1)
    language: str = Field(default="fr", description="Langue (fr/en/ar)")
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    detect_names: bool = Field(default=True)
    domains: Optional[List[str]] = Field(default=None)

class DetectionResult(BaseModel):
    entity_type: str
    category: str
    domain: Optional[str] = None
    value: str
    start: int
    end: int
    sensitivity_level: str
    sensitivity_score: Optional[float] = None  # NEW: Cahier formula score
    sensitivity_breakdown: Optional[Dict] = None  # NEW: {legal, risk, impact}
    confidence_score: float
    detection_method: str = "regex"
    context: Optional[str] = None
    analysis_explanation: Optional[str] = None # Added for explanation feature

class AnalyzeResponse(BaseModel):
    success: bool
    text_length: int
    detections_count: int
    detections: List[DetectionResult]
    summary: Dict[str, int]
    domains_summary: Dict[str, int]
    execution_time_ms: float
