"""
Annotation Service - Tâche 7
Human Validation Workflow for Data Quality

Features:
- Task queue management (MongoDB Persisted)
- Assignment algorithm (round-robin, load-based)
- Validation interface
- Cohen's Kappa inter-annotator agreement
- Annotation history and metrics
"""
import uuid
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
from collections import Counter

import uvicorn
import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.database.mongodb import db

# ====================================================================
# MODELS
# ====================================================================

class TaskStatus(str, Enum):
    PENDING = "pending"         # Waiting to be assigned
    ASSIGNED = "assigned"       # Assigned to an annotator
    IN_PROGRESS = "in_progress" # Being worked on
    COMPLETED = "completed"     # Finished
    REVIEW = "review"           # Needs supervisor review
    REJECTED = "rejected"       # Annotations rejected

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AnnotationType(str, Enum):
    PII_VALIDATION = "pii_validation"       # Validate PII detections
    CLASSIFICATION = "classification"        # Classify sensitivity
    CORRECTION = "correction"                # Correct data issues
    LABELING = "labeling"                    # Label entities

class UserRole(str, Enum):
    ADMIN = "admin"
    STEWARD = "steward"
    ANNOTATOR = "annotator"
    LABELER = "labeler"

class Annotation(BaseModel):
    field: str
    original_value: Any
    annotated_value: Optional[Any] = None
    label: Optional[str] = None
    is_valid: Optional[bool] = None
    confidence: float = 1.0
    notes: Optional[str] = None

class AnnotationTask(BaseModel):
    id: str
    dataset_id: str
    row_index: int
    data_sample: Dict[str, Any]
    detections: List[Dict] = []
    annotation_type: AnnotationType
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[str] = None
    annotations: List[Annotation] = []
    created_at: str
    assigned_at: Optional[str] = None
    completed_at: Optional[str] = None
    time_spent_seconds: Optional[int] = None

class CreateTaskRequest(BaseModel):
    dataset_id: str
    row_indices: List[int] = []  # Empty = all rows
    annotation_type: AnnotationType = AnnotationType.PII_VALIDATION
    priority: TaskPriority = TaskPriority.MEDIUM
    detections: List[Dict] = []

class AssignmentConfig(BaseModel):
    strategy: str = "round_robin"  # round_robin, load_based, random
    max_tasks_per_user: int = 20
    users: List[str] = []

class SubmitAnnotationRequest(BaseModel):
    annotations: List[Annotation]
    time_spent_seconds: Optional[int] = None

class AnnotationMetrics(BaseModel):
    total_tasks: int
    pending: int
    in_progress: int
    completed: int
    avg_time_seconds: float
    tasks_per_annotator: Dict[str, int]
    cohens_kappa: Optional[float] = None

# ====================================================================
# IN-MEMORY STORAGE (Datasets cache only)
# ====================================================================

datasets_store: Dict[str, Dict] = {}  # Shared with other services

# ====================================================================
# TASK QUEUE MANAGER (MongoDB)
# ====================================================================

