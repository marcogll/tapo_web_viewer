#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: falta Python 3."
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ERROR: falta FFmpeg."
  echo "macOS: brew install ffmpeg"
  echo "Debian/Ubuntu: sudo apt install ffmpeg"
  echo "Arch: sudo pacman -S ffmpeg"
  exit 1
fi

python3 server.py
