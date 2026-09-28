# AGENTS.md · Dashboard ECCSA (kiosco de la oficina)

Pantalla de KPIs de Full HD que vive en la TV de la oficina. Es una **app
independiente**: no depende de Field, ni de Admon, ni del HUB. Lee de
`ECCSA_Admon` (la misma base de datos de siempre), pero lo hace **por su
propio** y lo publica en un snapshot en disco.

```
http://dashboard.ecc-sa.com.mx:8101/     ← solo red interna de la oficina
```

## Reglas del proyecto

### 1. Offline de verdad
La pantalla **nunca** llama a internet en runtime. Eso no es una preferencia de
estilo, es la diferencia entre una pantalla útil y una pantalla con ceros:

| Qué | Cómo se resuelve |
|---|---|
| KPIs, fotos, avatares | snapshot en `/data/snapshot.json` + medios en `/data/media` |
| Fondos | se **bajan una vez** de Bing a `/data/media/wallpapers` (URLs locales en el snapshot). En Field el fondo era una URL de bing.com y sin red se perdía |
| Clima | Open-Meteo desde el servidor, **con respaldo**: si falla, se sirve la última lectura y se dice de cuándo es |
| Tipografía | Outfit self-hosted en `static/fonts` (OFL). Nada de Google Fonts |

Y la regla que gobierna el `snapshotter`: **si algo falla, no se borra nada**.
Cayó la BD → el snapshot viejo sigue y la pantalla lo muestra diciendo "datos
de hace 40 min". Nunca ceros falsos (en un tablero, un cero se lee como "no
trabaja nadie").

### 2. Solo lectura
El kiosco **no escribe nada** en la base. Ni cursores, ni notas, ni nada. Por
eso el estado de los deltas vive en `/data/state.json` y no en `HUB_Config`
(que sería una escritura más que auditar y que puede tumbar el refresco).

El CRUD de notas **no** está aquí: va en un módulo de Admon (y mientras tanto
sigue en Field, en `/dashboard/notas`).

### 3. Todo es de solo lectura, incluido el snapshot
La pantalla se apagaría sola a las 00:00 y volvería a las 06:00. Y la versión
del contenedor se chequea cada minuto: si cambió, **la pantalla se recarga
sola** (un kiosco puede estar encendido días sin que nadie le dé F5).

## Arquitectura

```
TV (Edge en modo kiosco, sin teclado)
  │  GET /            (build de SvelteKit, estático)
  │  GET /api/dashboard/snapshot  (4 endpoints, lectura)
  │  GET /media/**    (thumbs, wallpapers, avatares — los sirve nginx)
  ▼
contenedor `dashboard` (ServerVM, puerto 8101)
  ├─ nginx      pantalla + medios + proxy a la API
  ├─ api        FastAPI, 4 GETs
  └─ snapshotter (loop 120 s)  SQL Server · Open-Meteo · Bing · thumbs
                                 │
                            /data (volumen dashboard_data)
                            snapshot.json · eventos.json · state.json
                            media/{thumbs,wallpapers,avatars} · sync.log
```

### El snapshot
Un JSON que lo lee la pantalla y escribe el `snapshotter`. Contrato exacto en
`src/lib/kiosk/types.ts` (front) y `worker/snapshotter.py` (back). Si se toca
un campo, se toca en los dos lados; `schema_version` sube cuando el cambio es
incompatible.

Ciclo (cada 2 min): clima → fondos → datos de la BD → medios → deltas de
eventos → `snapshot.json`. Todo con escritura atómica (tmp + rename), para que
nginx nunca lea un archivo a medio escribir.

### Los avisos en vivo
`/data/state.json` guarda el último Id visto de cada tabla "viva" (km, tickets,
reportes, firmados, notas, avisos). Lo que aparece con Id mayor es un evento
nuevo:

