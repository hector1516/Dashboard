# Task 15 · Sonidos de transición/Volt y entrada animada de todos los objetos

**Estado:** hecho, sin push ni despliegue.
**Fecha:** 2026-11-25
**App:** `Dashboard` (kiosco 1920×1080), commit local sobre `main`.

## A · Dos tonos nuevos y sus conexiones

`src/lib/kiosk/audio.ts`:

| Tono | Cómo suena | Volumen relativo |
|---|---|---|
| `transicion` | pad grave que sube de **110 → 164.81 Hz** en 0.22 s (más un sub de 55 → 82.41 Hz en triangle, 0.24 s) | 0.05 + 0.02 = **≤ 0.07** |
| `volt` | dos notas cortas y amables **659.25 → 880 Hz**, 0.08 s cada una | 0.055 y 0.05 = **≤ 0.06** |

No hay arpegio ni nota aguda en `transicion`: es un deslizamiento exponencial de
frecuencia (un pad), pensado para oírse cada 45 s sin cansar. Se añadió el helper
`pad()` junto a `nota()`; `nota()` no se tocó.

**Dónde suenan:**

- `src/routes/+page.svelte`
  - `avanzar()` (la rotación) → `tonoTransicion()`.
  - `irAPantalla()` (cambio forzado por el panel remoto) → `tonoTransicion()`.
  - `tonoTransicion()` es el throttling: **máximo un pad cada 3 s**
    (`MS_ENTRE_TRANSICIONES = 3000`, contra `Date.now()`), así que un cambio
    forzado encima de otro no encadena sonidos. Un arranque con `?pantalla=…`
    no suena: esa ruta no llama a ninguna de las dos funciones.
- `src/lib/components/VoltComentario.svelte`
  - dentro de `hablar()`, justo después de `mascotState.set('speaking')` →
    `tocar('volt')`. Suena cada vez que Volt dice algo (incluido el primer
    saludo a los 4 s de arrancar).

**Mudo y horario nocturno:** las dos llamadas pasan por `tocar()`, que es la
misma puerta de antes y **no se modificó**:

```ts
export function tocar(tono: Tono) {
    if (silenciado || enHorarioSilencioso()) return;
```

Ningún tono nuevo crea osciladores por su cuenta, así que si el kiosco está
silenciado (persistido en `localStorage`) o son las 22:00–07:00, no suena nada.
También pasa por `desbloquear()` y el master gain, igual que el resto.

## B · Animación de todos los objetos al cambiar de pantalla

Nuevo `src/lib/rediseno/anim.css`, importado **una vez** al final de los imports
de `+page.svelte`. Actúa sobre las clases que ya existen, sin tocar los
`.svelte` de las 9 pantallas:

| Qué | Selectores | Animación |
|---|---|---|
| Filas de listas | `.lista`, `.movs`, `.estaciones`, `.rank-lista`, `.pers` → hijos | `k-entra`: `translateY(10px)` + opacidad, **360 ms** |
| Series (columnas) | `.barras`, `.dias` → hijos | `k-entra`, mismo escalonado |
| Caras | `.caras` → hijos | `k-entra` |
| Barras verticales | `.bbar`, `.dbar`, `.mini24 i` | `k-barra-y`: `scaleY(0) → 1`, `transform-origin: bottom`, 360–420 ms |
| Barras horizontales | `.est-pista i`, `.pista i` | `k-barra-x`: `scaleX(0) → 1`, origen izquierda, 420 ms |
| Fotos | `.cara img`, `.ava img`, `.thumb img`, `.auto-foto img`, `.escena .fondo` | `k-foto`: `scale(.94) → 1`, 420–450 ms |
| Chips del marco | `.marco .top .chip` | `k-chip`: `translateY(-6px)` + opacidad, 320 ms |

- Escalonado por `:nth-child`, **38 ms** entre hermanos hasta 10 (0, 38, 76…
  342 ms). Las 24 barras del histograma también se escalonan hasta 10.
- Easing de salida `cubic-bezier(.22,.8,.28,1)`, `both`, sin animaciones
  infinitas.
- **Las cifras no se tocan**: `<Numero>` ya cuenta. El archivo no tiene ninguna
  regla para `.cifra`.
- Sólo `transform` y `opacity`: ni `position` ni nada de layout.

**Apagado:** `+page.svelte` pone `class:sin-anim={sinAnim}` en `.escenario`
(`?sinanim=1`). En `anim.css`, `.sin-anim *` (y `::before`/`::after`) deja
`animation: none !important`, y `@media (prefers-reduced-motion: reduce)` hace lo
mismo sobre `.escenario *`. Eso apaga también el `caer` de las celdas: una
captura y una persona con sensibilidad al movimiento quieren el estado final
quieto, no una versión rápida de la fiesta.

## Verificación

- `npm run check` → **7 errores, 50 avisos**, exactamente el baseline; ninguno
  en los archivos tocados.
