# Task 13 · Clima con marca de agua y fondo/transiciones sin parpadeo

**Estado:** hecho, sin push ni despliegue.
**Fecha:** 2026-11-25
**App:** `Dashboard` (kiosco), commit local sobre `main`.

## 1 · Clima: dibujo isométrico de marca de agua

`src/lib/components/pantallas/bento/Clima.svelte` → la celda ancla 2×2
(`area="1/1/3/3" tono="dark"`) ahora pasa
`marcaAgua="/images/oficina-eccsa.webp"`.

`src/lib/rediseno/Celda.svelte` ganó una prop opcional `marcaAgua` (URL):

- pinta la imagen con `::before` y `z-index: -1` dentro de un
  `isolation: isolate` en la celda: la marca va **encima del fondo de la celda
  y debajo del rótulo, la cifra y el texto** (el número sigue por delante);
- `background-size: cover` / `center bottom`: cubre el ancho y se apoya al pie;
- `opacity: 0.10` (rango pedido 0.10–0.14), con `mask-image` que la desvanece
  hacia arriba (transparente al 0 %, opaca al 58 %) para que no compita con la
  temperatura;
- sobre la tinta oscura el dibujo se pasa a gris y se aclara
  (`filter: grayscale(1) brightness(2.2) contrast(0.9)`): así se lee como marca
  de agua clara y no como una foto de ladrillo;
- **si la imagen no carga no pasa nada**: es un `background-image`, falla en
  silencio y la celda queda legible (no hay `<img>` roto ni `onerror`);
- `pointer-events: none`.

Evidencia: `capturas/clima.png` (1920×1080, `?pantalla=clima`).

## 2 · Fondo y transiciones sin parpadeo

| Archivo | Cambio |
|---|---|
| `src/routes/+page.svelte` | `:global(html)` y `:global(body)` pasan de `#020617` a **`#e9ecf1`** (el `--k-base` del bento). Deja de asomarse el azul al arrancar, al recargar y entre pantallas. |
| `src/routes/+page.svelte` | `.escenario` gana la clase `fondo-claro` (solo con pantalla bento) con `background: #e9ecf1`: es lo que queda detrás cuando `.pantalla-caja` se funde. En `?clasico=1` no se aplica, así el Fondo (la foto) de las pantallas viejas sigue viéndose como siempre. |
| `src/routes/+page.svelte` | Bloque de carga a fondo claro: `.cargando-texto` en `#12141a`, `.cargando` y `.cargando-sub` en grises de tinta (`rgba(18,20,26,.62/.55)`). `.sin-pantalla` al mismo criterio. |
| `src/lib/components/SwarmRebuild.svelte` | El lavado del overlay era `rgba(15,23,42,…)` fijo (azul noche): **era un destello oscuro** sobre el bento claro. Ahora recibe `fondo` y `tinta` por props (por defecto `#E9ECF1`/`#12141A`) y se pinta con `rgba()` derivado; los bordes de los elementos construidos usan tinta al 12 % y el texto tipado, tinta. |
| `src/routes/+page.svelte` | A `SwarmRebuild` se le pasan `#E9ECF1`/`#12141A` en bento y `#0F172A`/`#F1F5F9` en `?clasico=1` (el modo viejo no cambia de aspecto). |
| `src/app.html` | `theme-color` de `#0F172A` a `#E9ECF1`. |
| `src/lib/components/effects/LogoTraceLoader.svelte` | La etiqueta «Cargando…» pasa de `#94a3b8` (gris de fondo oscuro) a tinta al 60 %. |

`.pantalla-caja` conserva su fundido de 0.4 s (`opacity` + `scale`/`translate`):
ahora el relevo se lee como un fundido suave sobre `#e9ecf1` porque el color de
debajo es el mismo de las pantallas.

`.negro` (apagado 00:00–06:00) sigue negro a propósito: no es un fondo de
transición.

Evidencias: `capturas/carga.png` (recarga real con la API colgada, logo y texto
en claro), `capturas/transicion-fundido.png` (fotograma a mitad del cambio) y
`capturas/swarm.png` (overlay SwarmRebuild ya en claro).

### Comprobación de que no hay fotograma oscuro

Barrido de 26 capturas cada 100 ms alrededor del cambio de pantalla (44.0 s →
46.5 s) midiendo la luminancia de un píxel del área de contenido:

```
44.0–45.3 s  20    (pantalla actual)
45.4 s      160    (fundido a la base)
45.5–45.7 s 232-236 (#e9ecf1 puro)
45.8 s      196    (entra la pantalla nueva)
45.9–46.5 s  20    (pantalla nueva)
```

Nunca baja del valor de la pantalla que se está yendo: no hay fotograma del
azul `#020617` ni del Fondo oscuro.

## 3 · Verificación

- `npm run check` → **7 errores, 50 avisos** (los 7 errores son el baseline:
  `animejs` sin default export, `avatarTransform`/`estado` en el avatar,
  `v.vehiculo`/`v.total_tickets` en Combustible y `tk.id_ticket`; ninguno en los
  archivos tocados).
- `npm run build` → OK, `Wrote site to "build"`.
- Capturas 1920×1080 con Playwright (Chromium) contra el `build/` servido en
  local con un mock de `/api/*` (esta máquina no tiene el backend ni la BD):
  - `?pantalla=clima` → `capturas/clima.png`
  - recarga real con `/api/dashboard/snapshot` sin responder (el estado
    `.cargando` se mantiene) → `capturas/carga.png`
  - Para la foto de la carga se neutralizó **solo** el `setTimeout` de 2500 ms
    que esconde el logo (`LogoTraceLoader`): la captura tarda más que eso.
    El estado fotografiado es el de una recarga real, no un montaje.

## 4 · Dudas / notas

- El brief decía que `.escenario` tenía `background: #020617`; en el código el
  azul estaba en `:global(body)`. Se cambió el `body`/`html` y, además, se le
  dio base clara a `.escenario` en bento (que es lo que evita el destello en el
  fundido).
- El `Fondo` (foto + clima animado) sigue montado y animándose aunque en bento
  quede tapado por el `Marco` opaco. No se quitó: es el mismo componente que
  usa `?clasico=1` y sacarlo cambia el orden de capas. Queda como candidato de
  rendimiento, fuera de este encargo.
- `?clasico=1` no cambia de aspecto (body claro solo se vería si la foto del
  Fondo fallara; el `.fondo` tiene su propio `#0F172A`).
