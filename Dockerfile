FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

ENV RTSP_VIEWER_HOST=0.0.0.0
ENV RTSP_VIEWER_NONINTERACTIVE=1

EXPOSE 8765

CMD ["python", "server.py"]