- `npm run build` → `Wrote site to "build"`.
- Capturas 1920×1080 (Playwright/Chromium contra `build/` + mock de `/api/*`):
  - `capturas/t15-combustible.png` — normal (foto del auto, barras, chips).
  - `capturas/t15-combustible-sinanim.png` — `?sinanim=1&pantalla=combustible`.
  - `capturas/t15-asistencia.png` — normal, para las filas de la lista.
- Comprobado en el DOM con `getComputedStyle`:
  - `.bento .lista .fila` → `k-entra` 0.36 s, retardos `0 / 0.038 / 0.076 s`
    (escalonado real, no todas a la vez).
  - `.bento .bcol .bbar` → `k-barra-y` 0.42 s, retardo 0.09 s.
  - `.bento .est-pista i` → `k-barra-x` 0.42 s, retardo 0.12 s.
  - `.bento .auto-foto img` → `k-foto` 0.42 s.
  - `.marco .top .chip` → `k-chip` 0.32 s.
  - Con `?sinanim=1` los cinco devuelven `animationName: none`.
- **La medición no cambia:** las cajas de `.bento`, `.bento .cell` y
  `.bento .bcol` son idénticas con animación y con `?sinanim=1`
  (`[0,76,1920,962]`, `[32,100,916,601]`, `[1000,477,84,201]` en ambos).
- Audio: no se puede oír en headless. Queda verificado por tipos, build y por la
  ruta de código, no por oído.

## Dudas / notas

- El pad `transicion` también suena en un cambio forzado (panel remoto); el
  throttle de 3 s es justo lo que evita que tres cambios seguidos lo encadenen.
- Las reglas están acotadas a `.bento` / `.marco`, así que las pantallas de
  `?clasico=1` y la banda de alertas no cambian de comportamiento.
- `.sin-anim *` apaga además el `caer` de `Celda` y `Portada`: es intencional
  para capturas; en operación normal no se activa.
- El escalonado se corta en 10 hermanos; una lista de 20 (Legends en `Equipo`)
  entra con las 10 primeras escalonadas y el resto con el último retardo. Se
  prefirió eso a que la lista tarde casi un segundo en terminar.

## Fix round 1

1. **Hermanos 11+ con retardo.** El shorthand resetea `animation-delay` a 0 y
   sólo había `:nth-child(1..10)`, así que la fila 11 entraba antes que la 2.
   Se añadió `:nth-child(n + 11) { animation-delay: 342ms; }` para
   `.bento :is(...) > *`, `.dias > .dcol` y `.mini24 > i`. Verificado en el DOM:
   `.mini24 i:nth-child(11)` y `:nth-child(24)` → `0.342s`; el criterio se
   aplica igual a las 20 filas de Legends (`.r-fila`).
2. **Volt ya no suena cada 11–19 s.** `hablar(t, r, importante = false)`: el
   tono sólo se dispara cuando el texto es un aviso nuevo del vigilante, la
   pérdida/regreso de internet o una presencia (`importante = true`), nunca en
   la charla de relleno. Además `tonoVolt()` limita a **una vez cada 60 s**
   (`MS_ENTRE_VOCES`) aunque lleguen varios avisos seguidos. Sigue pasando por
   `tocar()`, así que mudo y 22:00–07:00 siguen mandando.
3. **`.dias` acotado.** La serie de Actividad ahora es `.bento .dias > .dcol`
   (base y retardos). El badge de «3 días» de Comprobantes ya no se anima:
   medido en el DOM, `.bento .dias` y su `<span>` dan `animationName: none`,
   mientras `.bento .fila` sigue en `k-entra`.
4. **Sin `transform` permanente.** Los keyframes `k-barra-y` / `k-barra-x`
   terminan en `transform: none` y las animaciones usan `backwards` en vez de
   `both`: al acabar, la animación deja de aplicarse y el elemento vuelve a su
   `transform` natural. Medido después de la cascada: `.bbar`,
   `.mini24 i:nth-child(11)` y `.mini24 i:nth-child(24)` →
   `transform: none` (antes quedaba `matrix(1,0,0,1,0,0)`, que mantiene el
   stacking context).
5. **Comentario del import corregido.** Ya no afirma que importar al final haga
   ganar reglas: explica que `anim.css` es global, que los estilos `scoped`
   llevan el hash y desempatan, y que el archivo sólo añade animaciones que
   ninguna pantalla declara.

**Verificación del round:**

- `npm run check` → **7 errores, 50 avisos** (baseline).
- `npm run build` → `Wrote site to "build"`.
- Capturas regeneradas esperando a que la pantalla monte y a que la cascada
  termine (selector `.bento .cell` + **2 s**; en headless la hidratación tarda
  ~2–3 s y la espera fija de 2.2 s anterior cazaba un fotograma a media
  entrada): `capturas/t15-combustible.png` (normal),
  `capturas/t15-combustible-sinanim.png` (`?sinanim=1`) y
  `capturas/t15-asistencia.png`. Las cajas siguen idénticas con y sin
  animación (`[0,76,1920,962]`, `[32,100,916,601]`, `[1000,477,84,201]`).
- Filas: `k-entra` con retardos `0 / 0.038 / 0.076 s`. Con `?sinanim=1`, las
  cinco medidas devuelven `animationName: none`.
