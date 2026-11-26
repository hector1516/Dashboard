# Task 18 · El globo de Volt avisa entradas/salidas y tickets nuevos

**Estado:** hecho, sin push ni despliegue.

**Fecha:** 2026-11-26

**App:** `Dashboard` (kiosco 1920×1080), commit local sobre `main`.

El globo ya no vive sólo de `/api/dashboard/volt`. Los eventos que el kiosco
recibe por el snapshot también dejan una frase corta en Volt: una línea, la
misma mecánica de mostrar/ocultar del task 17 y el mismo throttle de sonido.

## Archivos

| Archivo | Cambio |
|---|---|
| `src/lib/kiosk/voltAviso.ts` | nuevo: store `voltAviso` + `decirVolt(texto, reaccion = '💬')` |
| `src/routes/+page.svelte` | `anunciar(e)`: presencia (`titulo === 'Entró' \| 'Salió'`) y `titulo` que empieza con `Ticket` llaman a `decirVolt` |
| `src/lib/components/VoltComentario.svelte` | se suscribe a `voltAviso`, muestra el mensaje con `mostrar()` y vacía el buzón |

## Cómo se comporta

- **Presencia** (`nivel:'pantalla'`, `titulo:'Entró' | 'Salió'`):
  - entró → `<persona> entró de la oficina.` con `👋`
  - salió → `<persona> salió de la oficina.` con `🚪`
  - Se decide por `e.titulo === 'Entró'`, no por el texto suelto.
- **Ticket** (`titulo:'Ticket <folio>'`): `Ticket nuevo de <persona>: <texto>.`
  con `🎫`. El aviso a pantalla completa que ya existía no se toca: el globo es
  un extra, no un segundo takeover.
- **Duración:** la del task 17, `10_500 + random < 1_500` ms (10.5–12 s); se va
  con `fade` y no queda montado. Una notificación nueva reemplaza el texto y
  reinicia el temporizador, nunca hay dos globos ni cola.
- **Sonido:** `mostrar()` sigue llamando a `tocar('volt')` con el throttle de
  60 s (`MS_ENTRE_VOCES`). Los tonos de los eventos (`tocar(e.tono ?? e.nivel)`)
  no cambian.
- **Buzón:** al consumir un mensaje el store vuelve a `null`; una recarga no
  repite la última frase. El suscriptor se da de baja en el `onDestroy` del
  `onMount`.

## Verificación

- `npm run check` → **7 errores, 50 avisos** (baseline exacto; los 7 son los
  conocidos de `animejs`, aritmética de `app/api`, `VehiculoKm.vehiculo`,
  `total_tickets` e `id_ticket`).
- `npm run build` → `Wrote site to "build"`.
- DOM real con `vite dev` (:5180) + Edge headless por CDP, leyendo
  `.comentario-texto`:

| Comprobación | Resultado |
|---|---|
| `?aviso=presencia` a los ~3 s | `Priscila Urbina entró de la oficina.` (`👋`) |
| Presencia a los ~14.5 s | `.comentario-texto` = **null** (se fue solo) |
| `?aviso=ticket` a los ~3.5 s | `Ticket nuevo de Ricardo Barajas: Kia Rio 21 · SAJ-721-D.` (`🎫`) |
| Ticket a los ~14 s | `null` |
| `decirVolt('Prueba desde consola.', '💬')` importando el store | globo visible a los 1.5 s |
| Cronología de presencia | aparece 3.1 s, el aviso de pantalla completa termina 13.5 s, globo oculto 14.5 s (~11.4 s visible) |

- Sin errores nuevos del globo. El log del dev server muestra uno **preexistente**:
  `Unknown state "happy"` desde `VoltNotificacion.svelte:35` al abrir un aviso a
  pantalla completa (`?aviso=presencia|ticket`); no lo introdujo este cambio y no
  impide que el globo aparezca y se oculte.

## Notas

- No se duplicó nada: la toma de pantalla completa y la banda siguen igual; el
  globo sólo añade la frase corta.
- El `?aviso=km|firmado` no habla por el globo (sólo presencia y ticket), como
  pedía el alcance.
