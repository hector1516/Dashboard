# Task 17 · Globo de Volt sólo con notificaciones

**Estado:** hecho, sin push ni despliegue.

**Fecha:** 2026-11-26

**App:** `Dashboard` (kiosco 1920×1080), commit local sobre `main`.

Antes el globo estaba **siempre montado** arriba de la placa y hablaba cada
11–19 s con charla de relleno (idle, entrada, salida, comentarios de pantalla).
Ahora sólo existe en el DOM mientras hay algo que notificar, se queda ~11 s y se
va con fundido. Sin notificación no hay globo ni texto.

## Archivos

| Archivo | Cambio |
|---|---|
| `src/lib/components/VoltComentario.svelte` | reescrito: sin charla aleatoria; `{#if visible}` + `fade` de salida; temporizador único de ocultar |
| `src/routes/+layout.svelte` | sólo el comentario que describía «comentarios aleatorios» |

## Cómo se comporta

- **Cuándo aparece** (en este orden de prioridad, un aviso por sondeo):
  1. **Aviso nuevo** del vigilante: `avisos` con `id` mayor que el último visto.
     Si llegan varios de golpe, sale el último; el resto se marca como visto
     (no se repite la historia en cadena).
  2. **Internet de vuelta**: el sondeo anterior decía `sin_internet` y el actual
     no.
  3. **Sin internet**: el sondeo actual dice `sin_internet` y el anterior no
     (o es el primero tras montar). No se repite mientras siga caído.
- **Cuánto dura:** `10_500 + random < 1_500` ms → entre 10.5 y 12 s. Al
  ocultarse no queda nada montado (`{#if visible}`) y el fundido de salida es
  `fade` de 240 ms; la entrada conserva `entraComentario` (0.4 s) y el fundido
  del texto.
- **Sondeo:** `/api/dashboard/volt` cada 60 s (`cache: 'no-store'`), más un
  sondeo inmediato al montar y al evento `online`/`offline` del navegador.
- **Memoria:** el último `id` visto se guarda en `localStorage`
  (`volt:ultimoAviso`). En el primer arranque de un kiosco sin clave se toma el
  id más alto como visto y no se cuentan los avisos viejos.
- **Muñeco:** `pauseWalking()` + `mascotState.set('speaking')` al mostrarse;
  `mascotState.set('idle')` + `resumeWalking()` al ocultarse (y en `onDestroy`
  si se desmonta visible).
- **Sonido:** `tocar('volt')` sólo dentro de `mostrar()`, con el throttle de
  60 s que ya tenía (`MS_ENTRE_VOCES`). Nada de tono por charla.
- **Sin cambios:** estilo translúcido (`rgba(255,255,255,.72)` + blur), avatar,
  flecha y posición fija `right:18px; bottom:142px` encima de la placa.
- **Fuera:** `siguiente()`, la lista `tipos` (`idle`, `entrada`, `salida`,
  `usuario_nuevo`, `usuario_inactivo`), `REACCIONES`, `getVoltComentario`,
  `getVoltComentarioPantalla` y el import de `currentScreen`. El único
  temporizador que queda es el de ocultar.

## Verificación

- `npm run check` → **7 errores, 50 avisos** (baseline exacto).
- `npm run build` → `Wrote site to "build"`.
- DOM real con Playwright/Chromium (1920×1080) contra `build/`, snapshot del
  mock del task 14 (`kiosco-mock14.mjs`) y `/api/dashboard/volt` interceptado
  para mover avisos e internet a voluntad:

| Comprobación | Resultado |
|---|---|
| Al montar (2.5 s después) | `.volt-comentario` = **0** |
| Llega aviso `id 6` | = **1**, texto `⚠️ Reporte R-2481 firmado por Héctor` |
| A los 12.5 s | = **0** |
| A los 21 s, sin novedad | = **0** (no vuelve solo) |
| Otro sondeo sin novedad | = **0** |
| `localStorage['volt:ultimoAviso']` | `"6"` |
| Recarga completa | = **0** (la historia no se repite) |
| `sin_internet: true` | = **1**, `📡 Sin internet por aquí…` |
| Se oculta y sigue sin red | = **0**, y otro sondeo = **0** (no repite) |
| Vuelve la red | = **1**, `🌐 ¡Volvió el internet!…` |
| `pageerror` | ninguno |

- Capturas (`capturas/`):
  - `t17-volt-aviso.png` — globo visible con el aviso, arriba de la placa.
  - `t17-volt-oculto.png` — el mismo instante tras los 12 s, sin globo.

## Notas

- El **pie** del marco (`PieVolt`, p. ej. «— Volt: El gasto va bien…») es otra
  pieza: no es el globo ni charla aleatoria, es una frase fija calculada por
  pantalla y se dejó intacta. Si el dueño también quiere el pie sin frase, es un
  cambio en cada pantalla (`Marco`/`PieVolt`), no en este componente.
- Mientras el globo está visible y llega otra notificación, el texto se
  reemplaza y el temporizador de ocultar se reinicia: nunca hay dos globos ni
  cola que lo deje fijo.
