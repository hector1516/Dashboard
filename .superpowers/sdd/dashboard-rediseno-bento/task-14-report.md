# Task 14 · Paleta del logo y cierre de la revisión 11–13

**Estado:** hecho, sin push ni despliegue.
**Fecha:** 2026-11-25
**App:** `Dashboard` (kiosco), commit local sobre `main`.

## A · Acento de marca naranja + azul

### Tokens

`src/lib/rediseno/tokens.css`:

| Token | Antes | Ahora |
|---|---|---|
| `--k-rojo` | `#e4002b` | **`#f26d26`** (naranja del logo) |
| `--k-azul` | — | **`#27347b`** (azul del logo) |

El nombre del token no cambió (solo el valor y el comentario): el resto del
sistema ya lo consume como «acento».

### Dónde se usa el azul

El brief decía que había `#1b3fa0`/`#2440a8` duros en `bento/`; **no existían**
(solo el `Combustible` clásico, fuera del alcance). Se interpretó «ancla
informativa» y se añadió la variante `.cell.azul` en `Celda.svelte`; las dos
anclas informativas que pedía la revisión pasaron de tinta a azul:

- `bento/Combustible.svelte` → «Gasto del mes» (`tono="azul"`).
- `bento/Equipo.svelte` → «En el equipo» (`tono="azul"`).
- Clima conserva `tono="dark"` para que la marca de agua siga leyéndose sobre
  tinta; Comprobantes usa `red` (alerta) o `dark` (todo al día).

### Contraste (WCAG, calculado)

| Combinación | Ratio | Uso |
|---|---|---|
| tinta `#12141A` sobre naranja `#F26D26` | **6.13:1** | ancla de alerta (texto normal) |
| blanco sobre azul `#27347B` | **11.27:1** | ancla informativa |
| crema `#F7F3EA` sobre azul | **10.18:1** | ancla informativa |
| menta `#7FE3CF` sobre azul | **7.40:1** | delta de Legends |
| salmón `#FF8F9F` sobre azul | **5.20:1** | variación al alza |
| ámbar oscuro `#8A6200` sobre blanco | **5.49:1** | «días» en ámbar |
| naranja `#F26D26` sobre blanco | **3.00:1** | solo cifras ≥20 px bold / 54 px |
| tinta al 62 % sobre blanco | **5.17:1** | textos secundarios |

Cambios de contraste:

- `.cell.red` pasa de `color:#fff` (2.9:1) a `color:var(--k-tinta)`.
- `Comprobantes`: el `.delta` del ancla ya no fuerza `#fff`; hereda tinta.
- `Comprobantes .ambar` (texto de días) pasa de `var(--k-ambar)` (2.45:1) a
  `#8a6200` (5.49:1), el mismo criterio que ya usaba `Actividad`. La barra
  `.pista i.ambar` sigue con `var(--k-ambar)`: ahí es fondo.
- Rótulos `.lbl` sobre naranja/azul suben de `.55` a `.8` (4.64:1 sobre naranja).
- Los textos secundarios que estaban a `opacity:.55` (3.0:1) suben a `.62`
  (5.17:1) en las seis pantallas que los usaban.
- Verde, ámbar y menta siguen siendo semánticos; no se tocaron como colores.

## B · Cierre de la revisión 11–13

1. **Legends completo (critical).** Fuera `TOPE_RANKING` y el «+N más»: la celda
   2×2 pinta las 12 filas del snapshot con sus puntos. Filas flexibles
   (`flex:1 1 0`, 24–44 px) para que 20 integrantes no necesiten scroll.
   Verificado en DOM: `12` filas, `0` elementos `.r-mas`.
2. **Carga en `?clasico=1`.** El bloque `.cargando` gana la clase de modo
   `clasico` cuando no es bento: texto crema con sombra, subtítulo claro y la
   etiqueta del `LogoTraceLoader` en claro (override `:global`). En bento
   conserva tinta. Capturas de ambos modos.
3. **Temperatura entera.** `Clima.svelte::grados()` redondea; la barra del
   `Marco` ya redondeaba. Verificado en DOM: `21°C` en la celda y `21°` en la
   barra; los rangos `26°/13°` y `25°/12°`.
4. **Avatares rodantes.** Cumpleaños y aniversarios usan
   `p.foto ?? p.avatar`; `ProximoCumple` declara `avatar?: string|null`. El
   fixture manda `foto:null` y `avatar` y los círculos lo pintan.
5. **Fechas relativas.** `cuando()` ahora calcula contra `p.fecha` (fecha
   absoluta de la próxima ocurrencia) y, si no viene, contra `dias` + la edad
   de `generado_en`. Si la fecha ya pasó, avanza al mismo día del año
   siguiente. Verificado con un snapshot de hace 3 días: la persona cuyo
   `dias` era `0` dice «en 363 días», no «hoy».
