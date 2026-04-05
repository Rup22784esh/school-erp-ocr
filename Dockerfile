FROM python:3.10-slim

# Install system dependencies + OpenCV requirements
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-nep \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# SMART MOVE: Download the 'Best' Math model (not included in standard apt-get)
# Note: Path might vary slightly depending on Tesseract version, usually /usr/share/tesseract-ocr/4.00/tessdata or /usr/share/tesseract-ocr/5/tessdata
RUN mkdir -p /usr/share/tesseract-ocr/5/tessdata/ && \
    wget -P /usr/share/tesseract-ocr/5/tessdata/ https://github.com/tesseract-ocr/tessdata_best/raw/main/equ.traineddata || \
    wget -P /usr/share/tesseract-ocr/4.00/tessdata/ https://github.com/tesseract-ocr/tessdata_best/raw/main/equ.traineddata

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
