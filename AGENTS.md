# AGENTS.md · Dashboard ECCSA (kiosco de la oficina)

> ⚠️ **LEGACY (ServerVM `10.188.141.31`):** lo que sigue describe el host
> viejo, que **ya no se usa**. Las apps se despliegan en WebbApps con Arcane
> (ver `AGENTS.md` de la raíz, §2). **No ejecutes estos pasos en ServerVM.**

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
| **Aviso a pantalla completa** (`pantalla`) | `aviso` | 10 s a pantalla completa: fondo verde saturado (90%), el **nombre de quien lo hizo en 168 px**, el módulo de dónde viene arriba, el dato grande, la barra de tiempo y "Continuar". **Sin fotografías**, por pedido explícito del usuario. Van en COLA de 3: si llegan cuatro de golpe se muestran uno por uno y el resto se ve de banda. Pausa la rotación. Atajo: `?aviso=km\|ticket\|firmado\|presencia` |
| **Marca de salida (lun–vie 18:30)** | `salida` | NO es una alerta: es una capa propia (`CapaSalida.svelte`) que se come la pantalla. Cuenta regresiva de 10 s (número gigante sobre rojo latente + un "tic" por segundo) y al llegar el **18:30 en números de 520 px** con bocinazo, 45 s. Pausa la rotación mientras está. Atajo: `?salida=cuenta\|ya\|fuera` |
| **Entrada / salida de la oficina** | `pantalla` | aviso a pantalla completa con su propio tono: 👋 *Entró, {nombre}* (tres notas que suben) · 🚪 *Salió, {nombre}* (dos que bajan). Vienen de `HUB_NetworkPresence`, que escribe el `network_scanner_worker`; el kiosco sólo lee. Lo que evita que sea insoportable es el cooldown de 20 min por persona y tipo, no que sea una banda |
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
| `?clasico=1` | vuelve al diseño anterior (marcha atrás temporal) |

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
| `?pantalla=portada` | la pantalla de portada con la imagen del mes |

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

## Cómo se recarga la pantalla cuando hay un deploy (leer antes de publicar)
Este fue el agujero que costó una tarde: se subían cambios del front, las
capturas Headless salían bien y **en la TV seguía lo de antes**, sin un solo
aviso. Dos fallas encimadas, y la segunda es la que más confunde:

- `leer_build()` (`api/config.py`) devuelve DOS cosas: el texto de `/app/BUILD`
  (lo escribe el Dockerfile al construir la imagen) **y la mtime de
  `/app/build/index.html`**. Con sólo el texto, un despliegue que copia la
  carpeta `build/` dentro del contenedor —que es el hotsync y también lo que se
  puede hacer a mano— no movía nada y la pantalla no se enteraba.
- El navegador compara ese identificador contra **el que tiene guardado en
  `localStorage`**, NO contra `datos.build`. Ese campo viene del snapshot, que
  se reescribe cada 2 min con el build del servidor: al primer refresco los dos
  ya eran iguales —con el JS viejo corriendo— y como nunca volvían a diferir,
  la pantalla no recargaba **nunca**. El bug se auto-ocultaba, y por eso tampoco
  lo arreglaba subir el BUILD a mano. Antes de recargar se guarda el
  identificador nuevo, para no entrar en bucle de recargas.
- **Palanca de operador**: tocar `/data/forzar-recarga` dentro del contenedor
  cambia el build y recarga todas las pantallas sin ir a la oficina a reiniciar
  Edge. Hace falta para lo que el navegador no puede detectar solo: cuando el JS
  que corre ya es el nuevo, en el servidor no cambia nada y nadie lo notaría.
- Para comprobar si la TV se enteró, contar recargas reales en el log de nginx:
  las peticiones `GET /` de clientes Edge son recargas; los `GET
  /api/panel/estado` cada 3 s son el polling del panel, no recargas. Ojo al
  parsear el log: un patrón mal hecho cuenta como recarga cualquier `GET` y da
  cifras absurdas (falso positivo).

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

