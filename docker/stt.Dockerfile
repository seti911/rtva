FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    libasound2-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python3.11 -m venv /opt/venv

RUN /opt/venv/bin/pip install --no-cache-dir \
    "sherpa-onnx==1.8.11" \
    websockets \
    numpy \
    soundfile

RUN update-alternatives --install /usr/bin/python3 python3 /opt/venv/bin/python3.11 1

WORKDIR /app

COPY src/stt_service /app/stt_service
COPY src/shared /app/shared

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV PARAKEET_MODEL_PATH=/models/parakeet

EXPOSE 8001

CMD ["/opt/venv/bin/python", "/app/stt_service/service.py"]