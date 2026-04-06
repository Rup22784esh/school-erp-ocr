FROM python:3.9-slim

# libgomp1 को जोड़ा गया है ताकि PaddleOCR का एरर खत्म हो सके
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# यूजर सेटअप
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# फाइलें कॉपी और इंस्टॉल करना
COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=user . /app

# पोर्ट 7860
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
