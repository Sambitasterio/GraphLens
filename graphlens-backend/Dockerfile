# GraphLens FastAPI backend image.
FROM python:3.11-slim

# tesseract is required by pytesseract (OCR fallback for scanned PDFs).
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# Cache pip downloads across builds (BuildKit) so requirements tweaks don't
# re-download the whole GraphRAG tree. Generous timeout/retries for big wheels.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --timeout 300 --retries 10 -r requirements.txt

COPY . .

# Run DB migrations on startup, then serve.
RUN chmod +x entrypoint.sh

EXPOSE 8000
CMD ["./entrypoint.sh"]
