FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    libasound2-dev \
    libportaudio2 \
    curl \
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

CMD ["python", "/app/stt_service/service.py"]
