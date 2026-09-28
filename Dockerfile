# ─────────────────────────────────────────────────────────────────────────────
# Dashboard ECCSA — el kiosco de la oficina.
#
# Dos etapas, como el Dockerfile de Field:
#   1. node:20-alpine compila el build estático de SvelteKit,
#   2. python:3.11-slim + nginx + supervisor corre el resultado.
#
# El Dockerfile NO lleva credenciales: entran por --env-file al hacer `docker
# run` (ver deploy/run_container.ps1) y el entrypoint las convierte en
# /app/api/secretos_local.py, que está en .gitignore.
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM python:3.11-slim

# nginx para servir la pantalla y los medios; supervisor para los 3 procesos.
# `curl` lo usa el HEALTHCHECK del final.
RUN apt-get update && apt-get install -y --no-install-recommends \
        nginx supervisor curl \
    && rm -rf /var/lib/apt/lists/*

# pymssql necesita FreeTDS (el driver de SQL Server).
COPY api/requirements.txt /tmp/requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends \
        freetds-dev gcc \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && apt-get purge -y gcc freetds-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# App: build estático, API, worker, configuración de nginx y supervisor.
COPY --from=build /app/build /app/build
COPY api/    /app/api/
COPY worker/ /app/worker/
# Las versiones que anuncia /api/shell/state (contrato del ECCSA-Shell):
# app.version sale de package.json y shell.version del ECCSA_SHELL_VERSION que
# estampa `sync_shell.py`. Sin estos dos archivos el endpoint respondía "?" y la
# pantalla no podía decir qué build tenía arriba.
COPY package.json          /app/package.json
COPY ECCSA_SHELL_VERSION   /app/ECCSA_SHELL_VERSION
COPY docker/nginx.conf /etc/nginx/sites-available/default
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/supervisor/ /app/docker/supervisor/
COPY docker/entrypoint.sh /app/docker/entrypoint.sh
RUN chmod +x /app/docker/entrypoint.sh

# El build se identifica con un hash: la pantalla lo consulta en
# /api/dashboard/version y se recarga sola si cambió tras un deploy.
RUN date -u +%Y%m%d-%H%M%S > /app/BUILD

RUN mkdir -p /data/media/thumbs /data/media/wallpapers /data/media/avatars \
             /var/log/supervisor /var/cache/nginx /run/nginx
VOLUME ["/data"]

EXPOSE 80

# El healthcheck pregunta al backend, no al puerto: nginx puede estar arriba
# mientras la API no. 503 = degradado, y el contenedor se reinicia solo.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8100/healthz || exit 1

CMD ["/app/docker/entrypoint.sh"]
