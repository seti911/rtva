FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# Audio bridge is a placeholder - connect via WebSocket from host
# For production, implement audio capture/playback

WORKDIR /app

COPY src/audio-bridge /app

EXPOSE 8004

# Placeholder - audio bridge will be implemented later
CMD ["tail", "-f", "/dev/null"]
