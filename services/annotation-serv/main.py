"""
Annotation Service - Tâche 7
Human Validation Workflow for Data Quality

Features:
- Task queue management
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
# IN-MEMORY STORAGE
# ====================================================================

tasks_store: Dict[str, AnnotationTask] = {}
datasets_store: Dict[str, Dict] = {}  # Shared with other services
user_assignments: Dict[str, List[str]] = {}  # user_id -> task_ids
annotation_history: List[Dict] = []

# ====================================================================
# TASK QUEUE MANAGER
# ====================================================================

class TaskQueue:
    """Manage annotation tasks"""
    
    def __init__(self):
        self.tasks = tasks_store
    
    def create_task(self, 
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
        self.tasks[task.id] = task
        return task
    
    def get_pending_tasks(self, priority: TaskPriority = None) -> List[AnnotationTask]:
        """Get all pending tasks"""
        tasks = [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
        if priority:
            tasks = [t for t in tasks if t.priority == priority]
        return sorted(tasks, key=lambda x: (
            {"critical": 0, "high": 1, "medium": 2, "low": 3}[x.priority.value],
            x.created_at
        ))
    
    def get_user_tasks(self, user_id: str, status: TaskStatus = None) -> List[AnnotationTask]:
        """Get tasks assigned to a user"""
        tasks = [t for t in self.tasks.values() if t.assigned_to == user_id]
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks
    
    def get_task(self, task_id: str) -> Optional[AnnotationTask]:
        """Get a specific task"""
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, **updates) -> Optional[AnnotationTask]:
        """Update task fields"""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        return task

# ====================================================================
# ASSIGNMENT MANAGER
# ====================================================================

class AssignmentManager:
    """Handle task assignment to annotators"""
    
    def __init__(self, queue: TaskQueue):
        self.queue = queue
        self.user_loads: Dict[str, int] = {}
        self.last_assigned_index = 0
    
    def get_user_load(self, user_id: str) -> int:
        """Get current number of active tasks for user"""
        tasks = self.queue.get_user_tasks(user_id)
        return len([t for t in tasks if t.status in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]])
    
    def assign_round_robin(self, users: List[str], count: int = None) -> List[Tuple[str, str]]:
        """Assign tasks using round-robin strategy"""
        pending = self.queue.get_pending_tasks()
        if count:
            pending = pending[:count]
        
        assignments = []
        for i, task in enumerate(pending):
            user = users[(self.last_assigned_index + i) % len(users)]
            task.assigned_to = user
            task.status = TaskStatus.ASSIGNED
            task.assigned_at = datetime.now().isoformat()
            assignments.append((task.id, user))
        
        self.last_assigned_index = (self.last_assigned_index + len(pending)) % len(users)
        return assignments
    
    def assign_load_based(self, users: List[str], max_per_user: int = 20) -> List[Tuple[str, str]]:
        """Assign tasks based on current load (give to least loaded users)"""
        pending = self.queue.get_pending_tasks()
        
        # Calculate loads
        loads = {user: self.get_user_load(user) for user in users}
        
        assignments = []
        for task in pending:
            # Find user with minimum load
            available = {u: l for u, l in loads.items() if l < max_per_user}
            if not available:
                break
            
            user = min(available, key=available.get)
            task.assigned_to = user
            task.status = TaskStatus.ASSIGNED
            task.assigned_at = datetime.now().isoformat()
            loads[user] += 1
            assignments.append((task.id, user))
        
        return assignments
    
    def assign_random(self, users: List[str], count: int = None) -> List[Tuple[str, str]]:
        """Randomly assign tasks"""
        pending = self.queue.get_pending_tasks()
        if count:
            pending = pending[:count]
        
        assignments = []
        for task in pending:
            user = random.choice(users)
            task.assigned_to = user
            task.status = TaskStatus.ASSIGNED
            task.assigned_at = datetime.now().isoformat()
            assignments.append((task.id, user))
        
        return assignments
    
    def assign_task(self, task_id: str, user_id: str) -> bool:
        """Manually assign a specific task"""
        task = self.queue.get_task(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return False
        
        task.assigned_to = user_id
        task.status = TaskStatus.ASSIGNED
        task.assigned_at = datetime.now().isoformat()
        
        # Track assignment
        if user_id not in user_assignments:
            user_assignments[user_id] = []
        user_assignments[user_id].append(task_id)
        
        return True

# ====================================================================
# INTER-ANNOTATOR AGREEMENT (Cohen's Kappa)
# ====================================================================

class AgreementCalculator:
    """Calculate inter-annotator agreement metrics"""
    
    @staticmethod
    def cohens_kappa(annotations1: List[str], annotations2: List[str]) -> float:
        """
        Calculate Cohen's Kappa for two annotators
        κ = (P_o - P_e) / (1 - P_e)
        """
        if len(annotations1) != len(annotations2) or len(annotations1) == 0:
            return 0.0
        
        # Get unique labels
        labels = list(set(annotations1 + annotations2))
        n = len(labels)
        
        # Build confusion matrix
        confusion = {l1: {l2: 0 for l2 in labels} for l1 in labels}
        for a1, a2 in zip(annotations1, annotations2):
            confusion[a1][a2] += 1
        
        total = len(annotations1)
        
        # Observed agreement (P_o)
        p_o = sum(confusion[l][l] for l in labels) / total
        
        # Expected agreement (P_e)
        p_e = 0
        for label in labels:
            # Proportion of times each annotator used this label
            p1 = sum(confusion[label].values()) / total
            p2 = sum(confusion[l][label] for l in labels) / total
            p_e += p1 * p2
        
        # Kappa
        if p_e == 1:
            return 1.0
        
        kappa = (p_o - p_e) / (1 - p_e)
        return round(kappa, 4)
    
    @staticmethod
    def fleiss_kappa(annotations_matrix: List[List[str]]) -> float:
        """
        Calculate Fleiss' Kappa for multiple annotators
        Each row = one item, each column = one annotator's label
        """
        if not annotations_matrix or not annotations_matrix[0]:
            return 0.0
        
        n_items = len(annotations_matrix)
        n_raters = len(annotations_matrix[0])
        
        # Get all labels
        all_labels = set()
        for row in annotations_matrix:
            all_labels.update(row)
        labels = list(all_labels)
        
        # Count matrix: how many raters assigned each label to each item
        counts = []
        for row in annotations_matrix:
            label_counts = Counter(row)
            counts.append([label_counts.get(l, 0) for l in labels])
        
        # P_i for each item
        P_i = []
        for row_counts in counts:
            sum_squares = sum(c * c for c in row_counts)
            p = (sum_squares - n_raters) / (n_raters * (n_raters - 1))
            P_i.append(p)
        
        P_bar = np.mean(P_i)
        
        # p_j for each label
        total_ratings = n_items * n_raters
        p_j = [sum(counts[i][j] for i in range(n_items)) / total_ratings for j in range(len(labels))]
        
        P_e = sum(p * p for p in p_j)
        
        if P_e == 1:
            return 1.0
        
        kappa = (P_bar - P_e) / (1 - P_e)
        return round(kappa, 4)

# ====================================================================
# FASTAPI APP
# ====================================================================

app = FastAPI(
    title="Annotation Service",
    description="Tâche 7 - Human Validation Workflow",
    version="2.0.0"
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
def root():
    return {
        "service": "Annotation Service",
        "version": "2.0.0",
        "status": "running",
        "total_tasks": len(tasks_store)
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/tasks/pending")
def get_pending_tasks():
    """Get pending tasks count for dashboard"""
    pending = [t for t in tasks_store.values() if t.status == TaskStatus.PENDING]
    return {
        "pending_count": len(pending),
        "tasks": [{"id": t.id, "type": t.annotation_type.value, "priority": t.priority.value} for t in pending[:10]]
    }

# ====================================================================
# TASK MANAGEMENT ENDPOINTS
# ====================================================================

@app.post("/tasks")
def create_tasks(request: CreateTaskRequest):
    """Create annotation tasks for a dataset"""
    if request.dataset_id not in datasets_store:
        # Create sample tasks anyway for demo
        pass
    
    df = datasets_store.get(request.dataset_id, {}).get("df")
    
    if df is not None:
        if not request.row_indices:
            request.row_indices = list(range(len(df)))
    elif not request.row_indices:
        # Demo mode: create sample tasks
        request.row_indices = [0, 1, 2]
    
    created_tasks = []
    for idx in request.row_indices:
        if df is not None:
            data_sample = df.iloc[idx].to_dict()
        else:
            data_sample = {"sample_field": f"value_{idx}"}
        
        task = task_queue.create_task(
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
def list_tasks(
    status: Optional[str] = None,
    user_id: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    """List tasks with optional filters"""
    tasks = list(tasks_store.values())
    
    if status:
        tasks = [t for t in tasks if t.status.value == status]
    if user_id:
        tasks = [t for t in tasks if t.assigned_to == user_id]
    if priority:
        tasks = [t for t in tasks if t.priority.value == priority]
    
    # Sort by priority and creation time
    tasks = sorted(tasks, key=lambda x: (
        {"critical": 0, "high": 1, "medium": 2, "low": 3}[x.priority.value],
        x.created_at
    ))
    
    return {
        "total": len(tasks),
        "tasks": [t.dict() for t in tasks[:limit]]
    }

@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    """Get specific task details"""
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task.dict()

@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    """Delete a task"""
    if task_id not in tasks_store:
        raise HTTPException(404, "Task not found")
    del tasks_store[task_id]
    return {"status": "deleted"}

# ====================================================================
# ASSIGNMENT ENDPOINTS
# ====================================================================

@app.post("/assign")
def assign_tasks(config: AssignmentConfig):
    """Assign pending tasks to users"""
    if not config.users:
        raise HTTPException(400, "No users provided")
    
    if config.strategy == "round_robin":
        assignments = assignment_manager.assign_round_robin(config.users)
    elif config.strategy == "load_based":
        assignments = assignment_manager.assign_load_based(
            config.users, 
            config.max_tasks_per_user
        )
    elif config.strategy == "random":
        assignments = assignment_manager.assign_random(config.users)
    else:
        raise HTTPException(400, f"Unknown strategy: {config.strategy}")
    
    return {
        "assignments": [{"task_id": t, "user_id": u} for t, u in assignments],
        "total_assigned": len(assignments)
    }

@app.post("/assign/{task_id}")
def assign_single_task(task_id: str, user_id: str):
    """Manually assign a task to a user"""
    if assignment_manager.assign_task(task_id, user_id):
        return {"status": "assigned", "task_id": task_id, "user_id": user_id}
    raise HTTPException(400, "Task not available for assignment")

@app.post("/tasks/{task_id}/start")
def start_task(task_id: str, user_id: str):
    """Mark task as in progress"""
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    
    if task.assigned_to != user_id:
        raise HTTPException(403, "Task not assigned to this user")
    
    task.status = TaskStatus.IN_PROGRESS
    return {"status": "started"}

# ====================================================================
# VALIDATION ENDPOINTS
# ====================================================================

@app.post("/tasks/{task_id}/submit")
def submit_annotation(task_id: str, request: SubmitAnnotationRequest):
    """Submit annotations for a task"""
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    
    task.annotations = request.annotations
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now().isoformat()
    task.time_spent_seconds = request.time_spent_seconds
    
    # Add to history
    annotation_history.append({
        "task_id": task_id,
        "user_id": task.assigned_to,
        "annotations": [a.dict() for a in request.annotations],
        "completed_at": task.completed_at,
        "time_spent": request.time_spent_seconds
    })
    
    return {"status": "submitted", "task_id": task_id}

@app.post("/tasks/{task_id}/review")
def request_review(task_id: str):
    """Send task for supervisor review"""
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    
    task.status = TaskStatus.REVIEW
    return {"status": "sent_for_review"}

@app.post("/tasks/{task_id}/approve")
def approve_task(task_id: str):
    """Approve task annotations (supervisor)"""
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    
    task.status = TaskStatus.COMPLETED
    return {"status": "approved"}

@app.post("/tasks/{task_id}/reject")
def reject_task(task_id: str, reason: str = ""):
    """Reject task annotations (supervisor)"""
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    
    task.status = TaskStatus.REJECTED
    # Reset for re-annotation
    task.annotations = []
    return {"status": "rejected", "reason": reason}

# ====================================================================
# METRICS ENDPOINTS
# ====================================================================

@app.get("/metrics")
def get_metrics():
    """Get annotation metrics"""
    tasks = list(tasks_store.values())
    
    status_counts = Counter(t.status.value for t in tasks)
    
    # Time metrics
    completed = [t for t in tasks if t.time_spent_seconds]
    avg_time = np.mean([t.time_spent_seconds for t in completed]) if completed else 0
    
    # Tasks per annotator
    tasks_per_user = Counter(t.assigned_to for t in tasks if t.assigned_to)
    
    return AnnotationMetrics(
        total_tasks=len(tasks),
        pending=status_counts.get("pending", 0),
        in_progress=status_counts.get("in_progress", 0) + status_counts.get("assigned", 0),
        completed=status_counts.get("completed", 0),
        avg_time_seconds=round(avg_time, 2),
        tasks_per_annotator=dict(tasks_per_user)
    ).dict()

@app.post("/metrics/kappa")
def calculate_agreement(user1: str, user2: str, task_type: str = None):
    """Calculate Cohen's Kappa between two annotators"""
    # Get completed tasks from both users
    tasks1 = [t for t in tasks_store.values() 
              if t.assigned_to == user1 and t.status == TaskStatus.COMPLETED]
    tasks2 = [t for t in tasks_store.values() 
              if t.assigned_to == user2 and t.status == TaskStatus.COMPLETED]
    
    if not tasks1 or not tasks2:
        return {"kappa": None, "message": "Not enough completed tasks"}
    
    # Find common items (same dataset_id and row_index)
    common_labels1 = []
    common_labels2 = []
    
    for t1 in tasks1:
        for t2 in tasks2:
            if t1.dataset_id == t2.dataset_id and t1.row_index == t2.row_index:
                # Get labels from annotations
                label1 = t1.annotations[0].label if t1.annotations else "unlabeled"
                label2 = t2.annotations[0].label if t2.annotations else "unlabeled"
                common_labels1.append(label1)
                common_labels2.append(label2)
    
    if not common_labels1:
        return {"kappa": None, "message": "No common items annotated by both users"}
    
    kappa = AgreementCalculator.cohens_kappa(common_labels1, common_labels2)
    
    # Interpretation
    if kappa < 0:
        interpretation = "Poor (worse than chance)"
    elif kappa < 0.20:
        interpretation = "Slight"
    elif kappa < 0.40:
        interpretation = "Fair"
    elif kappa < 0.60:
        interpretation = "Moderate"
    elif kappa < 0.80:
        interpretation = "Substantial"
    else:
        interpretation = "Almost Perfect"
    
    return {
        "kappa": kappa,
        "interpretation": interpretation,
        "common_items": len(common_labels1)
    }

