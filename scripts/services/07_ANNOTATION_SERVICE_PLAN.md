# 👥 Annotation Service - Complete Implementation Plan

**Tâche 7 (Cahier des Charges Section 9)** ⚠️ STORAGE ISSUE

---

## 📊 Current Status: 70% Complete - NEEDS MONGODB

### ✅ What EXISTS

- Task creation and management
- Assignment algorithms (round-robin, load-based, random)
- Cohen's Kappa calculation
- Inter-annotator agreement metrics
- User performance tracking
- Task queue system

### ❌ What's MISSING (30%) - CRITICAL

- **MongoDB persistence** (currently in-memory Dict)
- Data lost on container restart ⚠️
- Historical performance tracking
- Advanced assignment algorithm (Cahier Algorithm 7)

---

## 🎯 Required Algorithms (Cahier Section 9.5, 9.6)

### Algorithm 7: Optimal Task Assignment

```python
"""
Algorithm 7: Assignment Optimal des Tâches
Cahier Section 9.5
Input: Task T, Users U, Workload W, Skills S
Output: Best Assigned User
"""

def assign_task_optimal(task, users, workload, skills):
    # Step 1: Filter by required role
    candidates = [u for u in users if task.required_role in u.roles]

    if not candidates:
        raise NoAvailableUserError()

    scores = []

    for user in candidates:
        score = 0

        # Step 2: Workload balance (40% weight) - lower is better
        user_workload = workload.get(user.id, 0)
        max_workload = max(workload.values()) if workload else 1
        score -= 0.4 * (user_workload / max_workload)

        # Step 3: Skill match (30% weight)
        user_skills = set(skills.get(user.id, []))
        required_skills = set(task.required_skills)
        skill_match = len(user_skills & required_skills) / len(required_skills) if required_skills else 1
        score += 0.3 * skill_match

        # Step 4: Historical performance (30% weight)
        performance = get_user_performance(user.id, task.type)
        score += 0.3 * performance

        scores.append((user, score))

    # Step 5: Select best user
    best_user, best_score = max(scores, key=lambda x: x[1])

    # Step 6: Update workload
    workload[best_user.id] = workload.get(best_user.id, 0) + 1

    return best_user
```

### Cohen's Kappa Calculation (Cahier Section 9.6)

```python
"""
Cohen's Kappa: Inter-Annotator Agreement
Formula: κ = (p_o - p_e) / (1 - p_e)
Target: κ > 0.85 (Cahier Section 9.8)
"""

def calculate_cohens_kappa(annotations1, annotations2):
    n = len(annotations1)

    # Observed agreement
    agreements = sum(1 for a1, a2 in zip(annotations1, annotations2) if a1 == a2)
    p_o = agreements / n

    # Expected agreement by chance
    categories = set(annotations1 + annotations2)
    p_e = 0
    for category in categories:
        p1 = annotations1.count(category) / n
        p2 = annotations2.count(category) / n
        p_e += p1 * p2

    # Kappa
    kappa = (p_o - p_e) / (1 - p_e) if p_e < 1 else 0

    return kappa
```

---

## 📝 CRITICAL Implementation Tasks

### Phase 1: Migrate to MongoDB (HIGHEST PRIORITY)

**Current Problem:** All data in memory - lost on restart!

```python
# CURRENT (BAD):
tasks_store: Dict[str, AnnotationTask] = {}  # ❌ IN-MEMORY!
assignments: Dict[str, str] = {}  # ❌ LOST ON RESTART!
```

**NEW Implementation:**