| Evento | Nivel | Cómo se ve |
|---|---|---|
| Km registrado | `info` | banda abajo, 1 tono |
| Ticket OxxoGas (con foto) | `info` | banda con la foto del ticket |
| Reporte nuevo | `info` | banda |
| **Reporte firmado** | `destaque` | **toma de pantalla** 8 s + arpegio + confeti |
| **Cumpleaños hoy / aniversario** | `destaque` | toma de pantalla 9 s |
| Aviso del admin (`HUB_Notificaciones`) | `alerta` | banda ámbar, 3 notas graves |
| **Marca de salida (lun–vie 18:30)** | `salida` | NO es una alerta: es una capa propia (`CapaSalida.svelte`) que se come la pantalla. Cuenta regresiva de 10 s (número gigante sobre rojo latente + un "tic" por segundo) y al llegar el **18:30 en números de 520 px** con bocinazo, 45 s. Pausa la rotación mientras está. Atajo: `?salida=cuenta\|ya\|fuera` |
| **Entrada / salida de la oficina** | `info` | banda con su propio tono: 👋 *Hola, {nombre}* (tres notas que suben) · 🚪 *Adiós, {nombre}* (dos que bajan). Vienen de `HUB_NetworkPresence`, que escribe el `network_scanner_worker`; el kiosco sólo lee |
| Sin movimiento 6 h | `info` | banda informativa |

Antispam: dedup por `id`, máximo 1 `destaque` cada 3 min, tope de 3 bandas, y en
el primer arranque no se reproduce el historial (si no, la TV saluda a la
oficina con 100 avisos de golpe). Las entradas/salidas además tienen un
**cooldown de 20 min por persona y tipo**: sin él, un celular que pierde el
WiFi un momento produce SALIDA+ENTRADA cada 3 minutos y la pantalla se llena
del mismo nombre.

Y NO toman la pantalla: alguien entra 8 veces al día, y si cada entrada fuera
un takeover, el pasillo sería insoportable. Son saludos, no alarmas.

### El audio
Sintetizado con **WebAudio**, sin archivos: 0 KB, 0 peticiones, imposible que se
rompa sin red. Volumen 0.35, silencio automático de 22:00 a 07:00, panic-mute
con cualquier tecla o clic, y persistencia en `localStorage`. La TV lo abre con
`--autoplay-policy=no-user-gesture-required` (ver `deploy/tv/instalar-kiosco.ps1`);
si el navegador bloqueara el audio, sale un chip "toca para activar el sonido".

## El escenario: 1920×1080 fijo

El diseño se mide en px sobre un escenario de 1920×1080 que se escala al
viewport (`--k-escala`). NO se usa `vh`/`rem` para el layout: con eso el
dashboard de Field terminaba con `overflow: hidden` y pantallas que se
recortaban según el monitor. Con escenario fijo la pantalla se ve **igual** en
cualquier TV y nunca aparece scroll.

Efectos caros (confeti, ken-burns) se apagan solos si los fps caen de 40
(`modo-ligero`), y a las 23:00 baja el brillo (`modo-noche`).

## Parámetros de URL (pruebas y soporte)

| Parámetro | Qué hace |
|---|---|
| `?pantalla=legends` | deja esa pantalla fija, sin rotación |
| `?sinrotacion=1` | quita la rotación, se queda en la primera |
| `?sinanim=1` | sin animaciones de entrada (para capturas) |
| `?debug=1` | vuelca la geometría de la pantalla (`.kpis`, `.veh`… con medidas) |
| `?replay=1` | vuelve a sacar los últimos avisos (uno cada 3.5 s): para ver y **oír** cómo se ve una alerta sin esperar a que alguien entre |
| `?salida=cuenta` | fuerza la cuenta regresiva de la salida (10→1 y salta sola al cartel) |
| `?salida=ya` | fuerza el cartel final con el 18:30 gigante |
| `?salida=fuera` | desactiva la marca de salida aunque sea la hora (para capturar otra cosa a las 18:30) |
| `?reloj=1` | fuerza la cuenta de segundos aunque la pantalla esté fija por URL (se esconde justo cuando no hay rotación, así que sin esto no se podría revisar) |

Las capturas de las 11 pantallas se sacan solas con el Edge del ServerVM (el
mismo que corre en la TV): `deploy/capturar.ps1`.

## Despliegue

```bash
# En el ServerVM (C:\Dashboard = clon de este repo)
docker build -t dashboard:latest .                 # si cambian Dockerfile/requirements/docker/
powershell -ExecutionPolicy Bypass -File deploy\run_container.ps1
sh deploy/hotsync.sh                               # si solo cambian .svelte/.css/.py
```

- `run_container.ps1` lee las credenciales de `deploy/env.local` (gitignored) o,
  como respaldo, de los secrets de `hub_python`, y las pasa con `--env-file`
  temporal que se borra. **Nunca** hay una contraseña en el repo ni en la imagen.
- El **volumen `dashboard_data` no se borra** al recrear el contenedor: ahí
  está el snapshot y los medios.
