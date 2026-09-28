#!/bin/sh
# ─────────────────────────────────────────────────────────────────────────────
# entrypoint.sh — arma /app/api/secretos_local.py y arranca supervisord.
#
# Las credenciales NUNCA están en la imagen: entran por variables de entorno
# (`docker run --env-file`, ver deploy/run_container.ps1) y se escriben en un
# archivo que está en .gitignore. El archivo se regenera en cada arranque, así
# que rotar la contraseña es cambiar la variable y reiniciar el contenedor.
#
# Es el mismo patrón que usa hub_python y workersadmon: si algo se saliera de
# inventar su propia manera de leer secretos, la próxima rotación falla en
# producción y no en un `docker run` de prueba.
# ─────────────────────────────────────────────────────────────────────────────
set -eu

SECRETOS=/app/api/secretos_local.py

if [ -n "${HUB_DB_PASSWORD:-}" ]; then
  cat > "$SECRETOS" <<PY
# Generado por docker/entrypoint.sh — NO editar, NO subir al repo.
import os

DB_SERVER = os.environ.get("HUB_DB_SERVER", "10.188.141.15")
DB_USER = os.environ.get("HUB_DB_USER", "sa")
DB_PASSWORD = os.environ.get("HUB_DB_PASSWORD", "")
DB_DATABASE = os.environ.get("HUB_DB_DATABASE", "ECCSA_Admon")

DB_CONFIG_LOCAL = {
    "server": DB_SERVER,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "database": DB_DATABASE,
}
PY
  chmod 600 "$SECRETOS"
  echo "[entrypoint] secretos escritos desde el entorno (db=${HUB_DB_DATABASE:-ECCSA_Admon})"
else
  echo "[entrypoint] AVISO: HUB_DB_PASSWORD no está en el entorno." >&2
  echo "[entrypoint] El snapshotter no va a poder leer la base y la pantalla" >&2
  echo "[entrypoint] mostrará 'sin-datos'. Ver deploy/run_container.ps1." >&2
fi

# /data es volumen: si por lo que sea no estuviera montado, el snapshot
# desaparecería en cada reinicio. Se avisa en vez de fallar en silencio.
mkdir -p /data/media/thumbs /data/media/wallpapers /data/media/avatars
if ! mount | grep -q " /data "; then
  echo "[entrypoint] AVISO: /data no parece un volumen montado; el snapshot" >&2
  echo "[entrypoint] se perderá al reiniciar el contenedor." >&2
fi

echo "[entrypoint] build $(cat /app/BUILD 2>/dev/null || echo '?') · arrancando supervisord"
exec /usr/bin/supervisord -c /app/docker/supervisor/supervisord.conf