@app.get("/history")
def get_history(user_id: Optional[str] = None, limit: int = 100):
    """Get annotation history"""
    history = annotation_history
    if user_id:
        history = [h for h in history if h.get("user_id") == user_id]
    return {"history": history[-limit:], "total": len(history)}

# ====================================================================
# USER ENDPOINTS
# ====================================================================

@app.get("/users/{user_id}/tasks")
def get_user_tasks(user_id: str, status: Optional[str] = None):
    """Get tasks for a specific user"""
    tasks = task_queue.get_user_tasks(user_id)
    if status:
        tasks = [t for t in tasks if t.status.value == status]
    
    return {
        "user_id": user_id,
        "total": len(tasks),
        "tasks": [t.dict() for t in tasks]
    }

@app.get("/users/{user_id}/stats")
def get_user_stats(user_id: str):
    """Get statistics for a user"""
    tasks = task_queue.get_user_tasks(user_id)
    completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
    
    return {
        "user_id": user_id,
        "total_assigned": len(tasks),
        "completed": len(completed),
        "pending": len([t for t in tasks if t.status == TaskStatus.PENDING]),
        "in_progress": len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS]),
        "avg_time_seconds": np.mean([t.time_spent_seconds for t in completed if t.time_spent_seconds]) if completed else 0
    }

# ====================================================================
# MAIN
# ====================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📝 ANNOTATION SERVICE - Tâche 7")
    print("="*60)
    uvicorn.run("main:app", host="0.0.0.0", port=8007, reload=True)
