FROM python:3.9-slim

# Install system dependencies for OpenCV, Paddle, and common utils
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Pre-download PaddleOCR models (English & Devanagari/Hindi for Nepalese support)
# lang='hi' supports Devanagari script used in Nepali
RUN python3 -c "from paddleocr import PaddleOCR; PaddleOCR(use_angle_cls=True, lang='hi', use_gpu=False)"

# Hugging Face Spaces use port 7860 by default
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
