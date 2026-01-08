# Correction Service V2 - Deployment Guide

## Prerequisites

### System Requirements
- **OS**: Linux, macOS, or Windows
- **Python**: 3.9 or higher
- **RAM**: Minimum 4GB (8GB recommended for T5 model)
- **Disk Space**: ~2GB (for dependencies and models)
- **MongoDB**: 4.4+ (optional, but recommended for full features)

### Network Requirements
- Port 8006 available (or configure different port)
- Internet access for first-time model download (~500MB)
- MongoDB connection (if using database features)

## Installation

### Step 1: Clone and Navigate
```bash
cd /path/to/DataGov/services/correction-serv
```

### Step 2: Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

This will install:
- FastAPI, Uvicorn (API framework)
- Motor (async MongoDB driver)
- Transformers, PyTorch (T5 model)
- Pandas, NumPy, scikit-learn (data processing)
- PyYAML (configuration)

**Note**: First run will download T5 model (~500MB). This is a one-time download.

### Step 4: Configure Environment

Create `.env` file in project root:
```env
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=datagov
PORT=8006
```

### Step 5: Verify MongoDB (Optional)

If using MongoDB features (validation, learning, reporting):
```bash
# Check MongoDB is running
mongosh --eval "db.version()"

# Create database
mongosh
> use datagov
> db.createCollection("correction_validations")
> db.createCollection("correction_training_data")
> db.createCollection("correction_kpi_history")
> exit
```

## Running the Service

### Development Mode
```bash
python main.py
```

Service will start at: `http://localhost:8006`

API docs available at: `http://localhost:8006/docs`

### Production Mode

#### Using Uvicorn
```bash
uvicorn main:app --host 0.0.0.0 --port 8006 --workers 4
```

#### Using Gunicorn (Linux/macOS)
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8006
```

#### Using Docker
```bash
# Build image
docker build -t correction-service-v2 .

# Run container
docker run -d \
  -p 8006:8006 \
  -e MONGODB_URI=mongodb://host.docker.internal:27017 \
  -e DATABASE_NAME=datagov \
  --name correction-service \
  correction-service-v2
```

## Verification

### Health Check
```bash
curl http://localhost:8006/health
```

Expected response:
```json
{
  "status": "healthy",
  "t5_model_loaded": true,
  "database_connected": true,
  "timestamp": "2026-01-07T..."
}
```

### Test Detection
```bash
curl -X POST http://localhost:8006/detect \
  -H "Content-Type: application/json" \
  -d '{"row": {"date_naissance": "32/13/2024", "age": 250}}'
```

Expected: Detects 2 inconsistencies (FORMAT + DOMAIN)

### Run Example
```bash
python example_usage.py
```

Should complete all 7 workflow steps successfully.

## Performance Tuning

### T5 Model Selection

**For Development/Testing** (faster startup):
```python
# In main.py, startup() function:
t5_corrector = TextCorrectionT5(model_name="t5-small")  # Default
```

**For Production** (better accuracy):
```python
t5_corrector = TextCorrectionT5(model_name="t5-base")
```

**For High Performance** (requires GPU):
```python
t5_corrector = TextCorrectionT5(
    model_name="t5-base",
    device="cuda"  # Requires NVIDIA GPU + CUDA
)
```

### Worker Configuration

Adjust workers based on your CPU cores:
```bash
# Workers = (2 x CPU cores) + 1
uvicorn main:app --workers 9  # For 4-core CPU
```

### Database Optimization

Create indexes for better query performance:
```javascript
// In MongoDB
db.correction_validations.createIndex({"dataset_id": 1, "timestamp": -1})
db.correction_validations.createIndex({"status": 1, "confidence": 1})
db.correction_training_data.createIndex({"timestamp": -1})
db.correction_kpi_history.createIndex({"dataset_id": 1, "timestamp": -1})
```

## Monitoring

### Logs

Service logs include:
- Startup messages (engines initialization)
- Request processing (detection, correction)
- ML model predictions
- Validation events
- Learning triggers
- Errors and warnings

**View logs**:
```bash
# If running directly
python main.py 2>&1 | tee correction-service.log

# If using systemd
journalctl -u correction-service -f
```

### Metrics

**KPI Dashboard**: `GET /kpi/dashboard`

Monitor:
- Health score (0-100)
- Detection rate (target > 95%)
- Auto-correction precision (target > 90%)
- Auto-correction rate (target > 70%)
- Processing time (target < 5s per 1000 rows)

**Set up monitoring alerts** for:
- Health score < 80
- Any KPI below target
- Processing time > 10s per 1000 rows
- Error rate > 5%

### Health Checks

**Liveness probe**: `GET /health`
- Returns 200 if service is running
- Checks T5 model and database connectivity

**Readiness probe**: `GET /`
- Returns service stats
- Confirms all engines initialized

## Scaling

### Horizontal Scaling

Run multiple instances behind a load balancer:

```nginx
# nginx.conf
upstream correction_service {
    server localhost:8006;
    server localhost:8007;
    server localhost:8008;
}

