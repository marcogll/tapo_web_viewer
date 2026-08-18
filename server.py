#!/usr/bin/env python3
import hashlib
import http.server
import json
import os
import secrets
import signal
import socket
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
sessions = set()

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

def hash_password(pw):
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def first_run_setup():
    print("\n=== Configuración inicial RTSP Viewer ===\n")
    print("No se encontró config/cameras.json.")
    print("Se crea una configuración vacía; configura las cámaras desde la página web.")
    default_config()

def default_config():
    config = {
        "port": PORT,
        "admin_password_hash": "",
        "global_user": "",
        "global_password": "",
        "cameras": [],
        "site1": {"layout": "1x1", "cameras": []},
        "site2": {"layout": "1x1", "cameras": []}
    }
    CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except Exception:
        pass
    print(f"\nConfiguración vacía creada en: {CONFIG_FILE}")
    print("Abre la página de configuración para agregar cámaras.\n")

def load_config():
    if not CONFIG_FILE.exists():
        first_run_setup()
    cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    cfg.setdefault("admin_password_hash", "")
    cfg.setdefault("global_user", "")
    cfg.setdefault("global_password", "")
    return cfg

def camera_url(cam, cfg):
    user = cam.get("user") or cfg.get("global_user", "")
    password = cam.get("password") or cfg.get("global_password", "")
    user = urllib.parse.quote(user, safe="")
    password = urllib.parse.quote(password, safe="")
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
        "-i", camera_url(cam, config),
        "-map", "0:v:0",
        "-an",
    ]
    if cam.get("encode", config.get("encode", True)):
        cmd += [
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-tune", "zerolatency",
            "-crf", "26",
            "-g", "30",
            "-sc_threshold", "0",
        ]
    else:
        cmd += ["-c:v", "copy"]
    cmd += [
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

    def _send_json(self, code, obj):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _is_authed(self):
        cfg = load_config()
        if not cfg.get("admin_password_hash"):
            return True
        token = self.headers.get("X-Auth-Token", "")
        return token in sessions

    def do_GET(self):
        if self.path in ("/sitio1.html", "/sitio2.html"):
            self.send_response(301)
            self.send_header("Location", self.path.replace("sitio", "site"))
            self.end_headers()
            return
        if self.path == "/api/config":
            cfg = load_config()
            safe = {
                "cameras": [{"name": c["name"]} for c in cfg.get("cameras", [])],
                "site1": cfg.get("site1", {}),
                "site2": cfg.get("site2", {}),
                "port": cfg.get("port", PORT)
            }
            self._send_json(200, safe)
            return
        if self.path == "/api/config/full":
            if not self._is_authed():
                self._send_json(401, {"error": "No autorizado"})
                return
            cfg = load_config()
            cfg.pop("admin_password_hash", None)
            self._send_json(200, cfg)
            return
        if self.path == "/api/auth/check":
            cfg = load_config()
            self._send_json(200, {
                "authed": self._is_authed(),
                "has_password": bool(cfg.get("admin_password_hash"))
            })
            return
        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/login":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                cfg = load_config()
                if hash_password(body.get("password", "")) == cfg.get("admin_password_hash", ""):
                    token = secrets.token_hex(16)
                    sessions.add(token)
                    self._send_json(200, {"token": token})
                else:
                    self._send_json(401, {"error": "Password incorrecto"})
            except Exception:
                self._send_json(500, {"error": "Error de login"})
            return
        if self.path == "/api/config":
            if not self._is_authed():
                self._send_json(401, {"error": "No autorizado"})
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                new_cfg = json.loads(body.decode("utf-8"))
                old_cfg = load_config()
                new_cfg["admin_password_hash"] = old_cfg.get("admin_password_hash", "")
                if new_cfg.get("new_password"):
                    new_cfg["admin_password_hash"] = hash_password(new_cfg.pop("new_password"))
                CONFIG_FILE.write_text(json.dumps(new_cfg, ensure_ascii=False, indent=2), encoding="utf-8")
                try:
                    os.chmod(CONFIG_FILE, 0o600)
                except Exception:
                    pass
                self._send_json(200, {"ok": True})
            except Exception:
                self._send_json(500, {"error": "Error al guardar"})
            return
        return super().do_POST()

def stop_all(*_):
    try:
        httpd.shutdown()
    except Exception:
        pass
    for p in processes:
        try: p.terminate()
        except Exception: pass

config = load_config()
PORT = int(os.environ.get("RTSP_VIEWER_PORT", config.get("port", PORT)))
HOST = os.environ.get("RTSP_VIEWER_HOST", "127.0.0.1")
NONINTERACTIVE = os.environ.get("RTSP_VIEWER_NONINTERACTIVE") == "1"

os.chdir(BASE)

class ReusableTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

def bind_server(host, preferred_port):
    # Prefer the configured port, but automatically move upward if an old
    # instance or another app is still using it.
    for candidate in range(preferred_port, preferred_port + 20):
        try:
            return ReusableTCPServer((host, candidate), Handler), candidate
        except OSError as e:
            if getattr(e, "errno", None) in (48, 98, 10048):
                continue
            raise
    raise OSError(f"No hay un puerto disponible entre {preferred_port} and {preferred_port + 19}")

httpd, PORT = bind_server(HOST, PORT)
start_ffmpeg(config)

signal.signal(signal.SIGINT, stop_all)
if hasattr(signal, "SIGTERM"):
    signal.signal(signal.SIGTERM, stop_all)

def local_ips():
    ips = []
    try:
        for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
            if not ip.startswith("127."):
                ips.append(ip)
    except Exception:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.append(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    return list(dict.fromkeys(ips))

def open_pages():
    needs_setup = not config.get("cameras") or not config.get("admin_password_hash")
    if needs_setup:
        webbrowser.open(f"http://127.0.0.1:{PORT}/config.html")
        return
    for _ in range(40):
        if any(HLS_ROOT.glob("cam*/stream.m3u8")):
            break
        time.sleep(.25)
    webbrowser.open(f"http://127.0.0.1:{PORT}/site1.html")
    time.sleep(.5)
    webbrowser.open(f"http://127.0.0.1:{PORT}/site2.html")

if not NONINTERACTIVE and HOST in ("127.0.0.1", "localhost"):
    threading.Thread(target=open_pages, daemon=True).start()

print(f"Servidor escuchando en {HOST}:{PORT}")
print(f"Site 1: http://127.0.0.1:{PORT}/site1.html")
print(f"Site 2: http://127.0.0.1:{PORT}/site2.html")
print(f"Config:  http://127.0.0.1:{PORT}/config.html")
for ip in local_ips():
    print(f"Compartir (red local): http://{ip}:{PORT}/")
print("Ctrl+C para cerrar.")

try:
    httpd.serve_forever()
finally:
    stop_all()
    httpd.server_close()