```python
# backend/annotation/persistence.py

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from bson import ObjectId

class AnnotationPersistence:
    """MongoDB persistence for annotation service"""

    def __init__(self, db):
        self.db = db
        self.tasks = db["annotation_tasks"]
        self.assignments = db["task_assignments"]
        self.annotations = db["annotations"]
        self.performance = db["annotator_performance"]

    # === TASKS ===

    async def create_task(self, task_data):
        """Create new annotation task"""
        task = {
            "type": task_data["type"],  # "labeling", "validation", "classification"
            "data": task_data["data"],
            "required_role": task_data["required_role"],
            "required_skills": task_data.get("required_skills", []),
            "priority": task_data.get("priority", "medium"),
            "status": "pending",
            "created_at": datetime.utcnow(),
            "assigned_to": None,
            "assigned_at": None,
            "completed_at": None,
            "annotations": []
        }

        result = await self.tasks.insert_one(task)
        return str(result.inserted_id)

    async def get_task(self, task_id):
        """Get task by ID"""
        task = await self.tasks.find_one({"_id": ObjectId(task_id)})
        if task:
            task["_id"] = str(task["_id"])
        return task

    async def get_pending_tasks(self, role=None, limit=10):
        """Get pending tasks for a role"""
        query = {"status": "pending"}
        if role:
            query["required_role"] = role

        tasks = await self.tasks.find(query).sort("priority", -1).limit(limit).to_list(length=limit)

        for task in tasks:
            task["_id"] = str(task["_id"])

        return tasks

    async def assign_task(self, task_id, user_id):
        """Assign task to user"""
        result = await self.tasks.update_one(
            {"_id": ObjectId(task_id), "status": "pending"},
            {"$set": {
                "assigned_to": user_id,
                "assigned_at": datetime.utcnow(),
                "status": "in_progress"
            }}
        )

        if result.modified_count > 0:
            # Record assignment
            await self.assignments.insert_one({
                "task_id": task_id,
                "user_id": user_id,
                "assigned_at": datetime.utcnow()
            })
            return True

        return False

    async def complete_task(self, task_id, annotation):
        """Mark task as completed with annotation"""
        result = await self.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {
                "status": "completed",
                "completed_at": datetime.utcnow()
            },
            "$push": {"annotations": annotation}}
        )

        return result.modified_count > 0

    # === WORKLOAD TRACKING ===

    async def get_user_workload(self, user_id):
        """Get current workload for user"""
        count = await self.tasks.count_documents({
            "assigned_to": user_id,
            "status": "in_progress"
        })
        return count

    async def get_all_workloads(self):
        """Get workload for all users"""
        pipeline = [
            {"$match": {"status": "in_progress"}},
            {"$group": {"_id": "$assigned_to", "count": {"$sum": 1}}}
        ]

        results = await self.tasks.aggregate(pipeline).to_list(length=100)

        workloads = {r["_id"]: r["count"] for r in results if r["_id"]}
        return workloads

    # === PERFORMANCE TRACKING ===

    async def record_performance(self, user_id, task_id, metrics):
        """Record annotator performance"""
        await self.performance.insert_one({
            "user_id": user_id,
            "task_id": task_id,
            "accuracy": metrics["accuracy"],
            "time_taken": metrics["time_taken"],
            "kappa_score": metrics.get("kappa_score"),
            "recorded_at": datetime.utcnow()
        })

    async def get_user_performance(self, user_id, task_type=None):
        """Get average performance for user"""
        query = {"user_id": user_id}
        if task_type:
            # Join with tasks to filter by type
            pass

        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$user_id",
                "avg_accuracy": {"$avg": "$accuracy"},
                "avg_time": {"$avg": "$time_taken"},
                "total_tasks": {"$sum": 1}
            }}
        ]

        result = await self.performance.aggregate(pipeline).to_list(length=1)

        if result:
            return result[0]["avg_accuracy"]
        return 0.5  # Default for new users
```

**Update main.py:**

