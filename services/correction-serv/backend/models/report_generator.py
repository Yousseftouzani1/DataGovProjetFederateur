"""
Report Generator
=================
Data Quality V2 - User Story US-CORR-06

Generate comprehensive correction reports with full traceability.

"En tant qu'utilisateur, je veux générer un rapport de correction 
avec traçabilité"
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd


class ReportGenerator:
    """
    Generates comprehensive correction reports with traceability
    
    Report includes:
    - Summary statistics
    - Breakdown by inconsistency type
    - Correction details (before/after)
    - Confidence score distributions
    - Timeline of corrections
    - Validator contributions
    """
    
    def __init__(self, db):
        self.db = db
        self.corrections_collection = db.correction_validations
        self.history_collection = db.correction_history
    
    async def generate_correction_report(
        self,
        dataset_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive correction report for a dataset
        
        Args:
            dataset_id: ID of dataset
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Complete correction report
        """
        # Build query
        query = {"dataset_id": dataset_id}
        
        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date
            if end_date:
                query["timestamp"]["$lte"] = end_date
        
        # Get all corrections for this dataset
        corrections = await self.corrections_collection.find(query).to_list(length=10000)
        
        if not corrections:
            return {
                "dataset_id": dataset_id,
                "report_generated_at": datetime.utcnow().isoformat(),
                "status": "no_corrections_found",
                "summary": {"total_corrections": 0}
            }
        
        # Generate report sections
        summary = self._generate_summary(corrections)
        by_type = self._breakdown_by_type(corrections)
        by_field = self._breakdown_by_field(corrections)
        confidence_dist = self._confidence_distribution(corrections)
        timeline = self._corrections_timeline(corrections)
        details = self._correction_details(corrections[:100])  # First 100 for readability
        validators = self._validator_contributions(corrections)
        
        report = {
            "dataset_id": dataset_id,
            "report_generated_at": datetime.utcnow().isoformat(),
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            },
            "summary": summary,
            "breakdown_by_type": by_type,
            "breakdown_by_field": by_field,
            "confidence_distribution": confidence_dist,
            "timeline": timeline,
            "validator_contributions": validators,
            "correction_details": details,
            "kpi_metrics": self._calculate_kpis(corrections)
        }
        
        return report
    
    def _generate_summary(self, corrections: List[Dict]) -> Dict[str, Any]:
        """Generate summary statistics"""
        total = len(corrections)
        
        auto_applied = sum(1 for c in corrections if c.get("auto", False))
        manual_review = sum(1 for c in corrections if not c.get("auto", False))
        
        validated = sum(1 for c in corrections if "validation" in c)
        accepted = sum(
            1 for c in corrections 
            if c.get("validation", {}).get("decision") == "accept"
        )
        rejected = sum(
            1 for c in corrections 
            if c.get("validation", {}).get("decision") == "reject"
        )
        modified = sum(
            1 for c in corrections 
            if c.get("validation", {}).get("decision") == "modify"
        )
        
        avg_confidence = sum(c.get("confidence", 0) for c in corrections) / total if total > 0 else 0
        
        return {
            "total_corrections": total,
            "auto_applied": auto_applied,
            "manual_review": manual_review,
            "validated": validated,
            "validation_breakdown": {
                "accepted": accepted,
                "rejected": rejected,
                "modified": modified
            },
            "auto_apply_rate": round(auto_applied / total, 3) if total > 0 else 0,
            "validation_rate": round(validated / total, 3) if total > 0 else 0,
            "acceptance_rate": round(accepted / validated, 3) if validated > 0 else 0,
            "average_confidence": round(avg_confidence, 3)
        }
    
    def _breakdown_by_type(self, corrections: List[Dict]) -> Dict[str, Any]:
        """Breakdown by inconsistency type"""
        by_type = {}
        
        for correction in corrections:
            inc_type = correction.get("type", "UNKNOWN")
            
            if inc_type not in by_type:
                by_type[inc_type] = {
                    "count": 0,
                    "auto_applied": 0,
                    "avg_confidence": 0,
                    "confidences": []
                }
            
            by_type[inc_type]["count"] += 1
            if correction.get("auto", False):
                by_type[inc_type]["auto_applied"] += 1
            
            conf = correction.get("confidence", 0)
            by_type[inc_type]["confidences"].append(conf)
        
        # Calculate averages
        for type_name, data in by_type.items():
            if data["confidences"]:
                data["avg_confidence"] = round(
                    sum(data["confidences"]) / len(data["confidences"]), 
                    3
                )
            del data["confidences"]  # Remove raw list
        
        return by_type
    
    def _breakdown_by_field(self, corrections: List[Dict]) -> Dict[str, int]:
        """Breakdown by field"""
        by_field = {}
        
        for correction in corrections:
            field = correction.get("field", "unknown")
            by_field[field] = by_field.get(field, 0) + 1
        
        # Sort by count descending
        return dict(sorted(by_field.items(), key=lambda x: x[1], reverse=True))
    
    def _confidence_distribution(self, corrections: List[Dict]) -> Dict[str, Any]:
        """Analyze confidence score distribution"""
        confidences = [c.get("confidence", 0) for c in corrections]
        
        if not confidences:
            return {}
        
        import numpy as np
        
        return {
            "min": round(min(confidences), 3),
            "max": round(max(confidences), 3),
            "mean": round(np.mean(confidences), 3),
            "median": round(np.median(confidences), 3),
            "std": round(np.std(confidences), 3),
            "percentiles": {
                "25": round(np.percentile(confidences, 25), 3),
                "50": round(np.percentile(confidences, 50), 3),
                "75": round(np.percentile(confidences, 75), 3),
                "90": round(np.percentile(confidences, 90), 3)
            },
            "high_confidence_count": sum(1 for c in confidences if c >= 0.9),
            "medium_confidence_count": sum(1 for c in confidences if 0.6 <= c < 0.9),
            "low_confidence_count": sum(1 for c in confidences if c < 0.6)
        }
    
    def _corrections_timeline(self, corrections: List[Dict]) -> List[Dict[str, Any]]:
        """Create timeline of corrections"""
        timeline_data = {}
        
        for correction in corrections:
            timestamp = correction.get("timestamp") or correction.get("added_to_queue_at")
            
            if not timestamp:
                continue
            
            # Group by date
            if isinstance(timestamp, str):
                date_str = timestamp.split("T")[0]
            else:
                date_str = timestamp.strftime("%Y-%m-%d")
            
            if date_str not in timeline_data:
                timeline_data[date_str] = {
                    "date": date_str,
                    "corrections": 0,
                    "auto_applied": 0
                }
            
            timeline_data[date_str]["corrections"] += 1
            if correction.get("auto", False):
                timeline_data[date_str]["auto_applied"] += 1
        
        # Sort by date
        timeline = sorted(timeline_data.values(), key=lambda x: x["date"])
        
        return timeline
    
    def _correction_details(self, corrections: List[Dict]) -> List[Dict[str, Any]]:
        """Detailed list of corrections (limited to first 100)"""
        details = []
        
        for correction in corrections:
            detail = {
                "field": correction.get("field"),
                "original_value": correction.get("old_value"),
                "suggested_value": correction.get("new_value") or \
                    (correction.get("candidates", [{}])[0].get("value") if "candidates" in correction else None),
                "final_value": correction.get("final_value"),
                "type": correction.get("type"),
                "confidence": correction.get("confidence"),
                "auto_applied": correction.get("auto", False),
                "source": correction.get("source"),
                "timestamp": str(correction.get("timestamp") or correction.get("added_to_queue_at"))
            }
            
            # Add validation info if available
            if "validation" in correction:
                val = correction["validation"]
                detail["validation"] = {
                    "decision": val.get("decision"),
                    "validator": val.get("validator_id"),
                    "comments": val.get("comments")
                }
            
            details.append(detail)
        
        return details
    
    def _validator_contributions(self, corrections: List[Dict]) -> Dict[str, Any]:
        """Analyze validator contributions"""
        validator_stats = {}
        
        for correction in corrections:
            if "validation" not in correction:
                continue
            
            validator_id = correction["validation"].get("validator_id", "unknown")
            
            if validator_id not in validator_stats:
                validator_stats[validator_id] = {
                    "total_validations": 0,
                    "accepted": 0,
                    "rejected": 0,
                    "modified": 0
                }
            
            validator_stats[validator_id]["total_validations"] += 1
            
            decision = correction["validation"].get("decision")
            if decision == "accept":
                validator_stats[validator_id]["accepted"] += 1
            elif decision == "reject":
                validator_stats[validator_id]["rejected"] += 1
            elif decision == "modify":
                validator_stats[validator_id]["modified"] += 1
        
        # Calculate acceptance rates
        for stats in validator_stats.values():
            total = stats["total_validations"]
            if total > 0:
                stats["acceptance_rate"] = round(
                    (stats["accepted"] + stats["modified"]) / total, 
                    3
                )
        
        return validator_stats
    
    def _calculate_kpis(self, corrections: List[Dict]) -> Dict[str, Any]:
        """Calculate KPIs per Section 8.7"""
        total = len(corrections)
        
        if total == 0:
            return {}
        
        auto_applied = sum(1 for c in corrections if c.get("auto", False))
        validated = [c for c in corrections if "validation" in c]
        accepted = sum(
            1 for c in validated 
            if c["validation"].get("decision") in ["accept", "modify"]
        )
        
        return {
            "auto_correction_rate": round(auto_applied / total, 3),
            "auto_correction_precision": round(accepted / len(validated), 3) if validated else 0,
            "target_auto_rate": 0.70,
            "target_precision": 0.90,
            "meets_auto_rate_target": (auto_applied / total) >= 0.70,
            "meets_precision_target": (accepted / len(validated) >= 0.90) if validated else False
        }
    
    async def export_report(
        self,
        report: Dict[str, Any],
        format: str = "json",
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export report to file
        
        Args:
            report: Report data
            format: 'json', 'pdf', or 'excel'
            output_path: Path to save report
            
        Returns:
            Export result
        """
        if not output_path:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_path = f"./reports/correction_report_{timestamp}.{format}"
        
        try:
            if format == "json":
                import json
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, default=str)
            
            elif format == "excel":
                # Create multi-sheet Excel report
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    # Summary sheet
                    pd.DataFrame([report["summary"]]).T.to_excel(writer, sheet_name="Summary")
                    
                    # By type sheet
                    pd.DataFrame(report["breakdown_by_type"]).T.to_excel(writer, sheet_name="By Type")
                    
                    # Details sheet
                    pd.DataFrame(report["correction_details"]).to_excel(writer, sheet_name="Details", index=False)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            return {
                "status": "success",
                "output_path": output_path,
                "format": format
            }
            
        except Exception as e:
            return {
                "status": "error",
                "reason": str(e)
            }
