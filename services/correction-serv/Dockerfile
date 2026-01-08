# ===============================
# Data Governance - Correction Service
# ===============================

FROM python:3.11-slim

# -------------------------------
# Environment
# -------------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# -------------------------------
# Workdir
# -------------------------------
WORKDIR /app

# -------------------------------
# System dependencies (light)
# -------------------------------
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------
# Python dependencies
# -------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------
# Application code
# -------------------------------
COPY . .

# -------------------------------
# Expose FastAPI port
# -------------------------------
EXPOSE 8000

# -------------------------------
# Run service
# -------------------------------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
