#!/usr/bin/env python3
import hashlib
import json
import os
import getpass
from pathlib import Path

BASE = Path(__file__).resolve().parent
CONFIG_DIR = BASE / "config"
CONFIG_FILE = CONFIG_DIR / "cameras.json"

def ask(text, default=None, secret=False):
    suffix = f" [{default}]" if default else ""
    if secret:
        value = getpass.getpass(f"{text}{suffix}: ").strip()
    else:
        value = input(f"{text}{suffix}: ").strip()
    return value or (default or "")

def hash_password(pw):
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def choose_layout(label, default):
    value = ask(f"Layout para {label}: 1x1, 1x2 o 2x2", default).lower()
    if value not in ("1x1","1x2","2x2"):
        value = default
    return value

def camera_count(layout):
    return {"1x1":1,"1x2":2,"2x2":4}[layout]

def choose_cameras(label, cams, layout):
    print(f"\nCámaras disponibles para {label}:")
    for i,c in enumerate(cams, 1):
        print(f"  {i}. {c['name']}")
    maxn = camera_count(layout)
    raw = ask(f"Índices separados por coma (máximo {maxn})", ",".join(str(i+1) for i in range(min(maxn,len(cams)))))
    selected = []
    for part in raw.split(","):
        try:
            idx = int(part.strip()) - 1
            if 0 <= idx < len(cams) and idx not in selected:
                selected.append(idx)
        except ValueError:
            pass
    return selected[:maxn]

CONFIG_DIR.mkdir(exist_ok=True)
print("\n=== Configuración de cámaras ===\n")

admin_pw = ask("Password para la página de configuración web", secret=True)
if not admin_pw:
    print("ERROR: el password no puede estar vacío.")
    raise SystemExit(1)

global_user = ask("Usuario RTSP global (default para todas las cámaras)", "")
global_password = ask("Contraseña RTSP global (default para todas las cámaras)", "", secret=True)

cams = []
while True:
    name = ask("Nombre de la cámara", f"Camara {len(cams)+1}")
    ip = ask("IP")
    user = ask(f"Usuario RTSP (vacío = global '{global_user}')", "")
    password = ask(f"Contraseña RTSP (vacío = global)", "", secret=True)
    port = int(ask("Puerto RTSP", "554"))
    stream = ask("Ruta del stream", "/stream1")
    if not stream.startswith("/"):
        stream = "/" + stream

    cams.append({
        "name": name,
        "ip": ip,
        "user": user,
        "password": password,
        "port": port,
        "stream": stream
    })

    if len(cams) >= 4:
        break
    more = ask("¿Agregar otra cámara? (s/n)", "n").lower()
    if more not in ("s","si","sí","y","yes"):
        break

site1_layout = choose_layout("Sitio 1", "2x2" if len(cams) >= 4 else ("1x2" if len(cams)>=2 else "1x1"))
site1_cams = choose_cameras("Sitio 1", cams, site1_layout)

site2_layout = choose_layout("Sitio 2", "1x1")
site2_cams = choose_cameras("Sitio 2", cams, site2_layout)

config = {
    "port": 8765,
    "admin_password_hash": hash_password(admin_pw),
    "global_user": global_user,
    "global_password": global_password,
    "cameras": cams,
    "site1": {"layout": site1_layout, "cameras": site1_cams},
    "site2": {"layout": site2_layout, "cameras": site2_cams}
}

CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
try:
    os.chmod(CONFIG_FILE, 0o600)
except Exception:
    pass

print(f"\nConfiguración guardada en {CONFIG_FILE}")