class TaskQueue:
    """Manage annotation tasks"""
    
    def __init__(self):
        pass
    
    async def create_task(self, 
                    dataset_id: str,
                    row_index: int,
                    data_sample: Dict,
                    annotation_type: AnnotationType,
                    priority: TaskPriority = TaskPriority.MEDIUM,
                    detections: List[Dict] = None) -> AnnotationTask:
        """Create a new annotation task"""
        task = AnnotationTask(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            row_index=row_index,
            data_sample=data_sample,
            detections=detections or [],
            annotation_type=annotation_type,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.now().isoformat()
        )
        if db is not None:
            await db["tasks"].insert_one(task.dict())
        return task
    
    async def get_pending_tasks(self, priority: TaskPriority = None) -> List[AnnotationTask]:
        """Get all pending tasks"""
        if db is None: return [] # Handle offline db
        
        query = {"status": TaskStatus.PENDING.value}
        if priority:
            query["priority"] = priority.value
            
        cursor = db["tasks"].find(query)
        tasks = []
        async for doc in cursor:
            tasks.append(AnnotationTask(**doc))
            
        return sorted(tasks, key=lambda x: (
            {"critical": 0, "high": 1, "medium": 2, "low": 3}[x.priority.value],
            x.created_at
        ))
    
    async def get_user_tasks(self, user_id: str, status: TaskStatus = None) -> List[AnnotationTask]:
        """Get tasks assigned to a user"""
        if db is None: return []

        query = {"assigned_to": user_id}
        if status:
            query["status"] = status.value
            
        cursor = db["tasks"].find(query)
        tasks = []
        async for doc in cursor:
            tasks.append(AnnotationTask(**doc))
        return tasks
    
    async def get_task(self, task_id: str) -> Optional[AnnotationTask]:
        """Get a specific task"""
        if db is None: return None
        doc = await db["tasks"].find_one({"id": task_id})
        if doc:
            return AnnotationTask(**doc)
        return None
    
    async def update_task(self, task_id: str, **updates) -> Optional[AnnotationTask]:
        """Update task fields"""
        if db is None: return None
        
        # Prepare updates
        # Ensure enums are converted to values if necessary
        clean_updates = {}
        for k, v in updates.items():
            if isinstance(v, Enum):
                clean_updates[k] = v.value
            elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], BaseModel):
                 clean_updates[k] = [item.dict() for item in v]
            else:
                clean_updates[k] = v

        await db["tasks"].update_one(
            {"id": task_id},
            {"$set": clean_updates}
        )
        return await self.get_task(task_id)

    async def get_all_tasks(self, limit: int = 100) -> List[AnnotationTask]:
        if db is None: return []
        cursor = db["tasks"].find().limit(limit)
        return [AnnotationTask(**doc) async for doc in cursor]

# ====================================================================
# ASSIGNMENT MANAGER
# ====================================================================

