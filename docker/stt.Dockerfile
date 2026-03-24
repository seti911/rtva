FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    libasound2-dev \
    libportaudio2 \
    curl \
    bzip2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY src/stt_service /app/stt_service
COPY src/shared /app/shared

RUN pip install --no-cache-dir \
    websockets \
    numpy \
    "sherpa-onnx>=1.9.0"

ENV PYTHONPATH=/app
ENV PARAKEET_MODEL_PATH=/models/parakeet

EXPOSE 8001

# Note: To enable real Parakeet-TDT streaming transcription:
# 1. Download official model from sherpa-onnx releases
# 2. Mount at /models/parakeet-online/
# 3. Update service to use OnlineRecognizer
# Currently using intelligent dummy mode for pipeline testing

CMD ["python", "/app/stt_service/service.py"]
