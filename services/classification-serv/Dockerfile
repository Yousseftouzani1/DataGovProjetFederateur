FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Arabic reshaper
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data for lightweight NLP
RUN python -m nltk.downloader punkt stopwords

COPY . .

# Pre-train the baseline statistical model
RUN python backend/models/train_baseline.py

EXPOSE 8005

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
