"""
Learning Engine
================
Data Quality V2 - User Story US-CORR-05

Continuous learning from human validation feedback to improve
correction accuracy over time.

Key features:
- Collects validated corrections as training examples
- Triggers periodic T5 model retraining
- Tracks accuracy improvement month-over-month
- Manages model versioning
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import asyncio


class LearningEngine:
    """
    Continuous learning and model improvement system
    
    Implements US-CORR-05: "Je veux apprendre des validations 
    pour améliorer les futures corrections"
    """
    
    # Retraining thresholds
    MIN_TRAINING_EXAMPLES = 50
    RETRAIN_EVERY_N_VALIDATIONS = 100
    
    # Model versioning
    MODEL_SAVE_PATH = "./models/t5_corrector_finetuned"
    
    def __init__(self, db, t5_corrector=None):
        self.db = db
        self.training_collection = db.correction_training_data
        self.model_versions_collection = db.correction_model_versions
        self.t5_corrector = t5_corrector
    
    async def record_validation(
        self,
        correction_id: str,
        validation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Record a validation for learning
        
        This is called automatically after ValidationManager.validate_correction()
        
        Args:
            correction_id: ID of correction
            validation_data: Validation details
            
        Returns:
            Learning status and retraining trigger info
        """
        # Training example already created by ValidationManager
        # Just check if retraining should be triggered
        
        total_examples = await self.training_collection.count_documents({})
        
        should_retrain = (
            total_examples >= self.MIN_TRAINING_EXAMPLES and
            total_examples % self.RETRAIN_EVERY_N_VALIDATIONS == 0
        )
        
        result = {
            "learning_enabled": True,
            "total_training_examples": total_examples,
            "should_retrain": should_retrain,
            "min_examples_reached": total_examples >= self.MIN_TRAINING_EXAMPLES
        }
        
        if should_retrain:
            print(f"📚 Retraining threshold reached: {total_examples} examples")
            print(f"💡 Trigger model retraining via: POST /learning/retrain")
        
        return result
    
    async def get_learning_stats(self) -> Dict[str, Any]:
        """
        Get statistics on learning progress
        
        Returns:
            Comprehensive learning statistics
        """
        total_examples = await self.training_collection.count_documents({})
        
        # Get examples by inconsistency type
        pipeline = [
            {"$group": {
                "_id": "$inconsistency_type",
                "count": {"$sum": 1}
            }}
        ]
        cursor =self.training_collection.aggregate(pipeline)
        by_type = {doc["_id"]: doc["count"] async for doc in cursor}
        
        # Get recent accuracy (last 100 validations)
        recent_examples = await self.training_collection.find().sort(
            "timestamp", -1
        ).limit(100).to_list(length=100)
        
        if recent_examples:
            # Calculate how often ML suggestion matched human decision
            ml_correct = sum(
                1 for ex in recent_examples 
                if ex.get("ml_suggested") == ex.get("output_text")
            )
            recent_accuracy = ml_correct / len(recent_examples)
        else:
            recent_accuracy = 0.0
        
        # Get model version info
        latest_model = await self.model_versions_collection.find_one(
            {},
            sort=[("trained_at", -1)]
        )
        
        # Check if retraining is needed
        needs_retraining = (
            total_examples >= self.MIN_TRAINING_EXAMPLES and
            total_examples % self.RETRAIN_EVERY_N_VALIDATIONS == 0
        )
        
        return {
            "total_training_examples": total_examples,
            "by_inconsistency_type": by_type,
            "recent_accuracy": round( recent_accuracy, 3),
            "latest_model_version": latest_model.get("version") if latest_model else "base",
            "latest_model_trained_at": latest_model.get("trained_at") if latest_model else None,
            "needs_retraining": needs_retraining,
            "next_retrain_at": self.RETRAIN_EVERY_N_VALIDATIONS - (
                total_examples % self.RETRAIN_EVERY_N_VALIDATIONS
            )
        }
    
    async def retrain_model(
        self,
        num_epochs: int = 3,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Retrain T5 model on validated corrections
        
        Args:
            num_epochs: Number of training epochs
            force: Force retraining even if threshold not reached
            
        Returns:
            Retraining result with metrics
        """
        total_examples = await self.training_collection.count_documents({})
        
        # Check if we have enough examples
        if not force and total_examples < self.MIN_TRAINING_EXAMPLES:
            return {
                "status": "skipped",
                "reason": f"Not enough training data ({total_examples}/{self.MIN_TRAINING_EXAMPLES})",
                "success": False
            }
        
        if self.t5_corrector is None or self.t5_corrector.model is None:
            return {
                "status": "error",
                "reason": "T5 model not loaded",
                "success": False
            }
        
        try:
            print(f"🚀 Starting model retraining on {total_examples} examples...")
            start_time = datetime.utcnow()
            
            # Get all training examples
            examples = await self.training_collection.find().to_list(
                length=total_examples
            )
            
            # Convert to T5 format
            training_data = [
                {
                    "input": ex["input_text"],
                    "output": ex["output_text"]
                }
                for ex in examples
            ]
            
            # Create versioned model path
            version = f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            output_dir = f"{self.MODEL_SAVE_PATH}_{version}"
            
            # Fine-tune model (this may take several minutes)
            self.t5_corrector.train(
                training_data=training_data,
                output_dir=output_dir,
                num_epochs=num_epochs
            )
            
            end_time = datetime.utcnow()
            training_duration = (end_time - start_time).total_seconds()
            
            # Save model version metadata
            model_version = {
                "version": version,
                "trained_at": end_time,
                "training_examples": total_examples,
                "num_epochs": num_epochs,
                "training_duration_seconds": training_duration,
                "model_path": output_dir,
                "status": "active"
            }
            
            await self.model_versions_collection.insert_one(model_version)
            
            # Mark previous versions as archived
            await self.model_versions_collection.update_many(
                {"version": {"$ne": version}},
                {"$set": {"status": "archived"}}
            )
            
            print(f"✅ Model retrained successfully in {training_duration:.1f}s")
            print(f"📁 Model saved to: {output_dir}")
            
            return {
                "status": "success",
                "version": version,
                "training_examples": total_examples,
                "training_duration_seconds": training_duration,
                "model_path": output_dir,
                "success": True
            }
            
        except Exception as e:
            print(f"❌ Model retraining failed: {e}")
            return {
                "status": "error",
                "reason": str(e),
                "success": False
            }
    
    async def get_accuracy_trend(
        self,
        months: int = 6
    ) -> Dict[str, Any]:
        """
        Calculate accuracy improvement trend over time
        
        Implements KPI: "Amélioration continue: +5% accuracy/mois"
        
        Args:
            months: Number of months to analyze
            
        Returns:
            Monthly accuracy trends
        """
        start_date = datetime.utcnow() - timedelta(days=30 * months)
        
        # Get training examples by month
        pipeline = [
            {"$match": {"timestamp": {"$gte": start_date}}},
            {"$group": {
                "_id": {
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"}
                },
                "total": {"$sum": 1},
                "ml_correct": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$ml_suggested", "$output_text"]},
                            1,
                            0
                        ]
                    }
                }
            }},
            {"$sort": {"_id.year": 1, "_id.month": 1}}
        ]
        
        cursor = self.training_collection.aggregate(pipeline)
        monthly_data = await cursor.to_list(length=months)
        
        # Calculate accuracy per month
        trend = []
        for data in monthly_data:
            month_str = f"{data['_id']['year']}-{data['_id']['month']:02d}"
            accuracy = data["ml_correct"] / data["total"] if data["total"] > 0 else 0.0
            
            trend.append({
                "month": month_str,
               "accuracy": round(accuracy, 3),
                "total_examples": data["total"]
            })
        
        # Calculate improvement rate
        if len(trend) >= 2:
            first_accuracy = trend[0]["accuracy"]
            last_accuracy = trend[-1]["accuracy"]
            months_diff = len(trend)
            
            if first_accuracy > 0:
                improvement_rate = (last_accuracy - first_accuracy) / first_accuracy / months_diff
            else:
                improvement_rate = 0.0
        else:
            improvement_rate = 0.0
        
        return {
            "monthly_trend": trend,
            "months_analyzed": len(trend),
            "improvement_rate_per_month": round(improvement_rate, 3),
            "meets_kpi": improvement_rate >= 0.05  # 5% per month target
        }
    
    async def export_training_data(
        self,
        output_path: str,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        Export training data for external analysis
        
        Args:
            output_path: Path to save export
            format: Export format (json, csv, jsonl)
            
        Returns:
            Export result
        """
        import json
        
        examples = await self.training_collection.find().to_list(length=10000)
        
        try:
            if format == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(examples, f, indent=2, default=str)
            
            elif format == "jsonl":
                with open(output_path, 'w', encoding='utf-8') as f:
                    for ex in examples:
                        f.write(json.dumps(ex, default=str) + '\n')
            
            elif format == "csv":
                import pandas as pd
                df = pd.DataFrame(examples)
                df.to_csv(output_path, index=False)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            return {
                "status": "success",
                "exported_examples": len(examples),
                "output_path": output_path,
                "format": format
            }
            
        except Exception as e:
            return {
                "status": "error",
                "reason": str(e)
            }
    
    async def cleanup_old_examples(
        self,
        keep_days: int = 90
    ) -> Dict[str, Any]:
        """
        Clean up old training examples to manage database size
        
        Args:
            keep_days: Keep only examples from last N days
            
        Returns:
            Cleanup result
        """
        cutoff_date = datetime.utcnow() - timedelta(days=keep_days)
        
        result = await self.training_collection.delete_many({
            "timestamp": {"$lt": cutoff_date}
        })
        
        return {
            "deleted": result.deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
