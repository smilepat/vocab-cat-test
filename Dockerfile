FROM python:3.13-slim

WORKDIR /app

# Copy data files
COPY 9000word_full_db.csv ./
COPY vocabulary_graph.json ./

# Copy backend package
COPY irt_cat_engine/ ./irt_cat_engine/

# Install dependencies
RUN pip install --no-cache-dir -r irt_cat_engine/requirements.txt

# Cloud Run provides PORT env var (default 8080)
ENV PORT=8080

CMD ["sh", "-c", "uvicorn irt_cat_engine.api.main:app --host 0.0.0.0 --port $PORT"]