6. **Marca de agua.** `filter: grayscale(1) brightness(0.5) contrast(0.95)` y
   `opacity: .07` (antes `brightness(2.2)` / `.10`, que saturaba los muros y
   parecía foto). Ahora es una silueta de papel al pie de la celda.
7. **Transición.** Crossfade real: `{#key pantalla.id}` con `in:fade`/`out:fade`
   de 420 ms sobre `.capa-pantalla` absolutas; la pantalla saliente se queda
   montada mientras entra la nueva. `?sinanim=1` lo deja en seco. El
   `saliendo`/`setTimeout(520)` anterior desapareció. Evidencia:
   `capturas/cruce-3.20.png` (las dos pantallas superpuestas a mitad del
   cruce).

## Verificación

- `npm run check` → **7 errores, 50 avisos**, el mismo baseline (ninguno en los
  archivos tocados).
- `npm run build` → OK, `Wrote site to "build"`.
- `python -m unittest discover -s tests -v` → **21 tests OK**.
- Capturas 1920×1080 (Playwright/Chromium contra `build/` + mock de `/api/*`):
  - `capturas/t14-comprobantes.png` — ancla naranja, texto en tinta.
  - `capturas/t14-combustible.png` — ancla azul y texto blanco.
  - `capturas/t14-equipo.png` — ancla azul, 12 integrantes, avatares de respaldo.
  - `capturas/t14-clima.png` — marca de agua tenue y temperaturas enteras.
  - `capturas/t14-carga-bento.png` — carga sobre base clara, texto en tinta.
  - `capturas/t14-carga-clasico.png` — carga sobre `Fondo` oscuro, texto claro.
  - `capturas/cruce-3.20.png` — fotograma del crossfade.

## Dudas / notas

- **No había hex azules en `bento/`.** Los únicos `#1b3fa0` están en
  `pantallas/Combustible.svelte` (la pantalla clásica), que no forma parte del
  sistema bento ni estaba en las rutas del encargo; se dejó intacta para no
  cambiar el diseño de marcha atrás. Si se quiere, se tokeniza en otra pasada.
- **Anclas azules:** se aplicaron a Combustible y Equipo, que son las que la
  revisión nombra como «(azul)». El resto de anclas informativas siguen en
  tinta; convertirlas todas es una decisión de diseño, no de contraste.
- La escala de pies y notas por debajo de `.62` (`.45`, `.4`) se dejó como
  jerarquía visual deliberada; no interviene en la paleta de acento.

## Fix round 1

1. **Naranja como texto.** Nuevo token `--k-rojo-texto: #b24d12` (**5.30:1**
   sobre blanco). Lo usan `Comprobantes .rojo` (d�as del vale) y `Equipo
   .hoy`; `--k-rojo` (`#F26D26`) se queda para fondos, barras y subrayados.
   Tambi�n se a�adi� `--k-ambar-texto: #8a6200` (5.49:1) y se usa en
   `Comprobantes .ambar` y `Actividad .estado.medio`.
2. **Datos secundarios a AA.** Suben a `.62` (5.17:1 en claro):
   `Equipo .pos` (.35), `.rank-pie` (.45), `.delta.vacio` (.45) y
   `Clima .rango .min` (.45).
3. **`diasHasta()` con snapshot viejo.** Ahora `espera()` devuelve
   `{ dias, vueltas }`. Con `fecha` rueda al mismo d�a del a�o siguiente; sin
   `fecha` resta la edad del snapshot (`generado_en`) y suma 365 con signo
   (m�dulo 365, hasta 3 vueltas). `anosDe()` suma `vueltas` a los a�os del
   aniversario. Verificado en DOM con snapshot de 3 d�as: sin `fecha` ?
   �en 362 d�as� (antes �en 3 d�as�); aniversario pasado ? �5 a�os � en 363
   d�as� (antes 4).
4. **Legends sin recorte silencioso.** `.rank-lista` pasa a
   `justify-content: flex-start` + `overflow: hidden`; caben 19 filas y, si hay
   m�s, se pintan 18 + �y N m�s� (el resumen ocupa el �ltimo hueco). Con 12 se
   ven los 12; con 25 se ven los 18 primeros y �y 7 m�s�, con el podio intacto.
5. **Menores.** `Celda .cell.azul` usa `var(--k-sup)`; comentario de la marca
   de agua corregido a `brightness(0.5)` / opacidad `0.07`.

Verificaci�n del round: `npm run check` ? 7 errores / 50 avisos (baseline);
`npm run build` ? `Wrote site to "build"`; DOM con 25 integrantes ? 18 filas +
�y 7 m�s�. Capturas: `capturas/fix1-comprobantes.png`,
`capturas/fix1-equipo.png`, `capturas/fix1-clima.png` y
`capturas/fix1-equipo-25.png`.
