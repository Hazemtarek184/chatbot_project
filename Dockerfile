FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py ./
COPY config.py ./
COPY agents/ ./agents/
COPY handlers/ ./handlers/
COPY rag/ ./rag/
COPY data/ ./data/

RUN ls -l /app/data || echo "No data directory found"

CMD ["python", "main.py"] 