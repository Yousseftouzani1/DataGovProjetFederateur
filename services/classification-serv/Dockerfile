FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# CRITICAL OPTIMIZATION: Install CPU-only PyTorch first.
# This prevents downloading 4GB+ of Nvidia CUDA drivers.
RUN pip install --no-cache-dir torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu

# Install the rest of the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -m nltk.downloader punkt stopwords

COPY . .

# Pre-train the baseline statistical model
# (Ensure this script saves the model to a path that persists, e.g., inside /app)
RUN python backend/models/train_baseline.py

EXPOSE 8005

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]