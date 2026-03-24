FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN python3.11 -m venv /opt/venv

RUN /opt/venv/bin/pip install --no-cache-dir \
    websockets \
    numpy \
    llama-cpp-python \
    --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121

RUN update-alternatives --install /usr/bin/python3 python3 /opt/venv/bin/python3.11 1

WORKDIR /app

COPY src/llm_service /app/llm_service
COPY src/shared /app/shared

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV MODEL_PATH=/models/croissant/CroissantLLMChat-v0.1-Q3_K_M.gguf

EXPOSE 8002

CMD ["/opt/venv/bin/python", "/app/llm_service/service.py"]