server {
    listen 80;
    location / {
        proxy_pass http://correction_service;
    }
}
```

Start multiple instances:
```bash
uvicorn main:app --port 8006 &
uvicorn main:app --port 8007 &
uvicorn main:app --port 8008 &
```

### Database Scaling

For high traffic:
1. **MongoDB Replica Set**: For read scaling
2. **Connection Pooling**: Adjust `maxPoolSize` in MongoDB connection
3. **Sharding**: Shard collections by `dataset_id`

## Backup & Recovery

### Backup MongoDB Data

```bash
# Backup all correction data
mongodump --db datagov --out /backup/datagov-$(date +%Y%m%d)

# Backup specific collections
mongodump --db datagov \
  --collection correction_validations \
  --collection correction_training_data \
  --out /backup/corrections-$(date +%Y%m%d)
```

### Backup Fine-Tuned Models

```bash
# Backup fine-tuned T5 models
tar -czf t5-models-backup-$(date +%Y%m%d).tar.gz ./models/t5_corrector_finetuned*
```

### Restore

```bash
# Restore MongoDB
mongorestore --db datagov /backup/datagov-20260107/datagov

# Restore models
tar -xzf t5-models-backup-20260107.tar.gz -C ./models/
```

## Troubleshooting

### T5 Model Won't Load

**Symptom**: `⚠️ Failed to load T5 model`

**Solutions**:
1. Check internet connection (first-time download)
2. Increase RAM (minimum 4GB)
3. Use smaller model: `t5-small` instead of `t5-base`
4. Clear HuggingFace cache: `rm -rf ~/.cache/huggingface/`

### MongoDB Connection Errors

**Symptom**: `⚠️ Mongo error: ...`

**Solutions**:
1. Verify MongoDB is running: `mongosh`
2. Check connection string in `.env`
3. Ensure network access to MongoDB
4. Service still works without MongoDB (limited features)

### Slow Processing (> 5s per 1000 rows)

**Solutions**:
1. Use GPU acceleration: `device="cuda"`
2. Reduce T5 model size: Use `t5-small`
3. Increase workers: `--workers 8`
4. Cache frequently used corrections
5. Batch process instead of row-by-row

### High Memory Usage

**Solutions**:
1. Use `t5-small` instead of `t5-base` (350MB vs 850MB)
2. Set batch size limits in T5 corrector
3. Limit concurrent requests with Uvicorn workers
4. Enable swap memory if needed

## Security

### API Security

1. **Add Authentication**:
```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/detect")
async def detect(request: DetectRequest, token: HTTPAuthorizationCredentials = Depends(security)):
    # Verify token
    ...
```

2. **Rate Limiting**:
```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/detect")
@limiter.limit("100/minute")
async def detect(...):
    ...
```

### Database Security

1. Enable MongoDB authentication
2. Use strong passwords
3. Enable TLS/SSL connections
4. Restrict network access

### Data Privacy

1. PII data in corrections is logged - ensure proper access controls
2. Consider encryption for sensitive fields
3. Implement data retention policies
4. Regular audit of validation logs

## Maintenance

### Regular Tasks

**Daily**:
- Monitor KPI dashboard
- Check error logs
- Verify service health

**Weekly**:
- Review pending validations
- Check learning statistics
- Backup MongoDB data

**Monthly**:
- Analyze learning trends
- Review KPI improvements
- Backup fine-tuned models
- Update correction rules if needed

### Updates

To update the service:
```bash
git pull
pip install -r requirements.txt --upgrade
python main.py  # Restart service
```

### Model Retraining

Automatic retraining triggers every 100 validations.

Manual retraining:
```bash
curl -X POST http://localhost:8006/learning/retrain \
  -H "Content-Type: application/json" \
  -d '{"num_epochs": 3, "force": true}'
```

**Note**: Retraining may take 5-30 minutes depending on training data size.

## Support

### Getting Help

1. **Documentation**: See README.md
2. **API Docs**: http://localhost:8006/docs
3. **Example Usage**: `python example_usage.py`
4. **Tests**: `pytest tests/`

### Reporting Issues

Include in bug reports:
1. Service version (from `GET /`)
2. Error logs
3. Sample request that failed
4. System specs (OS, Python version, RAM)

## Quick Reference

```bash
# Start service
python main.py

# Run with more workers
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8006

# Health check
curl http://localhost:8006/health

# View API docs
open http://localhost:8006/docs

# Run example
python example_usage.py

# Run tests
pytest tests/ -v

# Backup data
mongodump --db datagov --out /backup/correction-data

# Trigger retraining
curl -X POST http://localhost:8006/learning/retrain
```

---

**Version**: 2.0.0  
**Last Updated**: 2026-01-07
