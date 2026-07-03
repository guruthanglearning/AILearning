FROM python:3.12-slim

WORKDIR /app

COPY requirements.docker.txt .
RUN pip install --no-cache-dir -r requirements.docker.txt

# Pre-download FinBERT so pods never hit a cold-download OOM spike at analysis time
RUN python -c "from transformers import pipeline; pipeline('text-classification', model='ProsusAI/finbert', top_k=None, truncation=True, max_length=512)"

COPY . .

EXPOSE 8010
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8010"]