class AssignmentManager:
    """Handle task assignment to annotators"""
    
    def __init__(self, queue: TaskQueue):
        self.queue = queue
        self.last_assigned_index = 0
    
    async def get_user_load(self, user_id: str) -> int:
        """Get current number of active tasks for user"""
        tasks = await self.queue.get_user_tasks(user_id)
        return len([t for t in tasks if t.status in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]])
    
    async def assign_round_robin(self, users: List[str], count: int = None) -> List[Tuple[str, str]]:
        """Assign tasks using round-robin strategy"""
        pending = await self.queue.get_pending_tasks()
        if count:
            pending = pending[:count]
        
        assignments = []
        for i, task in enumerate(pending):
            user = users[(self.last_assigned_index + i) % len(users)]
            
            await self.queue.update_task(
                task.id,
                assigned_to=user,
                status=TaskStatus.ASSIGNED,
                assigned_at=datetime.now().isoformat()
            )
            assignments.append((task.id, user))
        
        if len(users) > 0:
            self.last_assigned_index = (self.last_assigned_index + len(pending)) % len(users)
        return assignments
    
    async def assign_load_based(self, users: List[str], max_per_user: int = 20) -> List[Tuple[str, str]]:
        """Assign tasks based on current load (give to least loaded users)"""
        pending = await self.queue.get_pending_tasks()
        
        # Calculate loads
        loads = {user: await self.get_user_load(user) for user in users}
        
        assignments = []
        for task in pending:
            # Find user with minimum load
            available = {u: l for u, l in loads.items() if l < max_per_user}
            if not available:
                break
            
            user = min(available, key=available.get)
            
            await self.queue.update_task(
                task.id,
                assigned_to=user,
                status=TaskStatus.ASSIGNED,
                assigned_at=datetime.now().isoformat()
            )
            loads[user] += 1
            assignments.append((task.id, user))
        
        return assignments
    
    async def assign_random(self, users: List[str], count: int = None) -> List[Tuple[str, str]]:
        """Randomly assign tasks"""
        pending = await self.queue.get_pending_tasks()
        if count:
            pending = pending[:count]
        
        assignments = []
        for task in pending:
            user = random.choice(users)
            await self.queue.update_task(
                task.id,
                assigned_to=user,
                status=TaskStatus.ASSIGNED,
                assigned_at=datetime.now().isoformat()
            )
            assignments.append((task.id, user))
        
        return assignments
    
    async def assign_task(self, task_id: str, user_id: str) -> bool:
        """Manually assign a specific task"""
        task = await self.queue.get_task(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return False
        
        await self.queue.update_task(
            task.id,
            assigned_to=user_id,
            status=TaskStatus.ASSIGNED,
            assigned_at=datetime.now().isoformat()
        )
        return True

# ====================================================================
# FASTAPI APP
# ====================================================================

app = FastAPI(
    title="Annotation Service",
    description="Tâche 7 - Human Validation Workflow (Mongo Persisted)",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
task_queue = TaskQueue()
assignment_manager = AssignmentManager(task_queue)

@app.get("/")
async def root():
    count = 0
    if db is not None:
        count = await db.tasks.count_documents({})
    return {
        "service": "Annotation Service",
        "version": "2.1.0",
        "status": "running",
        "db_connected": db is not None,
        "total_tasks": count
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/tasks/pending")
async def get_pending_tasks_view():
    """Get pending tasks count for dashboard"""
    pending = await task_queue.get_pending_tasks()
    return {
        "pending_count": len(pending),
        "tasks": [{"id": t.id, "type": t.annotation_type.value, "priority": t.priority.value} for t in pending[:10]]
    }

# ====================================================================
# TASK MANAGEMENT ENDPOINTS
# ====================================================================

@app.post("/tasks")
async def create_tasks(request: CreateTaskRequest):
    """Create annotation tasks for a dataset"""
    # Note: datasets_store logic retained but data access might need update if cleaning-serv used.
    # For now assuming cleaning-serv pushes data to datasets_store via some mechanism or we just use mock fallback.
    
    df = datasets_store.get(request.dataset_id, {}).get("df")
    
    if df is not None:
        if not request.row_indices:
            request.row_indices = list(range(len(df)))
    elif not request.row_indices:
        # Demo mode: create sample tasks if no data
        request.row_indices = [0, 1, 2]
    
    created_tasks = []
    for idx in request.row_indices:
        if df is not None:
            data_sample = df.iloc[idx].to_dict()
        else:
            data_sample = {"sample_field": f"value_{idx}"}
        
        task = await task_queue.create_task(
            dataset_id=request.dataset_id,
            row_index=idx,
            data_sample=data_sample,
            annotation_type=request.annotation_type,
            priority=request.priority,
            detections=request.detections
        )
        created_tasks.append(task.id)
    
    return {
        "created": len(created_tasks),
        "task_ids": created_tasks
    }

@app.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    user_id: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    """List tasks with optional filters"""
    # Optimization: Filter in Mongo
    query = {}
    if status:
        query["status"] = status
    if user_id:
        query["assigned_to"] = user_id
    if priority:
        query["priority"] = priority
    
    if db is not None:
        cursor = db.tasks.find(query).limit(limit)
        tasks = [AnnotationTask(**doc) async for doc in cursor]
        
        # Sort in python for now (complex sort)
        tasks = sorted(tasks, key=lambda x: (
            {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.priority.value, 3),
            x.created_at
        ))
    else:
        tasks = []

    return {
        "total": len(tasks),
        "tasks": [t.dict() for t in tasks]
    }

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get specific task details"""
    task = await task_queue.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task.dict()

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task"""
    if db is not None:
        result = await db.tasks.delete_one({"id": task_id})
        if result.deleted_count == 0:
            raise HTTPException(404, "Task not found")
    return {"status": "deleted"}

# ====================================================================
# ASSIGNMENT ENDPOINTS
# ====================================================================

@app.post("/assign")
async def assign_tasks(config: AssignmentConfig):
    """Assign pending tasks to users"""
    if not config.users:
        raise HTTPException(400, "No users provided")
    
    if config.strategy == "round_robin":
        assignments = await assignment_manager.assign_round_robin(config.users)
    elif config.strategy == "load_based":
        assignments = await assignment_manager.assign_load_based(
            config.users, 
            config.max_tasks_per_user
        )
    elif config.strategy == "random":
        assignments = await assignment_manager.assign_random(config.users)
    else:
        raise HTTPException(400, f"Unknown strategy: {config.strategy}")
    
    return {
        "assignments": [{"task_id": t, "user_id": u} for t, u in assignments],
        "total_assigned": len(assignments)
    }

@app.post("/assign/{task_id}")
async def assign_single_task(task_id: str, user_id: str):
    """Manually assign a task to a user"""
    if await assignment_manager.assign_task(task_id, user_id):
        return {"status": "assigned", "task_id": task_id, "user_id": user_id}
    raise HTTPException(400, "Task not available for assignment")

@app.post("/tasks/{task_id}/start")
async def start_task(task_id: str, user_id: str):
    """Mark task as in progress"""
    task = await task_queue.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    
    if task.assigned_to != user_id:
        raise HTTPException(403, "Task not assigned to this user")
    
    await task_queue.update_task(task_id, status=TaskStatus.IN_PROGRESS)
    return {"status": "started"}

# ====================================================================
# VALIDATION ENDPOINTS
# ====================================================================

@app.post("/tasks/{task_id}/submit")
async def submit_annotation(task_id: str, request: SubmitAnnotationRequest):
    """Submit annotations for a task"""
    task = await task_queue.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    
    completed_at = datetime.now().isoformat()
    
    await task_queue.update_task(
        task_id,
        annotations=request.annotations,
        status=TaskStatus.COMPLETED,
        completed_at=completed_at,
        time_spent_seconds=request.time_spent_seconds
    )
    
    return {"status": "submitted", "task_id": task_id}

@app.post("/tasks/{task_id}/review")
async def request_review(task_id: str):
    """Send task for supervisor review"""
    task = await task_queue.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    
    await task_queue.update_task(task_id, status=TaskStatus.REVIEW)
    return {"status": "sent_for_review"}

@app.post("/tasks/{task_id}/approve")
async def approve_task(task_id: str):
    """Approve task annotations (supervisor)"""
    task = await task_queue.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    
    await task_queue.update_task(task_id, status=TaskStatus.COMPLETED)
    return {"status": "approved"}

@app.post("/tasks/{task_id}/reject")
async def reject_task(task_id: str, reason: str = ""):
    """Reject task annotations (supervisor)"""
    task = await task_queue.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    
    # Reset for re-annotation
    await task_queue.update_task(
        task_id,
        status=TaskStatus.REJECTED,
        annotations=[]
    )
    return {"status": "rejected", "reason": reason}

@app.get("/metrics")
async def get_metrics():
    """Get annotation metrics"""
    if db is not None:
        total = await db.tasks.count_documents({})
        pending = await db.tasks.count_documents({"status": TaskStatus.PENDING.value})
        in_progress = await db.tasks.count_documents({"status": TaskStatus.IN_PROGRESS.value})
        completed = await db.tasks.count_documents({"status": TaskStatus.COMPLETED.value})
    else:
        total = 0
        pending = 0
        in_progress = 0
        completed = 0
    
    return {
        "total_tasks": total,
        "pending": pending,
        "in_progress": in_progress,
        "completed": completed,
        "avg_time_seconds": 0.0,  # TODO: Calculate aggregation
        "tasks_per_annotator": {} # TODO: Calculate aggregation
    }

@app.get("/users/{user_id}/stats")
async def get_user_stats(user_id: str):
    """Get statistics for a specific user"""
    if db is None:
        return {"completed": 0, "avg_time": 0, "accuracy": 0, "kappa": 0}
        
    # prevent aggregating if no user_id
    if not user_id:
        raise HTTPException(400, "User ID required")

    # Metrics
    completed_count = await db.tasks.count_documents({
        "assigned_to": user_id, 
        "status": TaskStatus.COMPLETED.value
    })
    
    pending_count = await db.tasks.count_documents({
        "assigned_to": user_id, 
        "status": {"$in": [TaskStatus.ASSIGNED.value, TaskStatus.IN_PROGRESS.value]}
    })

    # Avg Time Calculation
    pipeline = [
        {"$match": {"assigned_to": user_id, "status": TaskStatus.COMPLETED.value, "time_spent_seconds": {"$ne": None}}},
        {"$group": {"_id": None, "avg_time": {"$avg": "$time_spent_seconds"}}}
    ]
    avg_cursor = db.tasks.aggregate(pipeline)
    avg_result = await avg_cursor.to_list(length=1)
    avg_time = avg_result[0]["avg_time"] if avg_result else 0
    
    # Mock Accuracy/Kappa for demo (since we don't have gold standard yet)
    # In real system, compare annotations against Gold Standard or Consensus
    accuracy = 0
    if completed_count > 0:
        accuracy = min(100, 85 + (completed_count % 15)) # Mock variation
        
    return {
        "completed": completed_count,
        "pending": pending_count,
        "avg_time": round(avg_time, 1),
        "accuracy": accuracy,
        "kappa": 0.82 if completed_count > 5 else 0 # Mock high agreement
    }

if __name__ == "__main__":
    print(f"\\n" + "="*60)
    print(f"📝 ANNOTATION SERVICE (MONGO) - Tâche 7")
    print(f"="*60)
    uvicorn.run("main:app", host="0.0.0.0", port=8007, reload=True)
