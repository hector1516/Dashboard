# Task 19 — Foto de los reportes como fondo del ancla 2×2

**Estado:** hecho, commit local. Sin push ni despliegue.

**Fecha:** 2026-11-26

**App:** `Dashboard` (kiosco 1920×1080), rama `main`.

El ancla de cada pantalla bento pinta una foto de los reportes de servicio por
detrás del contenido, con un velo del tono de la celda. Las fotos se precargan
UNA vez y las rota un solo temporizador global: cambiar de pantalla no reinicia
el índice, no vuelve a bajar nada y no interrumpe el ciclo.

## Archivos

| Archivo | Cambio |
|---|---|
| `src/lib/rediseno/fotosFondo.ts` | **nuevo**: stores `fotosFondo` y `fotoActual`; `cargarFotos(urls)` idempotente: precarga con `new Image()`, arranca un único `setInterval` de 8 s |
| `src/lib/rediseno/Celda.svelte` | prop `fondo?: boolean`: `<img>` absoluta (`object-fit: cover`), velo por tono, fundido con `{#key}` + `fade`, `z-index: -2` con el `isolation` de la celda, `pointer-events: none`; sin fundido con `prefers-reduced-motion` |
| `src/routes/+page.svelte` | `cargarFotos(d.fotos?.rutas ?? [])` en `refrescar()` (cada snapshot; la función es idempotente) |
| `src/lib/kiosk/types.ts`, `src/lib/kiosk/api.ts` | `fotos.rutas?: string[]` y `rutas: []` en el snapshot vacío |
| `bento/Actividad, Asistencia, Clima, Combustible, Comprobantes, Equipo, Tickets, UsoApps` | `fondo` en la `<Celda area="1/1/3/3">` |

## Cómo se comporta

- **Precarga única.** La primera lista se precarga completa con `new Image()`
  (sin `await`, sin handler de error: una foto rota se ignora). Con la misma
  lista no se repite: ni red, ni índice, ni timer.
- **Rotación global.** Un solo `setInterval` de 8000 ms avanza `indice` en bucle
  y publica en `fotoActual`. Los componentes solo se suscriben: al desmontarse
  una pantalla el timer sigue vivo, así el cambio no se reinicia ni parpadea.
- **Cambio de lista** (entró un reporte): se rearma con índice 0 y se reutiliza
  el mismo timer.
- **Lista vacía** o snapshot sin `fotos.rutas`: no arranca nada y el ancla queda
  con su color plano.
- **Foto detrás del contenido.** `z-index: -2` dentro del `isolation` de la
  celda; la marca de agua del Clima (`::before`, `-1`) sigue encima de la foto y
  el contenido, por delante. `pointer-events: none`: no roba clics ni
  selección.
- **Legibilidad.** Velo del tono de la celda (`dark` tinta .80→.84, `red`
  naranja .86→.84, `azul` azul oscurecido .86→.89, informativa blanca .90→.88)
  y el rótulo del ancla sube a `.82` cuando hay foto. Medido sobre el peor caso
  (foto blanca): cifra y `.sub` muy por encima de 4.5:1; el `.delta` al 60 %
  queda en 4.8:1 (tinta) y 5.1:1 (azul). El naranja queda en 4.3:1 para ese
  terciario, igual que ya estaba sobre el color plano.

## Verificación

- `npm run check` → **7 errores, 50 avisos** (baseline exacto).
- `npm run build` → `Wrote site to "build"`.
- `build/` servido en `localhost:5184` con el snapshot y los 30 thumbs reales
  (29 archivos: el snapshot repite una ruta), Edge headless por Playwright,
  1920×1080. Cambio de pantalla con el mismo mecanismo que la rotación (comando
  `ver` del panel remoto), sin recargar el documento:

| Comprobación | Resultado |
|---|---|
| Precarga inicial | **29 peticiones** a `/media/thumbs` (29 únicas) |
| Avance automático (~8 s) | `rep_55_3_w960.jpg` → `rep_106_2_w960.jpg`; peticiones siguen en **29** |
| Cambio a Combustible en la misma página | `src` antes = `src` después (`rep_106_2_w960.jpg`); `navigation` sigue en 1; marca `window` intacta; **29** peticiones |
| Rotación en la pantalla nueva | avanza sola a `rep_109_2_w960.jpg`; **29** peticiones |
| Volver a Actividad (ya vista) | `src` sigue en `rep_109_2_w960.jpg` (no reinicia); **29** peticiones, **0 nuevas** |

Capturas: `.superpowers/sdd/dashboard-rediseno-bento/capturas/t19-actividad.png`,
`t19-combustible.png` y `t19-comprobantes.png` (tonos tinta, azul y naranja).

## Desvío

- **Portada** no tiene ancla 2×2: su única celda 4×3 YA es una foto a sangre
  (la imagen del mes). Se deja como está; ponerle la foto de reportes debajo
  taparía el contenido de la portada. Son 8 anclas, no 9.
- Los 30 `rutas` del snapshot apuntan a 29 archivos distintos: una foto se
  repite. No es un fallo del cambio; la precarga deduplica por caché del
  navegador.
