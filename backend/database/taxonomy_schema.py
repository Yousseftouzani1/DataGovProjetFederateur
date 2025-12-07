"""
Taxonomy Schema for MongoDB
Defines the structure and indexes for taxonomy collections
"""
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

# ============================================================
# PYDANTIC MODELS FOR VALIDATION
# ============================================================

class SubclassSchema(BaseModel):
    """Schema for a taxonomy subclass/entity"""
    name: str
    name_en: Optional[str] = None
    synonyms_fr: List[str] = []
    synonyms_en: List[str] = []
    acronyms_fr: List[str] = []
    acronyms_en: List[str] = []
    regex_patterns: List[str] = []
    format: Optional[str] = None
    sensitivity_level: str = "unknown"  # critical, high, medium, low, unknown
    risk_level: Optional[str] = None
    regulations: List[str] = []
    why_sensitive: Optional[str] = None
    context_required: List[str] = []
    data_format: Optional[str] = None

class CategorySchema(BaseModel):
    """Schema for a taxonomy category"""
    class_name: str = Field(..., alias="class")
    class_en: Optional[str] = None
    type: str  # PII or SPI
    subclasses: List[SubclassSchema]

class DomainMetadata(BaseModel):
    """Schema for domain metadata"""
    domain_id: str
    domain_name: str
    domain_name_en: Optional[str] = None
    version: str = "1.0"
    context: str = "Maroc"
    last_updated: str
    description: str
    total_entities: int

class TaxonomyDocument(BaseModel):
    """Complete taxonomy document for MongoDB"""
    metadata: DomainMetadata
    categories: List[CategorySchema]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ============================================================
# MONGODB INDEXES
# ============================================================

TAXONOMY_INDEXES = [
    {"key": "metadata.domain_id", "unique": True},
    {"key": "metadata.domain_name", "unique": True},
    {"key": "categories.class"},
    {"key": "categories.subclasses.name"},
    {"key": "categories.subclasses.sensitivity_level"},
    {"key": "created_at"}
]

ENTITY_INDEXES = [
    {"key": "entity_id", "unique": True},
    {"key": "domain_id"},
    {"key": "category"},
    {"key": "sensitivity_level"},
    {"key": "name_text", "type": "text"}
]

DOMAIN_INDEXES = [
    {"key": "domain_id", "unique": True},
    {"key": "domain_name", "unique": True}
]

# ============================================================
# COLLECTION SCHEMAS (MongoDB Validation)
# ============================================================

TAXONOMY_COLLECTION_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["metadata", "categories"],
        "properties": {
            "metadata": {
                "bsonType": "object",
                "required": ["domain_id", "domain_name"],
                "properties": {
                    "domain_id": {"bsonType": "string"},
                    "domain_name": {"bsonType": "string"},
                    "version": {"bsonType": "string"},
                    "context": {"bsonType": "string"},
                    "description": {"bsonType": "string"}
                }
            },
            "categories": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": ["class", "type", "subclasses"],
                    "properties": {
                        "class": {"bsonType": "string"},
                        "type": {"enum": ["PII", "SPI"]},
                        "subclasses": {"bsonType": "array"}
                    }
                }
            }
        }
    }
}

ENTITY_COLLECTION_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["entity_id", "name", "domain_id", "category", "sensitivity_level"],
        "properties": {
            "entity_id": {"bsonType": "string"},
            "name": {"bsonType": "string"},
            "name_en": {"bsonType": "string"},
            "domain_id": {"bsonType": "string"},
            "domain_name": {"bsonType": "string"},
            "category": {"bsonType": "string"},
            "type": {"enum": ["PII", "SPI"]},
            "sensitivity_level": {"enum": ["critical", "high", "medium", "low", "unknown"]},
            "synonyms": {"bsonType": "array"},
            "acronyms": {"bsonType": "array"},
            "regex_patterns": {"bsonType": "array"},
            "regulations": {"bsonType": "array"}
        }
    }
}
