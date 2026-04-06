FROM python:3.10-slim

# Install system dependencies + OpenCV requirements
# We only install English and Nepali language packs to keep it lightweight
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-nep \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