## Cómo levantar la TV cuando el kiosco se apaga (LEER SI `tv_conectada` sale False)
- El cliente es **Edge en modo kiosco**, no un worker. Si no hay proceso `msedge.exe`
  con `--kiosk`, la TV está apagada y no es un bug del servidor.
- **El dominio `dashboard.ecc-sa.com.mx` NO resuelve desde el ServerVM**: no hay DNS
  ni entrada en el hosts. Hay que lanzar el kiosco con la IP
  `http://10.188.141.31:8101/`.
- Desde SSH (sesión 0) un `Start-Process msedge` abre el navegador donde nadie lo ve.
  Para que aparezca en el escritorio hay que correrlo en la **sesión interactiva**:
  una tarea programada con `-LogonType Interactive` para el usuario `ECCSA`, que es
  la sesión `console` (id 1). Es lo único que funciona.
- **Comprobar que volvió**: `tv_conectada` en `/api/panel/estado` y que el log de
  nginx reciba peticiones del navegador. Ojo al parsear el log: un `grep` mal escrito
  dio "0 peticiones" cuando había 107 mil. Comparar contra el reloj del contenedor.

---

<!-- SKILLS-CATALOG:START -->
## Skills disponibles

> **Catálogo completo:** `C:\Users\ECCSAia\.config\opencode\SKILLS.md` (global).
> **Regla:** antes de empezar una tarea, si hay un skill que aplique, cárgalo con la herramienta `skill` y síguelo. Los skills son parte del flujo, no adornos.

### RTK — ahorro de tokens (uso obligatorio)

`rtk` está instalado y el plugin de OpenCode reescribe comandos de shell para comprimir su salida. **Úsalo siempre** que aplique:

- Deja que el plugin lo haga, o prefija `rtk`: `rtk git status`, `rtk cargo test`, `rtk npm test`, `rtk ls`, `rtk grep ...`.
- Mide el ahorro con `rtk gain`; para ver la salida completa, `rtk bypass <comando>`.
- Si el comando no está soportado (PowerShell nativo, scripts Python), sigue normal.

### Caveman — modo por defecto (uso obligatorio)

Caveman está activo por defecto en OpenCode (plugin nativo + bloque global). Responde corto, sin fluff; conserva código, comandos, rutas, números y errores. Cambia con `/ultracave` (máxima compresión) o `/megacave` (chino clásico); desactiva con `stop caveman` o `normal mode` solo si el usuario lo pide. Herramientas MCP: `caveman_compress`, `caveman_stats`, `caveman_toon_encode/decode`.

<details>
<summary><strong>Catálogo completo: 92 skills</strong></summary>

### Proceso, calidad y colaboración

| Skill | Para qué sirve |
|---|---|
| `brainstorming` | Explora el problema, requisitos y alternativas antes de crear; convierte una idea vaga en un diseño acordado. |
| `writing-plans` | Convierte una spec en un plan paso a paso con archivos, interfaces, verificación y commits. |
| `executing-plans` | Ejecuta un plan en la sesión actual, tarea por tarea, con checkpoints y verificación. |
| `subagent-driven-development` | Reparte tareas independientes a subagentes y revisa su trabajo antes de integrarlo. |
| `dispatching-parallel-agents` | Lanza varios agentes en paralelo para tareas sin dependencias ni estado compartido. |
| `systematic-debugging` | Diagnostica bugs con hipótesis y evidencia antes de proponer o tocar código. |
| `test-driven-development` | Escribe primero el test que falla y luego la implementación mínima. |
| `verification-before-completion` | Verifica con comandos reales antes de declarar que algo está listo o arreglado. |
| `requesting-code-review` | Prepara el trabajo para revisión con contexto, criterios y evidencia. |
| `receiving-code-review` | Procesa feedback de revisión con rigor, sin aceptar sugerencias a ciegas. |
| `finishing-a-development-branch` | Decide merge, PR, limpieza y cierre de una rama de desarrollo. |
| `using-git-worktrees` | Aísla el trabajo en worktrees de git para no mezclar cambios. |
| `writing-skills` | Crea o edita skills con estructura, disparadores y verificación. |
| `using-superpowers` | Regla base: invocar los skills relevantes antes de responder o actuar. |
| `diagnosing-superpowers` | Investiga por qué una sesión de Superpowers falló o se atascó. |

