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

old = None
if CONFIG_FILE.exists():
    try:
        old = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        old = None

print("\n=== Configuración de cámaras ===\n")

# Password de configuración web: se conserva si ya existe
if old and old.get("admin_password_hash"):
    change_pw = ask("¿Cambiar el password de la página de configuración? (s/n)", "n").lower()
    if change_pw in ("s","si","sí","y","yes"):
        admin_pw = ask("Nuevo password", secret=True)
        if not admin_pw:
            print("ERROR: el password no puede estar vacío.")
            raise SystemExit(1)
        admin_hash = hash_password(admin_pw)
    else:
        admin_hash = old["admin_password_hash"]
else:
    admin_pw = ask("Password para la página de configuración web", secret=True)
    if not admin_pw:
        print("ERROR: el password no puede estar vacío.")
        raise SystemExit(1)
    admin_hash = hash_password(admin_pw)

# Credenciales globales: reutilizan los valores actuales
old_gu = (old or {}).get("global_user", "")
old_gp = (old or {}).get("global_password", "")
global_user = ask("Usuario RTSP global (default para todas las cámaras)", old_gu)
gp_ask = ask("Contraseña RTSP global (vacío = conservar actual)", "", secret=True)
global_password = gp_ask or old_gp

# Cámaras: reutilizan las actuales si existen
old_cams = (old or {}).get("cameras", [])
n_default = str(len(old_cams)) if old_cams else "1"
raw_n = ask("¿Cuántas cámaras vas a configurar?", n_default)
try:
    n_cams = max(1, int(raw_n))
except ValueError:
    n_cams = max(1, int(n_default))
n_cams = min(n_cams, 4)

cams = []
for i in range(n_cams):
    prev = old_cams[i] if i < len(old_cams) else {}
    print(f"\n--- Cámara {i+1} ---")
    name = ask("Nombre", prev.get("name", f"Camara {i+1}"))
    ip = ask("IP", prev.get("ip", ""))
    user = ask(f"Usuario RTSP (vacío = global '{global_user}')", prev.get("user", ""))
    password = ask("Contraseña RTSP (vacío = conservar actual)", "", secret=True) or prev.get("password", "")
    port = int(ask("Puerto RTSP", str(prev.get("port", 554))))
    stream = ask("Ruta del stream", prev.get("stream", "/stream1"))
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

site1_layout = choose_layout("Sitio 1", (old or {}).get("site1", {}).get("layout", "1x1"))
site1_cams = choose_cameras("Sitio 1", cams, site1_layout)

site2_layout = choose_layout("Sitio 2", (old or {}).get("site2", {}).get("layout", "1x1"))
site2_cams = choose_cameras("Sitio 2", cams, site2_layout)

config = {
    "port": 8765,
    "admin_password_hash": admin_hash,
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