FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py ./
COPY config.py ./
COPY agents/ ./agents/
COPY handlers/ ./handlers/
COPY rag/ ./rag/

CMD ["python", "main.py"] 