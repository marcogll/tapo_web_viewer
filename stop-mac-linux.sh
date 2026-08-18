#!/usr/bin/env bash
set +e
pkill -f "rtsp-viewer-multicam.*server.py" 2>/dev/null
pkill -f "ffmpeg.*stream.m3u8" 2>/dev/null
echo "Procesos RTSP Viewer detenidos."
