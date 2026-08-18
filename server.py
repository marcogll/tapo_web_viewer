#!/usr/bin/env python3
import http.server
import json
import os
import signal
import socketserver
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser
from pathlib import Path

BASE = Path(__file__).resolve().parent
CONFIG_DIR = BASE / "config"
CONFIG_FILE = CONFIG_DIR / "cameras.json"
HLS_ROOT = BASE / "hls"
PORT = 8765
processes = []

CONFIG_DIR.mkdir(exist_ok=True)
HLS_ROOT.mkdir(exist_ok=True)

def prompt(text, default=None, secret=False):
    suffix = f" [{default}]" if default else ""
    if secret:
        import getpass
        value = getpass.getpass(f"{text}{suffix}: ").strip()
    else:
        value = input(f"{text}{suffix}: ").strip()
    return value or (default or "")

def first_run_setup():
    print("\n=== Configuración inicial RTSP Viewer ===\n")
    cams = []
    while True:
        name = prompt("Nombre de la cámara", f"Camara {len(cams)+1}")
        ip = prompt("IP de la cámara")
        user = prompt("Usuario RTSP")
        password = prompt("Contraseña RTSP", secret=True)
        port = prompt("Puerto RTSP", "554")
        stream = prompt("Ruta del stream", "/stream1")
        if not stream.startswith("/"):
            stream = "/" + stream
        cams.append({
            "name": name,
            "ip": ip,
            "user": user,
            "password": password,
            "port": int(port),
            "stream": stream
        })
        if len(cams) >= 4:
            break
        more = prompt("¿Agregar otra cámara? (s/n)", "n").lower()
        if more not in ("s","si","sí","y","yes"):
            break

    config = {
        "port": PORT,
        "cameras": cams,
        "site1": {"layout": "2x2", "cameras": list(range(min(4, len(cams))))},
        "site2": {"layout": "1x1", "cameras": [0] if cams else []}
    }
    CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except Exception:
        pass
    print(f"\nConfiguración guardada en: {CONFIG_FILE}\n")

def load_config():
    if not CONFIG_FILE.exists():
        first_run_setup()
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))

def camera_url(cam):
    user = urllib.parse.quote(cam["user"], safe="")
    password = urllib.parse.quote(cam["password"], safe="")
    host = cam["ip"]
    port = cam.get("port", 554)
    stream = cam.get("stream", "/stream1")
    return f"rtsp://{user}:{password}@{host}:{port}{stream}"

def clean_hls():
    for item in HLS_ROOT.iterdir():
        if item.is_dir():
            for f in item.iterdir():
                try: f.unlink()
                except OSError: pass

def spawn_ffmpeg(idx, cam, transport):
    outdir = HLS_ROOT / f"cam{idx}"
    outdir.mkdir(exist_ok=True)
    for f in outdir.glob("*"):
        try:
            f.unlink()
        except OSError:
            pass

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "warning",
        "-fflags", "+genpts+discardcorrupt",
        "-use_wallclock_as_timestamps", "1",
        "-rtsp_transport", transport,
        "-i", camera_url(cam),
        "-map", "0:v:0",
        "-an",
        "-c:v", "copy",
        "-avoid_negative_ts", "make_zero",
        "-muxdelay", "0",
        "-f", "hls",
        "-hls_time", "1",
        "-hls_list_size", "3",
        "-hls_flags", "delete_segments+append_list+omit_endlist+independent_segments",
        str(outdir / "stream.m3u8")
    ]
    return subprocess.Popen(cmd, cwd=BASE)

def start_one_camera(idx, cam):
    name = cam.get("name", f"Camara {idx+1}")
    for transport in ("tcp", "udp"):
        print(f"[{name}] intentando RTSP por {transport.upper()}...")
        try:
            proc = spawn_ffmpeg(idx, cam, transport)
        except FileNotFoundError:
            print("ERROR: ffmpeg no está instalado o no está en PATH.")
            sys.exit(1)

        # Give FFmpeg time to either create the HLS playlist or fail.
        playlist = HLS_ROOT / f"cam{idx}" / "stream.m3u8"
        for _ in range(20):
            if playlist.exists():
                processes.append(proc)
                print(f"[{name}] conectado por {transport.upper()}.")
                return
            if proc.poll() is not None:
                break
            time.sleep(0.15)

        if proc.poll() is None and playlist.exists():
            processes.append(proc)
            print(f"[{name}] conectado por {transport.upper()}.")
            return

        try:
            proc.terminate()
        except Exception:
            pass
        time.sleep(0.2)

    print(f"[{name}] ERROR: no se pudo abrir el stream por TCP ni UDP.")

def start_ffmpeg(config):
    for idx, cam in enumerate(config.get("cameras", [])):
        start_one_camera(idx, cam)

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/api/config":
            cfg = load_config()
            safe = {
                "cameras": [{"name": c["name"]} for c in cfg.get("cameras", [])],
                "site1": cfg.get("site1", {}),
                "site2": cfg.get("site2", {})
            }
            data = json.dumps(safe).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        return super().do_GET()

def stop_all(*_):
    try:
        httpd.shutdown()
    except Exception:
        pass
    for p in processes:
        try: p.terminate()
        except Exception: pass

config = load_config()
PORT = int(config.get("port", PORT))

os.chdir(BASE)

class ReusableTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

def bind_server(preferred_port):
    # Prefer the configured port, but automatically move upward if an old
    # instance or another app is still using it.
    for candidate in range(preferred_port, preferred_port + 20):
        try:
            return ReusableTCPServer(("127.0.0.1", candidate), Handler), candidate
        except OSError as e:
            if getattr(e, "errno", None) in (48, 98, 10048):
                continue
            raise
    raise OSError(f"No hay un puerto disponible entre {preferred_port} y {preferred_port + 19}")

httpd, PORT = bind_server(PORT)
start_ffmpeg(config)

signal.signal(signal.SIGINT, stop_all)
if hasattr(signal, "SIGTERM"):
    signal.signal(signal.SIGTERM, stop_all)

def open_pages():
    for _ in range(40):
        if any(HLS_ROOT.glob("cam*/stream.m3u8")):
            break
        time.sleep(.25)
    webbrowser.open(f"http://127.0.0.1:{PORT}/site1.html")
    time.sleep(.5)
    webbrowser.open(f"http://127.0.0.1:{PORT}/site2.html")

threading.Thread(target=open_pages, daemon=True).start()

print(f"Site 1: http://127.0.0.1:{PORT}/site1.html")
print(f"Site 2: http://127.0.0.1:{PORT}/site2.html")
print(f"Configurar de nuevo: python3 setup.py")
print("Ctrl+C para cerrar.")

try:
    httpd.serve_forever()
finally:
    stop_all()
    httpd.server_close()