### Diseño, UI y visual

| Skill | Para qué sirve |
|---|---|
| `apple-design` | Audita UI/UX con las HIG de Apple y criterio de craft para Tauri, Electron, iOS o Android. |
| `frontend-design` | Da dirección visual distintiva a una UI nueva o a un rediseño, sin caer en plantillas. |
| `impeccable` | Diseña, rediseña, audita o pule interfaces: jerarquía, tipo, color, motion y accesibilidad. |
| `unslop` | Quita el look genérico de IA y convierte una pantalla en una interfaz con carácter. |
| `logo-design` | Diseña logos y marcas: brief, conceptos, SVG, pruebas y variantes de entrega. |
| `anatomy` | Crea figuras isométricas SVG interactivas que explican un sistema o componente. |
| `fun-isometric` | Genera stickers isométricos animados con presets de motion estilo Lottie. |
| `pixelfx` | Crea efectos pixel art y sprite sheets con 244 efectos listos y un loop de refinamiento. |
| `react-bits` | Añade componentes React animados de React Bits a un proyecto. |

### Video, media y sonido

| Skill | Para qué sirve |
|---|---|
| `hyperframes` | Produce o edita videos con HTML: launch films, explainers, charts, captions y overlays. |
| `hyperframes-cli` | CLI de HyperFrames: scaffold, preview, render, share e historial de proyecto. |
| `hyperframes-registry` | Unos 450 bloques y componentes HyperFrames listos para usar como fuente editable. |
| `media-use` | Consigue o genera música, SFX, imágenes, voz, video y transcripts para HyperFrames. |
| `reverse-any-video` | Reconstruye un video existente como proyecto HyperFrames editable, frame a frame. |
| `style-sampling` | Haz un episodio nuevo en un estilo de video probado (collage, finance, science, 3D). |
| `youtube` | Extrae transcript, metadata y comentarios de YouTube y los guarda en el vault. |
| `podcast` | Extrae metadata, transcript y resumen de un podcast y los guarda en el vault. |

### Investigación y conocimiento

| Skill | Para qué sirve |
|---|---|
| `research` | Investiga en web con citas: Perplexity si hay key, o fuentes gratuitas si no. |
| `research-deep` | Investigación profunda vault-first: detecta gaps, sintetiza y propaga al vault. |
| `notebooklm` | Investigación grounded con Gemini File Search, sin navegador. |
| `codebase-map` | Mapea un repo: arquitectura, flujos, archivos clave y preguntas abiertas. |
| `x-pulse` | Escanea X para ver tendencias, voces y hooks sobre un tema. |
| `x-read` | Lee a fondo un post o hilo de X: claims, sentimiento y voces a seguir. |
| `idea-discovery` | Propone 3-5 direcciones siguientes leyendo ideas y notas huérfanas del vault. |
| `vault-deep-synthesis` | Cruza todo lo que el vault sabe de un tema: acuerdos, contradicciones y gaps. |

### Obsidian / segundo cerebro

