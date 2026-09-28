#!/bin/sh
# ─────────────────────────────────────────────────────────────────────────────
# hotsync.sh — publica cambios SIN reconstruir la imagen.
#
# Cuándo: cuando solo cambian `.svelte`, `.css`, `static/`, `api/*.py` o
# `worker/*.py`. Es lo que va a pasar el 95% de las veces (ajustar una pantalla,
# un texto, una consulta) y tarda segundos en vez de minutos.
#
# Cuándo NO: si cambian `Dockerfile`, `api/requirements.txt` o `docker/`. Ahí
# hay que reconstruir la imagen (deploy/build.ps1).
#
# Se ejecuta en el ServerVM, por SSH:
#   sh deploy/hotsync.sh            # aplica
#   sh deploy/hotsync.sh --dry-run  # imprime qué haría
#
# NO toca Docker Desktop: solo copia archivos dentro del contenedor que ya está
# corriendo y reinicia lo que haga falta.
# ─────────────────────────────────────────────────────────────────────────────
set -eu

CONT="dashboard"
RUTA_APP="/app"
DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then DRY_RUN=1; fi

echo "== hotsync: origen=$(pwd) contenedor=$CONT"

# 1) El build estático. Se compila acá mismo con un node descartable para no
#    depender de que el ServerVM tenga Node instalado (mismo truco que Field).
echo "-- compilando el front (node:20-alpine, contenedor descartable)"
docker run --rm -v "$PWD:/src" -w /src node:20-alpine sh -c "npm ci --silent && npm run build" >/dev/null
[ -d build ] || { echo "ERROR: no se generó build/"; exit 1; }

if [ "$DRY_RUN" = "1" ]; then
  echo "-- DRY RUN: se copiaría"
  echo "   build/   → $RUTA_APP/build"
  echo "   api/     → $RUTA_APP/api   (y reinicio de 'api')"
  echo "   worker/  → $RUTA_APP/worker (y reinicio de 'snapshotter')"
  exit 0
fi

# 2) El front (lo que más cambia). -a conserva mtime: nginx sirve con
#    no-store igual, pero los /_app/immutable hashed se resuelven por nombre.
echo "-- copiando build/"
docker cp build/. $CONT:$RUTA_APP/build/

# 3) La API y el worker, solo si cambiaron.
if [ -d api ]; then
  echo "-- copiando api/ y reiniciando 'api'"
  docker cp api/. $CONT:$RUTA_APP/api/
  docker exec $CONT supervisorctl restart api >/dev/null
fi
if [ -d worker ]; then
  echo "-- copiando worker/ y reiniciando 'snapshotter'"
  docker cp worker/. $CONT:$RUTA_APP/worker/
  docker exec $CONT supervisorctl restart snapshotter >/dev/null
fi

# 4) El BUILD cambia en cada hotsync: es lo que hace que la pantalla recargue
#    sola (no tiene nadie que le dé F5).
BUILD=$(date -u +%Y%m%d-%H%M%S)
docker exec $CONT sh -c "echo $BUILD > /app/BUILD"
echo "-- build: $BUILD (la pantalla lo detecta en ≤60 s y se recarga)"

# 5) Que el snapshot se regenere ya, no en el próximo ciclo.
echo "-- forzando un ciclo del snapshotter"
docker exec $CONT supervisorctl restart snapshotter >/dev/null

echo "== listo"