- `hotsync.sh` compila el front en un `node:20-alpine` descartable, copia al
  contenedor, reinicia `api` y `snapshotter`, y cambia `/app/BUILD` (que es lo
  que hace que la pantalla se recargue sola).

**Nunca reiniciar Docker Desktop en el ServerVM.** Los despliegues son
`docker build` + `docker run`; nada de tocar el servicio.

En la TV, una vez (PowerShell como Administrador):

```powershell
powershell -ExecutionPolicy Bypass -File deploy\tv\instalar-kiosco.ps1
```

Eso pone la entrada del hosts, crea el acceso directo de Edge en modo kiosco
(`--kiosk`, pantalla completa, autoplay), lo deja en el autoinicio y programa
el apagado del monitor entre 23:00 y 07:00.

## ECCSA-Shell

App registrada en el shell como **cuarta** (variante `t4`, como Field). Su
`src/app.css` es el CSS del shell y **hay que importarlo** en
`src/routes/+layout.svelte` — sin ese import los `var(--color-*)` no existen y
los colores Salientes se ven grises.

Cumple el contrato (`ECCSA-Shell/docs/CONTRATO.md`): expone
`GET /api/shell/state` **sin sesión** (§2b: `user: null`, `sync.estado` = salud
del último refresco). Lo que **no** monta es el banner `.sync-header` ni el
modal de novedades: son controles de una app con usuario, y en una pantalla del
pasillo son ruido. La versión de app y de shell se ven en el pie.

Para actualizar el CSS del shell:

```bash
python ECCSA-Shell/tools/build_shell.py
python ECCSA-Shell/tools/sync_shell.py --target . --variant t4
```

## Verificación

```bash
curl -s http://dashboard.ecc-sa.com.mx:8101/healthz        # status + degradado + generado_en
docker exec dashboard supervisorctl status
docker exec dashboard tail -30 /data/sync.log
npm run build && npx svelte-check --tsconfig ./tsconfig.json
```

El `healthz` devuelve **503** si el último refresco falló: es lo que usa el
HEALTHCHECK del contenedor.

## Pendiente Known (aún NO hecho)

- **Aviso de asistencia**: cuando exista el módulo de asistencia
  (`HUB_Asistencia`/horarios), sumar el evento al `detectar()` de
  `api/eventos.py`. Falta confirmar la tabla y el sentido del dato.
- **Módulo de red de WorkersAdmon** (`HUB_*` de red/zerotier): idea de avisar
  cuando un dispositivo cae. Falta el evento y la fuente.
- **Módulo de notas en Admon**: cuando exista, se borra
  `field/src/routes/dashboard/notas/` (Corte 2 del plan).

## Bugs que ya se encontraron (no volver a pasarlos)

1. **La escala del escenario mal calculada**: dividir el viewport entre 100 en
   vez de entre 1920/1080 daba `--k-escala: 45` y la pantalla se veía negra.
2. **Thumbs con ancho inventado**: el front pedía 1280 y el backend generaba
   960 → 404 → foto negra a pantalla completa. Ahora el ancho se publica en
   `snapshot.media` y lo usa el front.
3. **`avatarSrc()` envolvía rutas como base64** → `data:image/png;base64,/media/…`
   → avatares rotos en Legends.
4. **`time.time()` para dormir**: un ajuste de reloj del host dejó al
   snapshotter 20 min sin refrescar. Ahora usa `time.monotonic()`.
5. **`leerParams()` con return temprano**: `?pantalla=x&sinanim=1` ignoraba el
   `sinanim`, y las capturas salían a medio camino de las animaciones (parecían
   tarjetas faltantes).
6. **`import '../app.css'` faltaba** en el layout: sin los tokens del shell.
7. **Fotos de tickets con 15 bytes basura** antes del JPEG en
   `HUB_OxxoGasTickets.ImagenTicket` (bug del sync offline de Field, sigue en
   producción). `api/medios.py::_recuperar_firma` las salva; el arreglo de raíz es
   del lado de Field.
8. **`DATEPART(hour, Fecha)`** no existe para columnas `date` (error 9810 en
   `ReportesServicio.Fecha`): hay que castear a `DATETIME`.
9. **Suma de odómetro**: la serie diaria de km **no** puede ser
   `SUM(Kilometros)` (esa columna es el odómetro: daba 594,362 km en un día).
   Es "última lectura del día menos la lectura anterior".
