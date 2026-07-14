FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (better Docker layer caching)
COPY Backend/requirements.txt Backend/requirements.txt
RUN pip install --no-cache-dir -r Backend/requirements.txt

# Copy backend code and dataset, preserving relative structure
COPY Backend Backend
COPY dataset dataset

WORKDIR /app/Backend

EXPOSE 7860

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]