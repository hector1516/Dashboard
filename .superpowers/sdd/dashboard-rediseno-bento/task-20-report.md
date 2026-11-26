# Task 20 — La casa en el ancla del clima y legibilidad de las fotos

**Estado:** hecho, commit local. Sin push ni despliegue.

**Fecha:** 2026-11-26

**App:** `Dashboard` (kiosco 1920×1080), rama `main`.

## 1 · La casa ECCSA en el ancla del clima

| Archivo | Cambio |
|---|---|
| `static/images/casa-eccsa.jpg` | el original del dueño (2000×1493, fondo blanco). Se versiona tal cual. |
| `static/images/casa-eccsa.webp` | **nuevo**: la misma ilustración recortada a WebP con alfa (1400 px de ancho, 358 KB), derivada del JPG. |
| `src/lib/components/pantallas/bento/Clima.svelte` | el ancla 2×2 deja la marca de agua y la foto de reportes; pinta la casa y su luz. |
| `src/lib/rediseno/Celda.svelte` | se retira la prop `marcaAgua` (quedó sin uso) y se ajusta la legibilidad sobre foto (ver §2). |

**Cómo se recortó.** El blanco del JPG no se puede quitar con CSS: con
`mix-blend-mode: multiply` sobre la tinta el muro se volvía barro y, metido en
un contenedor con `z-index`, el blanco dejaba de fundirse y aparecía el
rectángulo claro. Se generó un recorte con alfa: relleno por inundación desde
el borde para quitar el blanco, y borde con alfa proporcional a cuán claro es
el píxel, para que no quede halo. El resultado se apoya directo sobre la
tinta, a color, sin velo ni parche.

**Cómo se colocó.**

- La casa ocupa la **mitad derecha**, 57 % del ancho de la celda, apoyada al
  pie y recortada por el borde derecho e inferior (`right: -3%`,
  `bottom: -8%`).
- `mask-image` funde el borde izquierdo (transparente → opaco hasta el 50 %)
  para que la cifra y el texto sigan sobre tinta limpia.
- Detrás va una luz cálida en `radial-gradient` (máximo 40 % de alfa) que la
  despega del fondo sin lavar la tinta.
- No lleva la foto de los reportes: dos imágenes en la misma celda se
  estorban. Las otras 7 anclas siguen con su foto.

## 2 · Legibilidad sobre las fotos de fondo

- **Velo:** se mantiene el del tono de cada celda (tinta 80→84 %, naranja
  86→84 %, azul 86→89 %, informativa 90→88 %). Está por encima del 65–70 %
  que pedía el dueño y conserva el color. No se subió más: con las medidas de
  abajo no hace falta y apagaría la foto.
- **Sombra:** las anclas con foto llevan `text-shadow` corto y heredado
  (tinta y azul, negra; naranja, cálida) para separar el dato de la textura.
- **El ancla naranja es el caso límite.** Ahí el texto va en tinta y la
  translucidez cuesta contraste: la tinta al 82 % sobre la naranja plana da
  4.8:1, y una zona oscura de la foto la bajaba a **3.78:1**. Sobre foto, el
  rótulo, el `.sub` y el `.delta` de esa celda van **opacos** (la jerarquía la
  da el tamaño); así el peor caso queda en 4.5:1 o más en todo el rango de la
  foto, de negro a blanco.

**Medición real** (no estimada): se ocultó el texto, se tomó el píxel más
claro y el más oscuro de la caja de cada elemento, y se comparó contra su
color efectivo (color × opacidad compuesta). Se repitió forzando una foto
blanca, que es el peor caso:

| Pantalla | Tono | Peor contraste, foto real | Peor contraste, foto blanca |
|---|---|---|---|
| Clima | tinta + casa | 5.69:1 (`.lbl`) | igual (no lleva foto) |
| Asistencia | tinta | 8.01:1 (`.sub`) | 11.37:1 |
| Comprobantes | naranja | 4.65:1 (`.cifra`) | 6.13:1 |
| Combustible | azul | 5.43:1 (`.sub`) | 6.28:1 |

## Verificación

- `npm run check` → **7 errores, 50 avisos** (baseline exacto; ninguno en los
  archivos tocados).
- `npm run build` → `Wrote site to "build"`.
- Capturas 1920×1080 (Playwright/Chromium contra `build/` servido en
  `localhost:5184`, snapshot **real** de producción y los 30 thumbs reales):
  - `capturas/t20-clima-casa.png` — el ancla del clima con la casa.
  - `capturas/t20-ancla-tinta.png` — Asistencia (velo tinta).
  - `capturas/t20-ancla-naranja.png` — Comprobantes (velo naranja).
  - `capturas/t20-ancla-azul.png` — Combustible (velo azul).

## Desvíos y notas

- **La marca de agua ya no existe**: `Celda` perdió la prop `marcaAgua` y su
  `::before` (nadie más la usaba). `static/images/oficina-eccsa.webp` sigue en
  el repo porque la usa `OficinaIsometrica.svelte`.
- **La sombra de contacto del dibujo se conserva** dentro del WebP: sobre la
  tinta se lee como luz ambiental en la base, no como manchón. Quitarla
  arrastraba la banqueta del dibujo (probado).
- **El ancla del clima ya no rota la foto de los reportes.** Es la única de las
  8 que no la lleva; si el dueño la quiere de vuelta, van las dos imágenes y
  habría que decidir cuál manda.
- La medición usa la caja real de los glifos (`Range`), no la del bloque: con
  la caja del bloque, un texto corto como «Nublado» medía contra la casa y
  daba un falso 1.67:1.