| Skill | Para qué sirve |
|---|---|
| `obsidian-architect` | Documenta un codebase en notas de arquitectura dentro del vault. |
| `obsidian-board` | Muestra o actualiza un tablero kanban y marca vencidos. |
| `obsidian-board-hygiene` | Triaje masivo del tablero: archiva, reprograma o marca hecho. |
| `obsidian-brainstorm` | Brainstorm socrático multi-turno que termina en una nota de diseño. |
| `obsidian-capture` | Captura rápida de ideas al vault y a la nota diaria. |
| `obsidian-catchup` | Procesa capturas del bot de Telegram: voz, texto, imágenes, PDFs y links. |
| `obsidian-challenge` | Red-team de una idea contra el historial del vault. |
| `obsidian-checkin` | Revisa notas viejas de personas y proyectos y actualiza lo que ya no aplica. |
| `obsidian-connect` | Conecta dos dominios no relacionados usando el grafo del vault. |
| `obsidian-core` | Motor compartido de los skills Obsidian; solo soporte, no se invoca. |
| `obsidian-daily` | Crea o actualiza la nota diaria con calendario, tareas y contexto. |
| `obsidian-decide` | Registra decisiones: ligero en la nota del proyecto o ADR formal. |
| `obsidian-distill` | Condensa una nota o fuente en claims con procedencia. |
| `obsidian-emerge` | Detecta patrones y temas no nombrados en notas recientes. |
| `obsidian-export` | Exporta el vault a JSON, índice markdown o bundle OKF. |
| `obsidian-find` | Busca en el vault y devuelve resultados con contexto. |
| `obsidian-graduate` | Promueve una idea a spec de proyecto con tareas y tablero. |
| `obsidian-health` | Chequeo de salud del vault: contradicciones, gaps y notas viejas. |
| `obsidian-ingest` | Ingesta una fuente o carpeta por lotes, actualizando entidades y conceptos. |
| `obsidian-init` | Escanea el vault y genera `_CLAUDE.md`, `index.md` y `log.md`. |
| `obsidian-learn` | Revisa y poda aprendizajes del vault; muestra patrones activos. |
| `obsidian-log` | Registra una sesión de trabajo o dev en el vault. |
| `obsidian-merge` | Fusiona notas casi duplicadas y redirige la retirada. |
| `obsidian-panel` | Convoca un panel de perspectivas independientes sobre una decisión. |
| `obsidian-person` | Crea o actualiza una nota de persona desde la conversación. |
| `obsidian-project` | Crea o actualiza una nota de proyecto y la añade al tablero. |
| `obsidian-projects` | Estado de proyectos desde git y docs locales, sin config. |
| `obsidian-recap` | Resume hoy, semana o mes desde el vault. |
| `obsidian-reconcile` | Encuentra y resuelve contradicciones en el vault. |
| `obsidian-recurring` | Sigue obligaciones recurrentes con cadencia y próxima fecha. |
| `obsidian-reindex` | Reconstruye el índice semántico del vault y reporta cobertura. |
| `obsidian-retrieval-eval` | Mide recall@k y MRR de la búsqueda del vault. |
| `obsidian-review` | Genera una revisión semanal o mensual desde el historial. |
| `obsidian-save` | Guarda en el vault lo que valga la pena de la conversación. |
| `obsidian-synthesize` | Síntesis automática: detecta patrones y escribe páginas nuevas. |
| `obsidian-task` | Añade una tarea al tablero con prioridad y fecha inferidas. |
| `obsidian-visualize` | Genera un canvas visual del vault y sus conexiones. |
| `obsidian-world` | Carga identidad, valores, prioridades y estado actual en un solo paso. |
| `create-command` | Crea un comando de obsidian-second-brain mediante entrevista. |
| `crew` | Comparte un logbook de carpeta entre Claude Code, Codex, Cursor y Grok. |

### Caveman / ahorro de tokens (default)

| Skill | Para qué sirve |
|---|---|
| `caveman` | Voz telegráfica por defecto: respuesta corta, sin fluff, hechos técnicos intactos. |
| `ultracave` | Compresión máxima: fragmentos, una palabra si basta, cada hecho una vez. |
| `megacave` | Variante en chino clásico (文言文), términos técnicos verbatim. |
| `caveman-commit` | Mensaje Conventional Commit comprimido a intención. |
| `caveman-review` | Review comprimido: una línea por hallazgo con ubicación, problema y fix. |
| `caveman-compress` | Comprime archivos de memoria (CLAUDE.md, todos) y deja backup. |
| `caveman-help` | Tarjeta de referencia de comandos y modos de Caveman. |
| `caveman-stats` | Uso de tokens de la sesión y reporte nativo del host. |
| `cavecrew` | Delega a subagentes investigator/builder/reviewer con salida comprimida. |

### Plataformas y utilidades

| Skill | Para qué sirve |
|---|---|
| `opencode` | Todo sobre OpenCode: config, agentes, skills, plugins, SDK y troubleshooting. |
| `expo` | Crea y opera apps Expo/React Native por proyecto, sin Expo global. |
| `report` | Reporta un bug de OpenCode con diagnóstico y GitHub CLI. |

</details>
<!-- SKILLS-CATALOG:END -->
