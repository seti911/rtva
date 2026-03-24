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
ENV PARAKEET_MODEL_PATH=/models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8

EXPOSE 8001

# Uses official Parakeet-TDT v3 model from sherpa-onnx
# Supports 25 European languages including French
# Model should be mounted at /models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8/

CMD ["python", "/app/stt_service/service.py"]