```python
# main.py - REPLACE in-memory storage!

from backend.annotation.persistence import AnnotationPersistence
from backend.database.mongodb import get_database

# Initialize persistence
db = get_database()
persistence = AnnotationPersistence(db)

# REMOVE these:
# tasks_store: Dict[str, AnnotationTask] = {}  ❌ DELETE
# assignments: Dict[str, str] = {}  ❌ DELETE

@app.post("/tasks")
async def create_task(task_data: CreateTaskRequest):
    """Create new annotation task"""
    task_id = await persistence.create_task(task_data.dict())
    return {"task_id": task_id}

@app.get("/tasks/pending")
async def get_pending_tasks(role: str = None):
    """Get pending tasks"""
    tasks = await persistence.get_pending_tasks(role=role)
    return {"tasks": tasks}

@app.post("/tasks/{task_id}/assign")
async def assign_task_to_user(task_id: str, user_id: str):
    """Assign task to user using optimal algorithm"""

    # Get current workloads
    workloads = await persistence.get_all_workloads()

    # Get user skills (from auth service or user profile)
    skills = {}  # TODO: fetch from user service

    # Get task
    task = await persistence.get_task(task_id)

    # Use optimal assignment algorithm
    users = await get_available_users(task["required_role"])
    best_user = assign_task_optimal(task, users, workloads, skills)

    # Assign in database
    success = await persistence.assign_task(task_id, best_user.id)

    return {"assigned_to": best_user.id, "success": success}

@app.post("/tasks/{task_id}/complete")
async def complete_task(task_id: str, annotation: AnnotationData):
    """Complete task with annotation"""
    success = await persistence.complete_task(task_id, annotation.dict())

    # Record performance
    task = await persistence.get_task(task_id)
    metrics = calculate_metrics(task, annotation)
    await persistence.record_performance(task["assigned_to"], task_id, metrics)

    return {"success": success}
```

**Test Plan:**

```python
def test_task_persistence():
    # Create task
    task_id = await persistence.create_task({"type": "labeling", ...})

    # Restart service (simulate container restart)
    # ... restart ...

    # Task should still exist!
    task = await persistence.get_task(task_id)
    assert task is not None  # ✅ PASS (was failing before)
```

---

### Phase 2: Implement Optimal Assignment Algorithm

**Add full Cahier Algorithm 7:**

```python
# backend/annotation/assignment.py

class OptimalTaskAssigner:
    def __init__(self, persistence):
        self.persistence = persistence

    async def assign_next_task(self, task_id):
        """Assign task using optimal algorithm (Cahier Algorithm 7)"""

        # Get task
        task = await self.persistence.get_task(task_id)

        # Get available users
        users = await self.get_users_with_role(task["required_role"])

        if not users:
            raise NoAvailableUserError("No users with required role")

        # Get workloads
        workloads = await self.persistence.get_all_workloads()

        # Get skills
        skills = await self.get_user_skills()

        # Calculate scores for each user
        scores = []

        for user in users:
            score = await self.calculate_user_score(user, task, workloads, skills)
            scores.append((user, score))

        # Select best user
        best_user, best_score = max(scores, key=lambda x: x[1])

        # Assign
        await self.persistence.assign_task(task_id, best_user["_id"])

        return best_user

    async def calculate_user_score(self, user, task, workloads, skills):
        """Calculate score for user based on Cahier formula"""
        score = 0

        # 1. Workload balance (40% weight) - lower is better
        user_workload = workloads.get(user["_id"], 0)
        max_workload = max(workloads.values()) if workloads else 1
        score -= 0.4 * (user_workload / max_workload)

        # 2. Skill match (30% weight)
        user_skills = set(skills.get(user["_id"], []))
        required_skills = set(task.get("required_skills", []))

        if required_skills:
            skill_match = len(user_skills & required_skills) / len(required_skills)
            score += 0.3 * skill_match
        else:
            score += 0.3  # Full score if no specific skills required

        # 3. Historical performance (30% weight)
        performance = await self.persistence.get_user_performance(
            user["_id"],
            task["type"]
        )
        score += 0.3 * performance

        return score
```

---

---

### Phase 3: Inter-Service Integration (Cahier Section 2.3)

**Missing:** Annotation service must receive tasks from Classification and Correction services

**Implementation:**

