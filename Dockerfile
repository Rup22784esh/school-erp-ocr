FROM python:3.10-slim

# Step 1: Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Step 2: Manually download High-Quality (LSTM) language data
WORKDIR /usr/share/tesseract-ocr/4.00/tessdata/

RUN wget https://github.com/tesseract-ocr/tessdata_fast/raw/main/eng.traineddata -O eng.traineddata && \
    wget https://github.com/tesseract-ocr/tessdata_fast/raw/main/nep.traineddata -O nep.traineddata && \
    wget https://github.com/tesseract-ocr/tessdata_fast/raw/main/osd.traineddata -O osd.traineddata

# Step 3: Set Environment Variables for Path and Memory
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata/
ENV MALLOC_TRIM_THRESHOLD_=100000
ENV PYTHONUNBUFFERED=1

# Step 4: App Setup
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Step 5: Start Service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
