"""
KPI Tracker
============
Data Quality V2 - Section 8.7

Track and monitor Key Performance Indicators for the correction service.

KPI Targets (from specification):
- Detection rate > 95%
- Auto-correction precision > 90%
- Auto-correction rate > 70%
- Processing time < 5s per 1000 rows
- Accuracy improvement +5% per month
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import time


class KPITracker:
    """
    Tracks and monitors correction service KPIs
    
    Stores historical metrics and provides trend analysis
    """
    
    # Target values from Section 8.7
    TARGETS = {
        "detection_rate": 0.95,
        "auto_correction_precision": 0.90,
        "auto_correction_rate": 0.70,
        "processing_time_per_1000_rows": 5.0,  # seconds
        "monthly_accuracy_improvement": 0.05  # 5% per month
    }
    
    def __init__(self, db):
        self.db = db
        self.kpi_history = db.correction_kpi_history
        self.corrections_collection = db.correction_validations
    
    async def record_kpi_snapshot(
        self,
        dataset_id: Optional[str] = None,
        custom_metrics: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Record a KPI snapshot
        
        Args:
            dataset_id: Optional dataset ID for dataset-specific KPIs
            custom_metrics: Additional custom metrics to track
            
        Returns:
            Recorded KPI snapshot
        """
        # Calculate current KPIs
        kpis = await self._calculate_current_kpis(dataset_id)
        
        # Add custom metrics if provided
        if custom_metrics:
            kpis.update(custom_metrics)
        
        # Create snapshot
        snapshot = {
            "timestamp": datetime.utcnow(),
            "dataset_id": dataset_id,
            "kpis": kpis,
            "targets": self.TARGETS,
            "compliance": self._check_compliance(kpis)
        }
        
        # Save to database
        await self.kpi_history.insert_one(snapshot)
        
        return snapshot
    
    async def _calculate_current_kpis(
        self,
        dataset_id: Optional[str] = None
    ) -> Dict[str, float]:
        """Calculate current KPI values"""
        query = {}
        if dataset_id:
            query["dataset_id"] = dataset_id
        
        # Get recent corrections
        corrections = await self.corrections_collection.find(query).to_list(length=10000)
        
        if not corrections:
            return {
                "detection_rate": 0.0,
                "auto_correction_precision": 0.0,
                "auto_correction_rate": 0.0,
                "total_corrections": 0
            }
        
        total = len(corrections)
        
        # Auto-correction rate (percentage auto-applied)
        auto_applied = sum(1 for c in corrections if c.get("auto", False))
        auto_correction_rate = auto_applied / total if total > 0 else 0
        
        # Auto-correction precision (of validated corrections, what % were accepted)
        validated = [c for c in corrections if "validation" in c and c.get("auto", False)]
        if validated:
            accepted = sum(
                1 for c in validated 
                if c["validation"].get("decision") in ["accept", "modify"]
            )
            auto_correction_precision = accepted / len(validated)
        else:
            auto_correction_precision = 0.0
        
        # Detection rate (would need ground truth data - estimate from high confidence)
        high_confidence = sum(1 for c in corrections if c.get("confidence", 0) >= 0.8)
        detection_rate = high_confidence / total if total > 0 else 0
        
        # Average confidence
        avg_confidence = sum(c.get("confidence", 0) for c in corrections) / total if total > 0 else 0
        
        return {
            "detection_rate": round(detection_rate, 3),
            "auto_correction_precision": round(auto_correction_precision, 3),
            "auto_correction_rate": round(auto_correction_rate, 3),
            "total_corrections": total,
            "auto_applied_count": auto_applied,
            "avg_confidence": round(avg_confidence, 3)
        }
    
    def _check_compliance(self, kpis: Dict[str, float]) -> Dict[str, bool]:
        """Check if KPIs meet targets"""
        compliance = {}
        
        for metric, target in self.TARGETS.items():
            if metric in kpis:
                if metric == "processing_time_per_1000_rows":
                    # For time, lower is better
                    compliance[metric] = kpis[metric] <= target
                else:
                    # For rates, higher is better
                    compliance[metric] = kpis[metric] >= target
        
        return compliance
    
    async def get_kpi_summary(
        self,
        dataset_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get KPI summary for recent period
        
        Args:
            dataset_id: Optional dataset filter
            days: Number of days to analyze
            
        Returns:
            KPI summary with compliance status
        """
        # Get recent snapshot
        query = {}
        if dataset_id:
            query["dataset_id"] = dataset_id
        
        recent_snapshot = await self.kpi_history.find_one(
            query,
            sort=[("timestamp", -1)]
        )
        
        if not recent_snapshot:
            # Calculate fresh KPIs
            current_kpis = await self._calculate_current_kpis(dataset_id)
            compliance = self._check_compliance(current_kpis)
            recent_snapshot = {
                "kpis": current_kpis,
                "compliance": compliance,
                "timestamp": datetime.utcnow(),
                "targets": self.TARGETS
            }
        
        # Get historical trend
        start_date = datetime.utcnow() - timedelta(days=days)
        query["timestamp"] = {"$gte": start_date}
        
        historical = await self.kpi_history.find(query).sort("timestamp", 1).to_list(length=1000)
        
        trend = self._calculate_trend(historical)
        
        return {
            "current": recent_snapshot["kpis"],
            "targets": self.TARGETS,
            "compliance": recent_snapshot["compliance"],
            "trend": trend,
            "timestamp": recent_snapshot["timestamp"],
            "period_days": days
        }
    
    def _calculate_trend(self, historical: List[Dict]) -> Dict[str, Any]:
        """Calculate KPI trends from historical data"""
        if len(historical) < 2:
            return {"status": "insufficient_data"}
        
        # Get first and last snapshots
        first = historical[0]
        last = historical[-1]
        
        trends = {}
        
        for metric in ["detection_rate", "auto_correction_precision", "auto_correction_rate"]:
            if metric in first["kpis"] and metric in last["kpis"]:
                start_val = first["kpis"][metric]
                end_val = last["kpis"][metric]
                
                if start_val > 0:
                    change_pct = ((end_val - start_val) / start_val) * 100
                else:
                    change_pct = 0.0
                
                trends[metric] = {
                    "start_value": round(start_val, 3),
                    "end_value": round(end_val, 3),
                    "change_percent": round(change_pct, 2),
                    "direction": "improving" if change_pct > 0 else ("declining" if change_pct < 0 else "stable")
                }
        
        return trends
    
    async def track_processing_time(
        self,
        num_rows: int,
        processing_time_seconds: float,
        dataset_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Track processing time performance
        
        Args:
            num_rows: Number of rows processed
            processing_time_seconds: Time taken in seconds
            dataset_id: Optional dataset ID
            
        Returns:
            Performance metrics
        """
        # Normalize to time per 1000 rows
        time_per_1000 = (processing_time_seconds / num_rows) * 1000 if num_rows > 0 else 0
        
        meets_target = time_per_1000 <= self.TARGETS["processing_time_per_1000_rows"]
        
        # Record performance
        perf_record = {
            "timestamp": datetime.utcnow(),
            "dataset_id": dataset_id,
            "num_rows": num_rows,
            "processing_time_seconds": processing_time_seconds,
            "time_per_1000_rows": round(time_per_1000, 2),
            "meets_target": meets_target,
            "target": self.TARGETS["processing_time_per_1000_rows"]
        }
        
        await self.db.correction_performance.insert_one(perf_record)
        
        return perf_record
    
    async def get_performance_stats(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get processing time performance statistics
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Performance statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        cursor = self.db.correction_performance.find({
            "timestamp": {"$gte": start_date}
        })
        
        records = await cursor.to_list(length=10000)
        
        if not records:
            return {"status": "no_data"}
        
        times = [r["time_per_1000_rows"] for r in records]
        rows_processed = sum(r["num_rows"] for r in records)
        
        import numpy as np
        
        return {
            "total_batches": len(records),
            "total_rows_processed": rows_processed,
            "avg_time_per_1000_rows": round(np.mean(times), 2),
            "min_time_per_1000_rows": round(min(times), 2),
            "max_time_per_1000_rows": round(max(times), 2),
            "median_time_per_1000_rows": round(np.median(times), 2),
            "target": self.TARGETS["processing_time_per_1000_rows"],
            "meets_target": np.mean(times) <= self.TARGETS["processing_time_per_1000_rows"],
            "batches_meeting_target": sum(1 for r in records if r["meets_target"]),
            "target_compliance_rate": round(
                sum(1 for r in records if r["meets_target"]) / len(records), 
                3
            )
        }
    
    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics for dashboard display
        
        Returns:
            Comprehensive dashboard data
        """
        kpi_summary = await self.get_kpi_summary(days=30)
        performance = await self.get_performance_stats(days=7)
        
        # Overall health score (0-100)
        compliance = kpi_summary.get("compliance", {})
        compliance_score = sum(1 for v in compliance.values() if v) / len(compliance) * 100 if compliance else 0
        
        return {
            "health_score": round(compliance_score, 1),
            "kpis": kpi_summary,
            "performance": performance,
            "alerts": self._generate_alerts(kpi_summary, performance)
        }
    
    def _generate_alerts(
        self,
        kpi_summary: Dict[str, Any],
        performance: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate alerts for KPIs not meeting targets"""
        alerts = []
        
        compliance = kpi_summary.get("compliance", {})
        current = kpi_summary.get("current", {})
        
        for metric, meets_target in compliance.items():
            if not meets_target:
                target = self.TARGETS.get(metric, 0)
                current_val = current.get(metric, 0)
                
                alerts.append({
                    "severity": "warning",
                    "metric": metric,
                    "message": f"{metric.replace('_', ' ').title()} ({current_val:.2%}) below target ({target:.2%})",
                    "current_value": current_val,
                    "target_value": target
                })
        
        # Check performance
        if performance.get("status") != "no_data":
            if not performance.get("meets_target", True):
                alerts.append({
                    "severity": "warning",
                    "metric": "processing_time",
                    "message": f"Processing time ({performance.get('avg_time_per_1000_rows')}s) exceeds target ({self.TARGETS['processing_time_per_1000_rows']}s per 1000 rows)",
                    "current_value": performance.get('avg_time_per_1000_rows'),
                    "target_value": self.TARGETS['processing_time_per_1000_rows']
                })
        
        return alerts
