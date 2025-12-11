FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Install spaCy model for French if needed
# RUN python -m spacy download fr_core_news_sm

CMD ["python", "main.py"]
