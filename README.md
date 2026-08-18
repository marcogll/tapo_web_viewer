<p align="center">
  <a href="https://soul23.mx">
    <picture>
      <source
        media="(prefers-color-scheme: dark)"
        srcset="https://raw.githubusercontent.com/marcogll/mg_data_storage/refs/heads/main/soul23/logo/soul23_logo_wh.png">
      <source
        media="(prefers-color-scheme: light)"
        srcset="https://raw.githubusercontent.com/marcogll/mg_data_storage/refs/heads/main/soul23/logo/soul23_logo_blk.png">
      <img
        src="https://raw.githubusercontent.com/marcogll/mg_data_storage/refs/heads/main/soul23/logo/soul23_logo_blk.png"
        width="110"
        alt="Soul:23">
    </picture>
  </a>
</p>

<h1 align="center">RTSP Viewer Multicam</h1>

<p align="center">
  Visor multicámara RTSP/HLS para monitoreo local desde el navegador.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3a3a3a?style=flat-square&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/FFmpeg-3a3a3a?style=flat-square&logo=ffmpeg&logoColor=white">
  <img src="https://img.shields.io/badge/HLS.js-3a3a3a?style=flat-square&logo=javascript&logoColor=white">
</p>

---

## Descripción

RTSP Viewer Multicam es un visor local que consume streams RTSP de cámaras IP (Tapo, Hikvision, Dahua, etc.), los transcodifica a HLS mediante FFmpeg y los sirve en el navegador sin necesidad de usar la app del fabricante.

Nació de una necesidad simple: ver la cámara de la entrada desde la oficina sin tener que sacar el teléfono y abrir la app de Tapo cada vez. Ahora el stream vive en una pestaña del navegador, siempre accesible, con latencia baja y sin depender de servicios en la nube.

Soporta hasta 4 cámaras simultáneas con dos vistas independientes (Site 1 y Site 2), pensadas para distribuirse en monitores separados. Funciona en Windows, macOS y Linux, con o sin Docker.

## Características

- Hasta 4 cámaras simultáneas con layouts 1x1, 1x2 o 2x2
- Dos vistas independientes para multi-monitor
- Botón Picture-in-Picture individual por cámara
- Página de configuración web protegida con password (`/config.html`)
- Credenciales RTSP globales (default para todas las cámaras) con override individual por cámara
- Conexión RTSP con fallback automático de TCP a UDP
- Transcodificación con libx264 (elimina artefactos de frames corruptos)
- Puerto dinámico: si 8765 está ocupado, busca 8766-8784
- Limpieza automática de procesos FFmpeg al cerrar
- Configuración por terminal o por web, según prefieras
- HLS.js local: funciona sin conexión a internet

## Estructura del proyecto

```text
rtsp-viewer-multicam-v2/
├── config/
│   └── cameras.json          # Credenciales y layout (permisos 600)
├── hls/                      # Segmentos HLS generados en runtime
├── server.py                 # Servidor HTTP + gestión de FFmpeg
├── setup.py                  # Asistente interactivo de configuración
├── viewer.js                 # Reproductor HLS en navegador
├── style.css                 # Grid y estilos del visor
├── index.html                # Página de inicio con enlaces
├── site1.html                # Vista Sitio 1
├── site2.html                # Vista Sitio 2
├── config.html               # Página de configuración web (login + setup)
├── hls.min.js                # HLS.js local (funciona sin internet)
├── Dockerfile
├── docker-compose.yml
│   # Windows
├── setup-windows.bat
├── start-windows.bat
├── stop-windows.bat
├── start-docker-windows.bat  # (solo si usas Docker)
├── stop-docker-windows.bat   # (solo si usas Docker)
├── install-autostart-windows-docker.ps1
├── install-autostart-windows-nodocker.ps1
├── uninstall-autostart-windows.ps1
│   # macOS / Linux
├── setup-mac-linux.sh
├── start-mac-linux.sh
├── stop-mac-linux.sh
└── README.md
```

---

## Windows

### Requisitos (sin Docker)

No necesitas Docker ni WSL. Solo:

1. [Python 3](https://www.python.org/downloads/) -- al instalar, marcar **"Add Python to PATH"**
2. [FFmpeg](https://www.gyan.dev/ffmpeg/builds/) -- release full, extraer y agregar su carpeta `bin` al PATH

Verificar:

```cmd
python --version
ffmpeg -version
```

### Configuración inicial

```cmd
setup-windows.bat
```

El asistente por terminal pide: password de administrador, credenciales RTSP globales y las cámaras. Si ya existe configuración, reutiliza los valores actuales como defaults.

Alternativa por web: iniciar el servidor (`start-windows.bat`), abrir `http://127.0.0.1:8765/config.html`, crear el password y agregar las cámaras.

### Iniciar / Detener

```cmd
start-windows.bat    :: inicia y abre el navegador
stop-windows.bat     :: detiene todo
```

### Arranque automático al iniciar sesión

**Sin Docker (Python directo):**

```powershell
powershell -ExecutionPolicy Bypass -File install-autostart-windows-nodocker.ps1
```

**Con Docker** (solo si ya lo tienes instalado):

```powershell
powershell -ExecutionPolicy Bypass -File install-autostart-windows-docker.ps1
```

**Eliminar el arranque automático:**

```powershell
powershell -ExecutionPolicy Bypass -File uninstall-autostart-windows.ps1
```

Alternativa manual: copiar un acceso directo de `start-windows.bat` a la carpeta `shell:startup` (Win+R).

---

## macOS

### Requisitos

```bash
brew install python3 ffmpeg
```

### Configuración inicial

```bash
chmod +x setup-mac-linux.sh start-mac-linux.sh stop-mac-linux.sh
./setup-mac-linux.sh
```

### Iniciar / Detener

```bash
./start-mac-linux.sh
./stop-mac-linux.sh
```

### Arranque automático (launchd)

Crear `~/Library/LaunchAgents/com.rtsp-viewer.plist` (ajustar rutas):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.rtsp-viewer</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/TU_USUARIO/ruta/rtsp-viewer-multicam-v2/server.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/TU_USUARIO/ruta/rtsp-viewer-multicam-v2</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/rtsp-viewer.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/rtsp-viewer.err</string>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.rtsp-viewer.plist
# Detener
launchctl unload ~/Library/LaunchAgents/com.rtsp-viewer.plist
```

---

## Linux

### Requisitos

**Debian / Ubuntu:**

```bash
sudo apt update && sudo apt install python3 ffmpeg
```

**Arch Linux:**

```bash
sudo pacman -S python ffmpeg
```

**Fedora:**

```bash
sudo dnf install python3 ffmpeg
```

### Configuración inicial

```bash
chmod +x setup-mac-linux.sh start-mac-linux.sh stop-mac-linux.sh
./setup-mac-linux.sh
```

### Iniciar / Detener

```bash
./start-mac-linux.sh
./stop-mac-linux.sh
```

### Arranque automático (systemd)

Crear `/etc/systemd/system/rtsp-viewer.service` (ajustar rutas y usuario):

```ini
[Unit]
Description=RTSP Viewer Multicam
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=TU_USUARIO
WorkingDirectory=/home/TU_USUARIO/ruta/rtsp-viewer-multicam-v2
ExecStart=/usr/bin/python3 /home/TU_USUARIO/ruta/rtsp-viewer-multicam-v2/server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now rtsp-viewer.service
journalctl -u rtsp-viewer.service -f
```

Alternativa sin sudo (servicio de usuario):

```bash
mkdir -p ~/.config/systemd/user
```

```ini
# ~/.config/systemd/user/rtsp-viewer.service
[Unit]
Description=RTSP Viewer Multicam

[Service]
Type=simple
WorkingDirectory=%h/ruta/rtsp-viewer-multicam-v2
ExecStart=/usr/bin/python3 %h/ruta/rtsp-viewer-multicam-v2/server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now rtsp-viewer.service
loginctl enable-linger $USER
```

---

## Docker (Proxmox / servidor)

El proyecto incluye `Dockerfile` y `docker-compose.yml` para correrlo como contenedor. Ideal para Proxmox: el servidor escucha en `0.0.0.0` y la configuración se hace desde la web.

```bash
git clone https://github.com/marcogll/tapo_web_viewer.git
cd tapo_web_viewer
docker compose up -d --build
```

Acceder desde cualquier dispositivo de la red:

```text
http://IP_DEL_SERVIDOR:8765/
```

En el primer arranque se crea una configuración vacía. Abrir `http://IP_DEL_SERVIDOR:8765/config.html`, crear el password de administrador y agregar las cámaras. Reiniciar para aplicar:

```bash
docker compose restart
```

Los datos persisten en volúmenes:

| Volumen | Contenido |
|---|---|
| `./config` | `cameras.json` con credenciales y layout |
| `./hls` | Segmentos HLS temporales |

Variables de entorno:

| Variable | Default | Descripción |
|---|---|---|
| `RTSP_VIEWER_HOST` | `127.0.0.1` | Dirección de escucha. `0.0.0.0` para exponer en red local |
| `RTSP_VIEWER_PORT` | `8765` | Puerto de escucha |
| `RTSP_VIEWER_NONINTERACTIVE` | - | `1` para no abrir navegador ni pedir datos por terminal |

---

## Configuración de cámaras (común a todos los OS)

Hay dos formas de configurar: la **página web** (recomendada) o el **asistente por terminal**.

### Configuración web

1. Iniciar el servidor (script de tu OS o docker)
2. Abrir `http://127.0.0.1:8765/config.html` (o `http://IP_DEL_SERVIDOR:8765/config.html` en red local)
3. En el primer acceso se pide crear el password de administrador
4. Agregar las cámaras y configurar los sitios
5. Reiniciar el servidor para aplicar

### Asistente por terminal

```cmd
:: Windows
setup-windows.bat
```

```bash
# macOS / Linux
./setup-mac-linux.sh
```

Solicita:

1. **Password de configuración** -- protege la página web `/config.html`
2. **Usuario RTSP global** -- default para todas las cámaras (opcional)
3. **Contraseña RTSP global** -- default para todas las cámaras (opcional)
4. Por cada cámara:

| Campo | Ejemplo |
|---|---|
| Nombre | Recepción |
| IP | 192.168.100.22 |
| Usuario RTSP (vacío = global) | marcogll |
| Contraseña RTSP (vacío = global) | ******** |
| Puerto RTSP | 554 |
| Ruta del stream | /stream1 |

Si una cámara deja Usuario/Contraseña vacíos, usa las credenciales globales. Si la cámara tiene sus propios valores, estos tienen prioridad.

### Cámaras Tapo

1. App Tapo > Settings > Advanced Settings > habilitar RTSP
2. Crear cuenta RTSP local (usuario y contraseña)
3. Obtener IP desde la app o el router
4. Rutas comunes: `/stream1` (HD), `/stream2` (SD)

Las credenciales se guardan en `config/cameras.json` con permisos `600` en macOS/Linux.

---

## Uso del visor

### Vistas

```text
http://127.0.0.1:8765/          # Página de inicio con enlaces
http://127.0.0.1:8765/site1.html
http://127.0.0.1:8765/site2.html
```

### Compartir en la red local

Si el servidor escucha en `0.0.0.0` (docker o `RTSP_VIEWER_HOST=0.0.0.0`), cualquier dispositivo de la red puede ver las cámaras:

```text
http://IP_DEL_SERVIDOR:8765/
```

El servidor imprime las URLs compartibles al arrancar.

### Picture-in-Picture

Cada cámara tiene un botón **PiP** en la esquina inferior derecha. Al hacer click, el video se muestra en una ventana flotante que permanece encima de otras aplicaciones.

Para PiP global del navegador, usar la extensión [Picture-in-Picture Extension (by Google)](https://chromewebstore.google.com/detail/picture-in-picture-extens/hkgfoiooedgoejojocmhlaklaeopbecg?hl=en):

1. Instalar la extensión desde Chrome Web Store
2. Abrir cualquier sitio del visor (`site1.html` o `site2.html`)
3. Click derecho sobre el video > "Picture in picture" o usar el botón de la extensión

---

## Seguridad

- El servidor HTTP escucha solo en `127.0.0.1` por defecto (no accesible desde la red)
- `config/cameras.json` tiene permisos `600` en macOS/Linux
- La página de configuración y los endpoints de escritura requieren password
- El password de administrador se guarda como hash SHA-256
- La API pública `/api/config` solo expone nombres de cámaras y layouts, nunca credenciales

## Troubleshooting

**Puerto ocupado** -- El servidor busca automáticamente puertos 8766-8784. Verificar:

```bash
# macOS
lsof -nP -iTCP:8765 -sTCP:LISTEN
# Linux
ss -tlnp | grep 8765
```

```cmd
:: Windows
netstat -ano | findstr :8765
```

**Camara no conecta** -- Verificar IP con `ping`, probar la URL RTSP en VLC (`rtsp://user:pass@IP:554/stream1`), confirmar que RTSP esta habilitado en la app Tapo. Algunas Tapo solo aceptan 1-2 conexiones RTSP simultaneas: no dejes dos instancias del visor corriendo a la vez.

**FFmpeg no encontrado** -- Verificar `ffmpeg -version`. Si no existe, instalar segun la seccion de tu OS.

**Video con delay** -- Ajustar `hls_time` en `server.py` (valor menor = menor latencia, mas CPU). Considerar stream SD (`/stream2`).

**Raya verde en el video** -- Causada por frames corruptos al copiar el stream. El servidor transcodifica con libx264 por defecto, lo que la elimina. Si reaparece, reinicia el servidor.

**Procesos colgados:**

```bash
# macOS / Linux
pkill -f "ffmpeg.*stream.m3u8"
```

```cmd
:: Windows
taskkill /F /IM ffmpeg.exe
```

## Licencia

Uso libre para fines personales y comerciales.
