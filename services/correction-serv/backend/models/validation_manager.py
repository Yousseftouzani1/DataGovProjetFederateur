"""
Validation Manager
===================
Data Quality V2 - User Stories US-CORR-04, US-CORR-05

Manages human validation workflow for corrections requiring review.
Coordinates between Data Annotators and the learning system.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class ValidationDecision(str, Enum):
    """Validation decision types"""
    ACCEPT = "accept"
    REJECT = "reject"
    MODIFY = "modify"


class ValidationRecord(BaseModel):
    """Record of human validation"""
    correction_id: str
    field: str
    original_value: Any
    suggested_value: Any
    decision: ValidationDecision
    final_value: Any
    validator_id: str
    validator_role: str  # "data_steward", "data_annotator"
    confidence_original: float
    timestamp: datetime
    comments: Optional[str] = None


class ValidationQueue:
    """
    Queue of corrections awaiting human review
    
    Organizes corrections by priority:
    - Confidence score (lower = higher priority)
    - Inconsistency type
    - Impact level
    """
    
    def __init__(self, db):
        self.db = db
        self.collection = db.correction_validations
    
    async def add_to_queue(
        self,
        correction: Dict[str, Any],
        priority: int = 5
    ) -> str:
        """
        Add correction to validation queue
        
        Args:
            correction: Correction details with suggested values
            priority: 1 (highest) to 10 (lowest), default 5
            
        Returns:
            Queue item ID
        """
        queue_item = {
            **correction,
            "status": "pending_review",
            "priority": priority,
            "added_to_queue_at": datetime.utcnow(),
            "assigned_to": None
        }
        
        result = await self.collection.insert_one(queue_item)
        return str(result.inserted_id)
    
    async def get_pending(
        self,
        validator_id: Optional[str] = None,
        limit: int = 50,
        min_confidence: float = 0.0,
        max_confidence: float = 0.9
    ) -> List[Dict[str, Any]]:
        """
        Get pending validations
        
        Args:
            validator_id: Filter by assigned validator
            limit: Max number to return
            min_confidence: Minimum confidence score
            max_confidence: Maximum confidence score
            
        Returns:
            List of pending corrections ordered by priority
        """
        query = {
            "status": "pending_review",
            "confidence": {"$gte": min_confidence, "$lte": max_confidence}
        }
        
        if validator_id:
            query["assigned_to"] = validator_id
        
        cursor = self.collection.find(query).sort([
            ("priority", 1),  # Higher priority first
            ("confidence", 1),  # Lower confidence first
            ("added_to_queue_at", 1)  # Older first
        ]).limit(limit)
        
        items = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for item in items:
            item["_id"] = str(item["_id"])
        
        return items
    
    async def assign_to_validator(
        self,
        correction_id: str,
        validator_id: str
    ) -> bool:
        """Assign correction to specific validator"""
        result = await self.collection.update_one(
            {"_id": correction_id, "status": "pending_review"},
            {"$set": {
                "assigned_to": validator_id,
                "assigned_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0


class ValidationManager:
    """
    Manages the complete validation workflow
    
    Responsibilities:
    - Record validation decisions
    - Update correction status
    - Trigger learning from validated corrections
    - Track validator performance
    """
    
    def __init__(self, db):
        self.db = db
        self.queue = ValidationQueue(db)
        self.validations_collection = db.correction_validations
        self.training_collection = db.correction_training_data
    
    async def validate_correction(
        self,
        correction_id: str,
        decision: ValidationDecision,
        final_value: Any,
        validator_id: str,
        validator_role: str,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record human validation of a correction
        
        Args:
            correction_id: ID of the correction being validated
            decision: ACCEPT, REJECT, or MODIFY
            final_value: The final value to use (may differ from suggested)
            validator_id: ID of the validator
            validator_role: Role (data_steward or data_annotator)
            comments: Optional validation comments
            
        Returns:
            Validation result with learning status
        """
        # Get the original correction
        correction = await self.validations_collection.find_one(
            {"_id": correction_id}
        )
        
        if not correction:
            raise ValueError(f"Correction {correction_id} not found")
        
        # Create validation record
        validation = ValidationRecord(
            correction_id=correction_id,
            field=correction["field"],
            original_value=correction["old_value"],
            suggested_value=correction.get("candidates", [{}])[0].get("value") 
                if "candidates" in correction else correction.get("suggested_value"),
            decision=decision,
            final_value=final_value,
            validator_id=validator_id,
            validator_role=validator_role,
            confidence_original=correction.get("confidence", 0.0),
            timestamp=datetime.utcnow(),
            comments=comments
        )
        
        # Update correction status in database
        new_status = "validated_accepted" if decision == ValidationDecision.ACCEPT else \
                     "validated_rejected" if decision == ValidationDecision.REJECT else \
                     "validated_modified"
        
        await self.validations_collection.update_one(
            {"_id": correction_id},
            {"$set": {
                "status": new_status,
                "validation": validation.dict(),
                "validated_at": datetime.utcnow(),
                "validated_by": validator_id,
                "final_value": final_value
            }}
        )
        
        # Create training example for learning
        learning_recorded = await self._create_training_example(
            correction, 
            validation
        )
        
        return {
            "validation_id": correction_id,
            "decision": decision.value,
            "final_value": final_value,
            "learning_recorded": learning_recorded,
            "timestamp": validation.timestamp.isoformat()
        }
    
    async def batch_validate(
        self,
        validations: List[Dict[str, Any]],
        validator_id: str,
        validator_role: str
    ) -> Dict[str, Any]:
        """
        Validate multiple corrections in batch
        
        Args:
            validations: List of {correction_id, decision, final_value, comments}
            validator_id: ID of validator
            validator_role: Role of validator
            
        Returns:
            Summary of batch validation
        """
        results = {
            "accepted": 0,
            "rejected": 0,
            "modified": 0,
            "errors": []
        }
        
        for val in validations:
            try:
                await self.validate_correction(
                    correction_id=val["correction_id"],
                    decision=ValidationDecision(val["decision"]),
                    final_value=val["final_value"],
                    validator_id=validator_id,
                    validator_role=validator_role,
                    comments=val.get("comments")
                )
                
                if val["decision"] == "accept":
                    results["accepted"] += 1
                elif val["decision"] == "reject":
                    results["rejected"] += 1
                else:
                    results["modified"] += 1
                    
            except Exception as e:
                results["errors"].append({
                    "correction_id": val["correction_id"],
                    "error": str(e)
                })
        
        return results
    
    async def _create_training_example(
        self,
        correction: Dict[str, Any],
        validation: ValidationRecord
    ) -> bool:
        """
        Create training example from validated correction
        
        Format for T5 fine-tuning:
        Input: "correct: <incorrect_value> context: <field_name>"
        Output: <validated_correct_value>
        """
        try:
            training_example = {
                "input_text": f"correct: {correction['old_value']} context: {correction['field']}",
                "output_text": str(validation.final_value),
                "field": correction["field"],
                "inconsistency_type": correction.get("type", "UNKNOWN"),
                "ml_suggested": correction.get("ml_suggestion"),
                "rule_suggested": correction.get("rule_suggestion"),
                "human_decision": validation.decision.value,
                "validator_id": validation.validator_id,
                "validator_role": validation.validator_role,
                "original_confidence": validation.confidence_original,
                "timestamp": datetime.utcnow(),
                "metadata": {
                    "correction_id": validation.correction_id,
                    "comments": validation.comments
                }
            }
            
            await self.training_collection.insert_one(training_example)
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to create training example: {e}")
            return False
    
    async def get_validation_stats(
        self,
        validator_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get validation statistics
        
        Args:
            validator_id: Filter by specific validator
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            Validation statistics
        """
        query = {"status": {"$in": [
            "validated_accepted",
            "validated_rejected",
            "validated_modified"
        ]}}
        
        if validator_id:
            query["validated_by"] = validator_id
        
        if start_date or end_date:
            query["validated_at"] = {}
            if start_date:
                query["validated_at"]["$gte"] = start_date
            if end_date:
                query["validated_at"]["$lte"] = end_date
        
        # Aggregate statistics
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$validation.decision",
                "count": {"$sum": 1},
                "avg_confidence": {"$avg": "$validation.confidence_original"}
            }}
        ]
        
        cursor = self.validations_collection.aggregate(pipeline)
        results = await cursor.to_list(length=100)
        
        stats = {
            "total": 0,
            "accepted": 0,
            "rejected": 0,
            "modified": 0,
            "avg_confidence": {}
        }
        
        for result in results:
            decision = result["_id"]
            count = result["count"]
            stats["total"] += count
            
            if decision == "accept":
                stats["accepted"] = count
                stats["avg_confidence"]["accepted"] = result["avg_confidence"]
            elif decision == "reject":
                stats["rejected"] = count
                stats["avg_confidence"]["rejected"] = result["avg_confidence"]
            elif decision == "modify":
                stats["modified"] = count
                stats["avg_confidence"]["modified"] = result["avg_confidence"]
        
        # Calculate acceptance rate
        if stats["total"] > 0:
            stats["acceptance_rate"] = (stats["accepted"] + stats["modified"]) / stats["total"]
        else:
            stats["acceptance_rate"] = 0.0
        
        return stats
    
    async def get_validator_leaderboard(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top validators by activity and quality
        
        Returns:
            List of validators with stats
        """
        pipeline = [
            {"$match": {
                "status": {"$in": ["validated_accepted", "validated_rejected", "validated_modified"]}
            }},
            {"$group": {
                "_id": "$validated_by",
                "total_validations": {"$sum": 1},
                "accepted": {
                    "$sum": {"$cond": [{"$eq": ["$validation.decision", "accept"]}, 1, 0]}
                },
                "avg_response_time": {"$avg": {
                    "$subtract": ["$validated_at", "$added_to_queue_at"]
                }}
            }},
            {"$sort": {"total_validations": -1}},
            {"$limit": limit}
        ]
        
        cursor = self.validations_collection.aggregate(pipeline)
        leaderboard = await cursor.to_list(length=limit)
        
        return leaderboard
