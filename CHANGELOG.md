# CHANGELOG

## 2026-09-28 · v1.0.0 — Primera versión del kiosco

App independiente con la información del dashboard que estaba dentro de Field,
para la TV de la oficina (1920×1080, red interna, sin Cloudflare).

### Nuevo
- **10 pantallas** con rotación de 45 s en orden aleatorio:
  La Oficina Ahora, Combustible, Legends, Reportes, Tickets, Cumpleaños,
  Métricas, Fotografías, Clima y Notas.
- **Escenario fijo de 1920×1080** escalado al viewport: la pantalla se ve igual
  en cualquier TV y nunca aparece scroll (Field dependía de `vh`/`rem` con
  `overflow: hidden`).
- **Avisos en vivo con sonido**: registro de km, tickets OxxoGas (con foto),
  reportes nuevos, reportes **firmados**, **cumpleaños/aniversarios del día**,
  avisos del admin y "oficina sin movimiento". Tres niveles: banda inferior,
  toast de esquina y **toma de pantalla completa** con confeti (pausa la
  rotación). Antispam: dedup por id, 1 destaque cada 3 min, tope de 3 bandas.
- **Audio sintetizado con WebAudio** (sin archivos): 0 KB, 0 peticiones.
  Volumen 0.35, silencio automático 22:00–07:00, panic-mute con cualquier tecla.
- **Backend propio y autónomo**: `worker/snapshotter.py` calcula cada 2 min el
  snapshot con SQL Server + Open-Meteo + fondos de Bing, genera los thumbs y
  los avatares, y escribe todo en `/data`. **Si algo falla no borra nada**:
  la pantalla sigue con el último dato y lo dice.
- **Fondos locales**: se bajan una vez de Bing y se sirven desde el volumen
  (en Field era una URL de bing.com: sin red se perdía el fondo).
- **Tipografía self-hosted** (Outfit, OFL): sin CDN.
- **Modo noche** (23:00–06:00, brillo al 70%) y **apagado** de 00:00 a 06:00.
- **Modo ligero** automático si los fps caen de 40, y **anti-quemado** (±2 px
  cada 4 min).
- **Recarga por versión**: la pantalla compara el build del contenedor cada
  minuto y se recarga sola tras un deploy (un kiosco no tiene a nadie que le
  dé F5).
- **Parámetros de URL** para pruebas y soporte: `?pantalla=`, `?sinrotacion=1`,
  `?sinanim=1`, `?debug=1` (geometría de la pantalla).
- **API mínima** de 4 GETs: `/api/dashboard/snapshot`, `/api/dashboard/version`,
  `/api/shell/state` (contrato del ECCSA-Shell, sin sesión) y `/healthz`.
- **Instalador para la TV** (`deploy/tv/instalar-kiosco.ps1`): hosts, acceso
  directo de Edge en modo kiosco con sonido, autoinicio y apagado nocturno.
- `deploy/capturar.ps1`: capturas de las 10 pantallas con el Edge del servidor
  (el mismo que corre en la TV).

### Mejoras sobre el dashboard de Field
- El carrusel de fotos **sí avanza** (en Field `photoIdx` nunca se incrementaba:
  la foto se quedaba 20 segundos congelada).
- **Heatmap hora × día** en Métricas: responde "a qué hora trabaja la oficina".
- **Radar de flota** con semáforo por hora del último registro, no solo por si
  hay km en la semana.
- **Ventana móvil de 7 días** en Combustible: la semana de ECCSA empieza en
  domingo, así que con la semanal los domingos la pantalla quedaba vacía.
- La serie diaria de km se calcula por vehículo (última lectura del día menos la
  anterior). Sumar el odómetro daba cifras sin sentido (594,362 km en un día).
- Se **distingue "sin datos" de "cero"**: si no hay lectura anterior para
  comparar, la tarjeta lo dice en vez de inventar un 0.
- Avatares y fotos viajan como **archivos locales**, no como base64 dentro del
  JSON (la respuesta pasó de ~700 KB a ~12 KB).
- Las fotos de tickets corruptas en la base (15 bytes basura antes del JPEG, un
  bug del sync offline de Field) **se recuperan** en vez de no mostrarse.

### ECCSA-Shell
- Registrada como **cuarta app** del shell (variante `t4`), y subida al shell
  1.10.0 para quedar al día con Field, Admon y el panel.
- `sync_shell.py`: se arregló `--target X --variant t4`, que estaba roto
  (nunca encontraba la ruta del CSS), y `APP_ID_DE_VARIANTE` pasó a derivarse
  del nombre de la carpeta, porque con dos apps `t4` se pisaban entre sí.
- `propagate.py`: `REPOS` con el repo nuevo y mensajes dinámicos.
- `check_versiones.py`: compara también `dashboard` y salta las apps cuyo
  contenedor no está corriendo (antes las marcaba como desincronizadas).
- `docs/`: contrato del caso "app sin sesión" (§2b), receta para pantallas
  (CREAR-APP §5b) y tablas de "las 3 apps" actualizadas.

### Bugs encontrados y corregidos durante la puesta en marcha
1. Escala del escenario mal calculada (45× en vez de 1×) → pantalla negra.
2. Thumbs pedidos a 1280 px cuando el backend genera 960 → foto negra.
3. `avatarSrc()` envolvía rutas locales como base64 → avatares rotos.
4. El `snapshotter` dormía con `time.time()`: un ajuste de reloj del host lo
   dejó 20 min sin refrescar → ahora `time.monotonic()`.
5. `leerParams()` con `return` temprano: `?pantalla=x&sinanim=1` ignoraba el
   segundo parámetro.
6. Faltaba `import '../app.css'`: los tokens del shell no existían.
7. `DATEPART(hour, Fecha)` sobre una columna `date` (error 9810).
8. Nombres de archivo de los fondos tomados del path (`bing-th.jpg` para todos).
9. `MAX(Id)` con la identidad mezclada con un agregado → columna sin nombre.

### Pendiente
- Módulo de notas en Admon (CRUD). Hasta entonces el de Field sigue vivo en
  `/dashboard/notas`, y el dashboard de Field **no** se borra todavía: el corte
  se hace cuando la TV ya apunte acá.
- Aviso de asistencia (falta definir el evento y la fuente de datos).
- Aviso del módulo de red de WorkersAdmon (misma cosa).