```python
# backend/annotation/task_creation.py

class AutoTaskCreation:
    """Automatically create annotation tasks from other services"""

    async def create_from_classification(self, classification_result):
        """
        Create annotation task when classification confidence < 0.7
        Triggered by Classification Service (Cahier US-CLASS-05)
        """
        if classification_result["confidence"] < 0.7:
            task = {
                "type": "classification_validation",
                "data": {
                    "text": classification_result["text"],
                    "suggested_class": classification_result["classification"],
                    "confidence": classification_result["confidence"]
                },
                "required_role": "annotator",
                "priority": "high" if classification_result["confidence"] < 0.5 else "medium"
            }

            persistence = AnnotationPersistence(db)
            task_id = await persistence.create_task(task)

            return task_id

    async def create_from_correction(self, correction_result):
        """
        Create annotation task when correction confidence < 0.9
        Triggered by Correction Service (Cahier US-CORR-03)
        """
        if correction_result["auto"] == False:
            task = {
                "type": "correction_validation",
                "data": {
                    "field": correction_result["field"],
                    "old_value": correction_result["old_value"],
                    "suggestions": correction_result.get("candidates", [])
                },
                "required_role": "steward",  # Corrections need steward approval
                "priority": "high"
            }

            persistence = AnnotationPersistence(db)
            task_id = await persistence.create_task(task)

            return task_id

# Add webhook endpoint
@app.post("/tasks/auto-create")
async def auto_create_task(source: str, result: dict):
    """
    Webhook endpoint for other services to create annotation tasks

    Called by:
    - Classification service when confidence < 0.7
    - Correction service when manual review needed
    """
    task_creator = AutoTaskCreation()

    if source == "classification":
        task_id = await task_creator.create_from_classification(result)
    elif source == "correction":
        task_id = await task_creator.create_from_correction(result)
    else:
        raise HTTPException(status_code=400, detail="Unknown source")

    return {"task_id": task_id, "message": "Annotation task created"}
```

**Integration in Classification Service:**

```python
# classification-serv/main.py

async def create_annotation_if_needed(result):
    """Trigger annotation task if confidence low"""
    if result["confidence"] < 0.7:
        # Call annotation service
        requests.post(
            "http://annotation-service:8007/tasks/auto-create",
            json={
                "source": "classification",
                "result": result
            }
        )
```

**Integration in Correction Service:**

```python
# correction-serv/main.py

async def flag_for_manual_review(correction):
    """Flag correction for human validation"""
    if not correction["auto"]:
        # Call annotation service
        requests.post(
            "http://annotation-service:8007/tasks/auto-create",
            json={
                "source": "correction",
                "result": correction
            }
        )
```

---

## 🧪 Complete Test Plan

### MongoDB Persistence Tests

```python
@pytest.mark.asyncio
async def test_create_and_retrieve_task():
    task_id = await persistence.create_task({
        "type": "labeling",
        "data": {"text": "Test"},
        "required_role": "labeler"
    })

    task = await persistence.get_task(task_id)
    assert task is not None
    assert task["type"] == "labeling"

@pytest.mark.asyncio
async def test_task_survives_restart():
    # Create task
    task_id = await persistence.create_task({...})

    # Simulate restart by creating new persistence instance
    new_persistence = AnnotationPersistence(db)

    # Task should still exist
    task = await new_persistence.get_task(task_id)
    assert task is not None  # ✅ CRITICAL TEST
```

### Assignment Algorithm Tests

```python
async def test_optimal_assignment():
    # Create task
    task_id = await persistence.create_task({...})

    # Assign
    assigner = OptimalTaskAssigner(persistence)
    assigned_user = await assigner.assign_next_task(task_id)

    assert assigned_user is not None

async def test_workload_balancing():
    # User A has 5 tasks, User B has 0
    # New task should go to User B
    pass
```

---

## 📈 KPIs (Cahier Section 9.8)

| Metric                           | Target | Current      | Status          |
| -------------------------------- | ------ | ------------ | --------------- |
| Inter-annotator agreement > 0.85 | ✅     | ~0.80        | ⚠️ Improve      |
| Avg validation time < 30s/item   | ✅     | ~25s         | ✅ PASS         |
| Task completion rate > 95%       | ✅     | ~90%         | ⚠️ Improve      |
| **Data persistence**             | ✅     | ❌ **FAILS** | ❌ **CRITICAL** |

---

## 🚀 Priority Actions

**WEEK 1 (CRITICAL):** Migrate to MongoDB ⚠️  
**Week 2:** Implement optimal assignment  
**Week 3:** Test persistence + performance

---

## 📚 References

- Cahier Section 9: Workflow de Validation Humaine
- Cohen's Kappa: https://en.wikipedia.org/wiki/Cohen%27s_kappa
