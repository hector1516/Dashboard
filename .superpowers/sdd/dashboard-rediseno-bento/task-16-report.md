# Task 16 · Conteo de todos los números del Dashboard

**Estado:** hecho, sin push ni despliegue.
**Fecha:** 2026-11-26
**App:** `Dashboard` (kiosco 1920×1080), commit local sobre `main`.

Antes sólo contaba el ancla (`<Numero>`); las demás cifras —montos, conteos,
puntos, días, porcentajes, grados— aparecían de golpe. Ahora cada pantalla entra
con sus números contando de 0 a su valor.

## Archivos

| Archivo | Cambio |
|---|---|
| `src/lib/rediseno/contar.ts` | **nuevo**: `contarNumeros(raiz, { duracion })` |
| `src/lib/rediseno/Numero.svelte` | `data-numero` en el `<span>` (el barrido lo salta) + tope en 0 para `k` |
| `src/lib/components/CuentaRotacion.svelte` | `data-sin-contar` (cuenta regresiva de 45 s: cambia sola) |
| `src/routes/+page.svelte` | import y `$effect` que barre el escenario al entrar cada pantalla |

## Cómo cuenta

- Recorre los elementos de `raiz` y actúa sobre el que tiene **un solo nodo de
  texto** y ningún hijo con forma de elemento. Los comentarios de Svelte
  (`<!--[-->`, `<!---->`) que envuelven un `{#if}` no cuentan como contenido:
  sin eso, media pantalla quedaba fuera sólo por venir de un bloque
  condicional (medido: «Sin comprobante» y «Saldo Go Vale» no contaban).
- El texto, recortado, tiene que ser un número y nada más:
  `^(\s*)(\$?)(\d+(?:,\d{3})*)(\.\d+)?(\s?(?:°C|°|%))?(\s*)$`.
  Se respeta el formato original: prefijo `$`, comas de miles, decimales y
  sufijo (`%`, `°`, `°C`).
- Anima **el nodo de texto** con un `requestAnimationFrame` compartido: easing
  cúbico, 700 ms, una sola pasada. El último fotograma escribe el **texto
  original** (no un redondeo), así que la cifra termina exacta.
- No toca lo que esté dentro de `[data-numero]` (el ancla) ni de
  `[data-sin-contar]` (relojes y contadores que cambian solos).
- **No cuenta cifras metidas en una frase**: si el padre del elemento tiene
  texto propio alrededor (el «· promedio » de «23 vales · promedio $5,400»,
  con el monto en un `<b>`), se salta. Sin esa regla, el `<b>$5,400</b>` se
  animaba y la frase llegaba a leerse «promedio $32» a media cuenta.
- Se apaga con `prefers-reduced-motion: reduce`, con `.sin-anim` en el
  escenario y con `?sinanim=1` (se mira la URL además de la clase porque el
  efecto puede correr antes de que `+page.svelte` ponga la clase).

En `+page.svelte` el barrido corre en un `$effect` después de `tick()` y de un
`requestAnimationFrame`, con dependencias `pantalla.id`, `cargando` y `sinAnim`:
una vez por pantalla, y sólo cuando ya hay datos que pintar (si no, el primer
barrido caería sobre el esqueleto de carga y no volvería a correr).

## Verificación

- `npm run check` → **7 errores, 50 avisos** (baseline exacto).
- `npm run build` → `Wrote site to "build"`.
- DOM real con Playwright/Chromium contra `build/` y snapshot mockeado
  (muestreo cada 40 ms desde antes de hidratar):

**Combustible** — trayectorias de `.cifra`:

| Cifra | Trayectoria (resumen) | Final |
|---|---|---|
| Sin comprobante | `$0 → $3,489 → … → $19,790` | `$19,800` |
| Saldo Go Vale | `$0 → $2,643 → … → $14,992` | `$15,000` |
| Precio del litro | `$0.00 → $3.08 → … → $17.49` | `$17.50` |
| Ancla (Numero) | `$29,680 → … → $124,209` | `$124,209` |
| «12 h» | sin cambios | `12 h` |

- `.sub` «23 vales · promedio $5,400» → **un solo valor** en todo el muestreo
  (no se anima ni la frase ni el `<b>` del monto).
- `.temp` del marco (`27°`) cuenta `0° → 5° → … → 27°`; es un número, no el
  reloj. `.reloj` (`10:21 a.m.`) y `.fecha` quedan intactos (no casan el
  patrón).
- Con `?sinanim=1`: todas las cifras ya están en su valor final en la primera
  muestra y no cambian.
- Con `prefers-reduced-motion: reduce`: idéntico, valores finales desde la
  primera muestra.
- Cascada intacta en Asistencia: `.bento .lista > .fila` sigue con
  `animationName: k-entra` y retardos `0 / 0.038 / 0.076 / 0.114 s`, mientras
  sus cifras (`4`, `5`, `1`) cuentan.
- Cambio de pantalla por panel remoto simulado (Tickets → Asistencia →
  Combustible): en cada entrada las cifras vuelven a contar desde 0 y terminan
  exactas (`4/5/1` y `$124,209 / $19,800 / $15,000 / $17.50`).
- `pageerror`: ninguno.
- Capturas (`capturas/`):
  - `t16-combustible.png` — normal, tras esperar la animación.
  - `t16-combustible-sinanim.png` — `?sinanim=1`.
  - `t16-cambio-pantalla.png` — rotación tras el segundo cambio.

## Notas

- **`12 h` no cuenta**: el sufijo permitido es `%`, `°` y `°C`; `h`, `km` o
  `días` quedan fuera a propósito. Ampliar el patrón a unidades sueltas
  animaría fragmentos de frases («desde las 08:02»). Si el dueño quiere que la
  hora del pico cuente, el cambio es una línea en `NUMERO` y se revisa el resto.
- **Bug encontrado y corregido:** el `requestAnimationFrame` puede entregar un
  timestamp anterior al `performance.now()` con el que se toma `t0`; el primer
  fotograma pintaba `$-27,952`. Se topó `k` en 0 en `contar.ts` y también en
  `Numero.svelte` (el ancla tenía el mismo fallo).
- Se barre una vez por pantalla: si el snapshot llega después de montar (más
  allá de la carga inicial) y cambia un número en pantalla, ese número no
  vuelve a contar hasta la siguiente entrada. Es lo pedido y evita que el
  refresco de 30 s reinicie las cifras.
- La cuenta de rotación (`.rot`) quedó marcada `data-sin-contar`: cambia cada
  segundo y animarla la haría pelear con su propio contador.
