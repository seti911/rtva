FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV COQUI_TOS_AGREED=1

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN python3.11 -m venv /opt/venv

RUN /opt/venv/bin/pip install --no-cache-dir \
    websockets \
    numpy \
    torch==2.4.0 \
    torchaudio==2.4.0 \
    transformers==4.36.0 \
    TTS

RUN update-alternatives --install /usr/bin/python3 python3 /opt/venv/bin/python3.11 1

WORKDIR /app

COPY src/tts_service /app/tts_service
COPY src/shared /app/shared

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app

EXPOSE 8003

CMD ["/opt/venv/bin/python", "/app/tts_service/service.py"]