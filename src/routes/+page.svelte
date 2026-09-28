/*
	Kiosco — orquestador.

	Aquí viven los relojes y las decisiones, no las pantallas:
	  · rotación de 10 pantallas cada 45 s, en orden aleatorio y sin repetir
	    consecutively,
	  · refresco del snapshot cada 30 s (la BD se actualiza cada 2 min; 30 s
	    es suficiente y no martilla al servidor),
	  · alertas: dedup, niveles, antispam y la pausa de la rotación cuando
	    algo se toma la pantalla,
	  · apagado de 00:00 a 06:00 y modo noche de 23:00 a 06:00,
	  · recarga automática cuando el build del contenedor cambia,
	  · anti-quemado: desplazamiento periódico de ±2 px.

	El audio lo inicializa el navegador con `--autoplay-policy`, pero también
	se despierta con el primer gesto por si el kiosco se abre a mano.
*/
<script lang="ts">
import { onMount, onDestroy } from 'svelte';
import { cargarSnapshot, pedirBuild, snapshotVacio } from '$lib/kiosk/api';
import type { EventoKiosko, PantallaDef, Snapshot } from '$lib/kiosk/types';
import { esLluvioso, esNublado, esSoleado, haceCuanto, nombreDia, nombreMes } from '$lib/kiosk/format';
import {
	initAudio, tocar, apagar, setVolumen, getVolumen, estaSilenciado,
	audioBloqueado, desbloquear, ambienteClima, detenerAmbiente
} from '$lib/kiosk/audio';
import { montarConfeti, redimensionar, degradar, lanzarConfeti, lanzarOro, pararConfeti, fpsActual } from '$lib/kiosk/fx';
import { APP_VERSION, SHELL_VERSION } from '$lib/shell.js';

import Fondo from '$lib/components/Fondo.svelte';
import HdrKiosco from '$lib/components/HdrKiosco.svelte';
import CapaAlertas from '$lib/components/CapaAlertas.svelte';
import Combustible from '$lib/components/pantallas/Combustible.svelte';
import Legends from '$lib/components/pantallas/Legends.svelte';
import Reportes from '$lib/components/pantallas/Reportes.svelte';
import Tickets from '$lib/components/pantallas/Tickets.svelte';
import Notas from '$lib/components/pantallas/Notas.svelte';
import Celebraciones from '$lib/components/pantallas/Celebraciones.svelte';
import Fotos from '$lib/components/pantallas/Fotos.svelte';
import Metricas from '$lib/components/pantallas/Metricas.svelte';
import Clima from '$lib/components/pantallas/Clima.svelte';
import Pulso from '$lib/components/pantallas/Pulso.svelte';

/* ── Configuración de la pantalla ─────────────────────────────── */
const ROTACION_MS = 45_000;      // 45 s por pantalla
const REFRESCO_MS = 30_000;      // pedir el snapshot
const SHELL_MS = 60_000;         // preguntar por versión del build
const MAX_BANDAS = 3;            // avisos simultáneos abajo
const COOLDOWN_DESTAQUE_MS = 180_000;  // 1 toma de pantalla cada 3 min
const APAGADO_DESDE = 0;         // 00:00
const APAGADO_HASTA = 6;         // 06:00
const NOCHE_DESDE = 23;          // modo noche (brillo) desde las 23
const TICK_EVENTO_MS = 20_000;   // cuánto vive una banda

/**
 * Las 10 pantallas. "pulso" entra dos veces por vuelta: es el latido de fondo
 * y si apareciera una vez cada 3 minutos se olvidaría.
 */
const PANTALLAS: PantallaDef[] = [
	{ id: 'pulso', icono: '⚡', label: 'La Oficina Ahora' },
	{ id: 'combustible', icono: '⛽', label: 'Combustible' },
	{ id: 'legends', icono: '🏆', label: 'ECCSA Legends' },
	{ id: 'reportes', icono: '📊', label: 'Reportes' },
	{ id: 'tickets', icono: '🎫', label: 'Tickets' },
	{ id: 'celebraciones', icono: '🎂', label: 'Cumpleaños' },
	{ id: 'metricas', icono: '📈', label: 'Métricas' },
	{ id: 'fotos', icono: '📸', label: 'Fotografías' },
	{ id: 'clima', icono: '🌤️', label: 'Clima' },
	{ id: 'notas', icono: '📌', label: 'Notas' }
];

/* ── Estado ───────────────────────────────────────────────────── */
let datos = $state<Snapshot>(snapshotVacio());
let cargando = $state(true);
let orden = $state<number[]>([]);
let pos = $state(0);
let saliendo = $state(false);
let reloj = $state('');
let fecha = $state('');
let apagado = $state(false);
let modoNoche = $state(false);
let modoLigero = $state(false);
let antiguedad = $state('—');
let silenciado = $state(false);
let volumen = $state(0.35);
let bloqueado = $state(false);
let shellEstado = $state<'idle' | 'syncing' | 'pending' | 'offline' | 'error'>('idle');
let sinAnim = $state(false);
let shellUsuario = $state<string | null>(null);

let banda = $state<EventoKiosko[]>([]);
let toast = $state<EventoKiosko | null>(null);
let toma = $state<EventoKiosko | null>(null);
let vistos = new Set<string>();
let primerCarga = true;
let ultimoDestaque = 0;
let ultimoGanador = '';

let fondoRef = $state<any>(null);
let canvasRef: HTMLCanvasElement | null = null;
let escenarioRef: HTMLDivElement | null = null;
let timers: any[] = [];

/**
 * Escala del escenario fijo: el diseño mide 1920×1080 y se escala al viewport
 * con el mismo factor en X y Y (letterbox si no coincide la relación). Es lo
 * que hace que la pantalla se vea IGUAL en cualquier TV y que nunca aparezca
 * scroll, en vez de depender de vh/rem como antes.
 */
function escalar() {
	if (!escenarioRef) return;
	// k = 1 en una ventana de 1920×1080 exacta; menor si la pantalla es más
	// chica (letterbox) o más grande (se aprovecha todo). Probar con "el
	// viewport dividido entre 100" daba 45 en vez de 1: el escenario se iba
	// 45× hacia arriba y la captura salía negra.
	const k = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
	escenarioRef.style.setProperty('--k-escala', String(k));
}

/* ── Derivados ────────────────────────────────────────────────── */
const pantalla = $derived(PANTALLAS[orden[pos] ?? 0] ?? PANTALLAS[0]);
const periodo = $derived(periodoDelDia());
const clima = $derived(datos.clima?.actual);
const origenBuena = $derived(clima?.temperatura != null);

function periodoDelDia(): 'dawn' | 'day' | 'dusk' | 'night' {
	const h = new Date().getHours();
	if (h >= 5 && h < 7) return 'dawn';
	if (h >= 7 && h < 17) return 'day';
	if (h >= 17 && h < 19) return 'dusk';
	return 'night';
}

/** ¿Ahora mismo debe estar la pantalla en negro? (00:00–06:00) */
function debeApagarse(): boolean {
	const h = new Date().getHours();
	return h >= APAGADO_DESDE && h < APAGADO_HASTA;
}

/* ── Reloj ────────────────────────────────────────────────────── */
function tickReloj() {
	const now = new Date();
	reloj = now.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
	fecha = `${nombreDia(now)}, ${now.getDate()} de ${nombreMes(now).toLowerCase()} de ${now.getFullYear()}`;
	antiguedad = haceCuanto(datos.generado_en);
	const h = now.getHours();
	apagado = debeApagarse();
	modoNoche = h >= NOCHE_DESDE || h < 6;
}

/* ── Datos ────────────────────────────────────────────────────── */
async function refrescar() {
	try {
		const { datos: d, viaApi } = await cargarSnapshot();
		datos = d;
		if (viaApi) shellEstado = 'idle';
		procesarEventos(d.eventos ?? []);
		chequearClima(d);
		chequearCelebraciones(d);
	} catch {
		// Sin red ni backend: se conserva el snapshot anterior. La pantalla
		// sigue mostrando lo último bueno y el header lo dice.
		shellEstado = 'error';
	}
	if (primerCarga) {
		primerCarga = false;
		cargando = false;
	}
}

/** Clima → ambiente sonoro + efectos visuales. */
function chequearClima(d: Snapshot) {
	const a = d.clima?.actual;
	if (!a) return;
	ambienteClima(a.codigo_clima ?? 0, !!a.es_dia);
}

/* ── Alertas ──────────────────────────────────────────────────── */
function procesarEventos(eventos: EventoKiosko[]) {
	if (!eventos?.length) return;

	// Al arrancar no se reproducen los 100 del historial: la pantalla saludaría
	// a la oficina con 100 avisos de golpe. Solo se anotan como vistos.
	if (primerCarga) {
		eventos.forEach((e) => vistos.add(e.id));
		return;
	}

	for (const e of eventos) {
		if (vistos.has(e.id)) continue;
		vistos.add(e.id);
		anunciar(e);
	}
	// El set crece sin límite en una pantalla que dura semanas.
	if (vistos.size > 500) vistos = new Set([...vistos].slice(-300));
}

function anunciar(e: EventoKiosko) {
	tocar(e.nivel);

	if (e.nivel === 'destaque' && e.segundos) {
		const ahora = Date.now();
		if (ahora - ultimoDestaque > COOLDOWN_DESTAQUE_MS) {
			ultimoDestaque = ahora;
			toma = e;
			timers.push(setTimeout(() => (toma = null), e.segundos * 1000));
			return;
		}
		// Con el cooldown activo el evento se degrada a banda: se sigue viendo
		// aunque no se robe la pantalla.
	}

	if (e.nivel === 'exito') {
		toast = e;
		timers.push(setTimeout(() => (toast = null), 6000));
		return;
	}

	banda = [e, ...banda].slice(0, MAX_BANDAS);
	timers.push(
		setTimeout(() => {
			banda = banda.filter((x) => x.id !== e.id);
		}, TICK_EVENTO_MS)
	);
}

/** Confeti cuando hay un cumpleaños hoy o cambia el ganador de Legends. */
function chequearCelebraciones(d: Snapshot) {
	const hayCumple = (d.cumpleanos?.hoy?.length ?? 0) > 0;
	const ganador = d.legends?.ranking?.[0]?.nombre ?? '';
	if (primerCarga) {
		ultimoGanador = ganador;
		return;
	}
	if (hayCumple) lanzarConfeti(130);
	else if (ganador && ultimoGanador && ganador !== ultimoGanador) lanzarOro(110);
	if (ganador) ultimoGanador = ganador;
}

/* ── Rotación ─────────────────────────────────────────────────── */
function barajar(): number[] {
	const a = PANTALLAS.map((_, i) => i);
	for (let i = a.length - 1; i > 0; i--) {
		const j = Math.floor(Math.random() * (i + 1));
		[a[i], a[j]] = [a[j], a[i]];
	}
	return a;
}

function avanzar() {
	// Una toma de pantalla en curso manda: no se cambia lo que se está leyendo.
	if (toma) return;
	saliendo = true;
	setTimeout(() => {
		pos = (pos + 1) % orden.length;
		if (pos === 0) orden = barajar();   // vuelta nueva, orden nuevo
		saliendo = false;
		// Fondo nuevo en cada giro (aleatorio de los locales).
		if (fondoRef?.cambiarFondo && datos.fondos.length) {
			fondoRef.cambiarFondo(Math.floor(Math.random() * datos.fondos.length), 1600);
		}
	}, 520);
}

/* ── Anti-quemado: la TV se presta el píxel ───────────────────── */
let antiQuemado = 0;
function moverAntiQuemado() {
	antiQuemado = antiQuemado === 0 ? 1 : antiQuemado === 1 ? 2 : antiQuemado === 2 ? 3 : 0;
}

/* ── Modo ligero si la pantalla no da ────────────────────────── */
let chequeoFps = 0;
function medirFps() {
	chequeoFps++;
	if (chequeoFps % 10 !== 0) return;
	const fps = fpsActual();
	const nuevo = fps < 40;
	if (nuevo !== modoLigero) {
		modoLigero = nuevo;
		degradar(nuevo);
	}
}

/* ── Shell: estado de salud para el banner del ECCSA-Shell ───── */
async function leerShell() {
	try {
		const r = await fetch('/api/shell/state', { cache: 'no-store' });
		if (!r.ok) return;
		const j = await r.json();
		shellUsuario = j?.user?.nombre ?? null;
		if (j?.sync?.estado) shellEstado = j.sync.estado;
	} catch {
		shellEstado = 'error';
	}
}

/* ── Recarga por versión ──────────────────────────────────────── */
async function vigilarBuild() {
	const b = await pedirBuild();
	if (!b) return;
	if (datos.build && b !== datos.build) {
		// El contenedor se reconstruyó: la pantalla se recarga sola. Sin esto
		// un hotsync no se ve hasta que alguien reinicie Edge a mano.
		location.reload();
	}
}

/* ── Ciclo de vida ────────────────────────────────────────────── */
/** Parámetros de URL: para probar una pantalla puntual sin esperar 45 s.
 *  `?pantalla=legends` deja esa pantalla fija; `?sinrotacion=1` quita el giro.
 *  Es el modo que usan las pruebas y el soporte en vivo: enseñar una pantalla
 *  concreta sin esperar a que le toque el turno. */
function leerParams() {
	if (typeof location === 'undefined') return null;
	const q = new URLSearchParams(location.search);
	// OJO: se leen TODOS los parámetros; no hay return temprano. Con
	// `?pantalla=legends&sinanim=1` el `sinanim` se ignoraba (el `if` de
	// pantalla salía antes) y las capturas salían a medio camino de las
	// animaciones de entrada, lo que hacía parecer que faltaban tarjetas.
	const id = q.get('pantalla');
	const congelar = !!(id && PANTALLAS.some((p) => p.id === id));
	const out: { fija: number | null; sinAnim: boolean; debug: boolean } = {
		// `null` = la pantalla queda fija donde esté (para capturar o revisar).
		fija: congelar ? PANTALLAS.findIndex((p) => p.id === id) : null,
		sinAnim: q.get('sinanim') === '1',
		debug: q.get('debug') === '1'
	};
	// `?sinrotacion=1` o `?sinanim=1` sin `pantalla=`: congela en la primera.
	if (!congelar && (q.get('sinrotacion') === '1' || q.get('sinanim') === '1')) {
		out.fija = 0;
	}
	return out;
}

const params = leerParams();

onMount(() => {
	orden = barajar();
	if (params?.fija !== null && params?.fija !== undefined) {
		orden = [params.fija];
		pos = 0;
	}
	initAudio();
	silenciado = estaSilenciado();
	volumen = getVolumen();
	bloqueado = audioBloqueado();

	if (canvasRef) montarConfeti(canvasRef);
	escalar();
	window.addEventListener('resize', redimensionar);
	window.addEventListener('resize', escalar);
	// Panic-mute: cualquier tecla o clic corta el sonido.
	window.addEventListener('keydown', alTeclar);
	window.addEventListener('pointerdown', alTocar);

	tickReloj();
	refrescar();
	leerShell();

	// ?sinanim=1: sin animaciones de entrada (capturas y revisión de diseño).
	sinAnim = params?.sinAnim === true;
	if (params?.debug) setTimeout(dibujarDebug, 1500);

	const tReloj = setInterval(tickReloj, 1000);
	const tDatos = setInterval(refrescar, REFRESCO_MS);
	// Con ?pantalla=... la pantalla queda fija (no gira): es el modo de prueba.
	const tGiro = params?.fija !== null && params?.fija !== undefined ? null : setInterval(avanzar, ROTACION_MS);
	const tShell = setInterval(leerShell, 60_000);
	const tBuild = setInterval(vigilarBuild, SHELL_MS);
	const tAnti = setInterval(moverAntiQuemado, 4 * 60 * 1000);
	const tFps = setInterval(medirFps, 1000);
	timers.push(tReloj, tDatos, tShell, tBuild, tAnti, tFps);
	if (tGiro) timers.push(tGiro);

	const onVis = () => {
		if (!document.hidden) {
			tickReloj();
			refrescar();
		}
	};
	document.addEventListener('visibilitychange', onVis);
	timers.push(() => document.removeEventListener('visibilitychange', onVis));
});

onDestroy(() => {
	timers.forEach((t) => (typeof t === 'function' ? t() : clearInterval(t)));
	window.removeEventListener('resize', redimensionar);
	window.removeEventListener('resize', escalar);
	window.removeEventListener('keydown', alTeclar);
	window.removeEventListener('pointerdown', alTocar);
	detenerAmbiente();
	pararConfeti();
});

/**
 * ?debug=1 — vuelca la geometría de la pantalla actual.
 *
 * Existe porque dos veces un layout se ve mal y no se sabe por qué desde el
 * código: el navegador es el único que sabe el ancho real de cada caja. Con
 * esto el `docker exec ... --dump-dom` deja los números en el HTML y se
 * revisan sin adivinar.
 */
function dibujarDebug() {
	const area = document.querySelector('.area');
	const out: string[] = [];
	const caja = (sel: string, etiqueta: string) => {
		const els = Array.from(document.querySelectorAll(sel));
		if (!els.length) { out.push(`${etiqueta}: (ninguno)`); return; }
		const e = els[0] as HTMLElement;
		out.push(
			`${etiqueta}: ${els.length} · ${Math.round(e.offsetWidth)}x${Math.round(e.offsetHeight)}` +
			` @ ${Math.round(e.offsetLeft)},${Math.round(e.offsetTop)}` +
			` · col=${getComputedStyle(e).gridTemplateColumns || '-'}`
		);
	};
	out.push(`viewport: ${window.innerWidth}x${window.innerHeight} · k=${(document.querySelector('.escenario') as HTMLElement)?.style.getPropertyValue('--k-escala')}`);
	caja('.area', 'area');
	caja('.screen', 'screen');
	caja('.kpis', 'kpis');
	caja('.kpi', 'kpi');
	caja('.cuerpo', 'cuerpo');
	caja('.col-izq', 'col-izq');
	caja('.flota', 'flota');
	caja('.veh', 'veh');
	caja('.barras', 'barras');
	caja('.spark-box', 'spark');
	caja('.podio', 'podio');
	caja('.tarjeta', 'tarjeta');
	caja('.heat', 'heat');
	caja('.rejilla', 'rejilla');
	caja('.tkt', 'tkt');
	caja('.reporte', 'reporte');
	caja('.celeb-grid, .rejilla.r-xl, .rejilla.r-md', 'celebraciones');
	const pre = document.createElement('pre');
	pre.id = 'debug-kiosco';
	pre.style.cssText = 'position:fixed;left:8px;bottom:40px;z-index:9999;font:12px monospace;color:#0f0;background:#000c;padding:8px;white-space:pre';
	pre.textContent = out.join('\n');
	area?.appendChild(pre);
}

function alTeclar() {
	desbloquear();
	bloqueado = audioBloqueado();
}
function alTocar() {
	desbloquear();
	bloqueado = audioBloqueado();
}

function alternarSilencio() {
	const nuevo = apagar();
	silenciado = nuevo;
	tocar('click');
}
function cambiarVolumen(v: number) {
	setVolumen(v);
	volumen = getVolumen();
}
</script>

<svelte:head>
	<title>Centro de Operaciones ECCSA</title>
	<meta name="robots" content="noindex, nofollow" />
</svelte:head>

<!--
	El banner `.sync-header` del ECCSA-Shell NO se monta acá, y es a propósito:
	es un botón de sincronización de una app con sesión y usuario, y el kiosco
	no tiene ninguno (docs/CONTRATO.md §2b). Lo que sí se cumple es el
	contrato: `GET /api/shell/state` existe y responde, y la versión de app y de
	shell se ven en el pie de la pantalla, que es donde sirven en un TV.
-->

<!-- Apagado nocturno: negro absoluto, sin canvas ni animaciones -->
{#if apagado}
	<div class="negro"></div>
{:else}
	<div
		class="kiosco"
		class:modo-noche={modoNoche}
		class:modo-ligero={modoLigero}
		class:sin-anim={sinAnim}
		style="--anti:{antiQuemado}px"
	>
		<Fondo
			bind:this={fondoRef}
			fondos={datos.fondos ?? []}
			{periodo}
			lluvioso={esLluvioso(clima?.codigo_clima ?? 0)}
			soleado={esSoleado(clima?.codigo_clima ?? 0, clima?.es_dia ?? true)}
			nublado={esNublado(clima?.codigo_clima ?? 0)}
			tenue={modoNoche}
		/>

		<!-- Escenario fijo 1920×1080 escalado al viewport. Determinista. -->
		<div class="escenario" bind:this={escenarioRef}>
			<div class="pantalla-caja" class:saliendo>
				<HdrKiosco
					pantallaIcono={pantalla.icono}
					pantallaLabel={pantalla.label}
					{reloj}
					{fecha}
					posicion={`${Math.min(pos + 1, orden.length)}/${orden.length}`}
					degradado={datos.degradado ?? []}
					generadoEn={datos.generado_en}
					{antiguedad}
					{silenciado}
					{volumen}
					{bloqueado}
					onSilenciar={alternarSilencio}
					onVolumen={cambiarVolumen}
					onAudioDesbloquear={() => { desbloquear(); bloqueado = audioBloqueado(); }}
				/>

				<div class="area">
					{#if cargando}
						<div class="cargando"><div class="spinner"></div><div>Cargando centro de operaciones…</div></div>
					{:else}
						{#key pantalla.id}
							{#if pantalla.id === 'pulso'}<Pulso {datos} />
							{:else if pantalla.id === 'combustible'}<Combustible {datos} />
							{:else if pantalla.id === 'legends'}<Legends {datos} />
							{:else if pantalla.id === 'reportes'}<Reportes {datos} />
							{:else if pantalla.id === 'tickets'}<Tickets {datos} />
							{:else if pantalla.id === 'celebraciones'}<Celebraciones {datos} />
							{:else if pantalla.id === 'metricas'}<Metricas {datos} />
							{:else if pantalla.id === 'fotos'}<Fotos {datos} />
							{:else if pantalla.id === 'clima'}<Clima {datos} />
							{:else if pantalla.id === 'notas'}<Notas {datos} />
							{/if}
						{/key}
					{/if}
				</div>
			</div>

			<!-- Canvas único de confeti, sobre todo lo demás -->
			<canvas class="confeti" bind:this={canvasRef} aria-hidden="true"></canvas>

			<CapaAlertas {banda} {toast} {toma} onCerrarToma={() => (toma = null)} />

			<footer class="pie">
				<span>ECCSA · Centro de Operaciones · v{APP_VERSION} · shell {SHELL_VERSION}</span>
				<span>
					{#if datos.degradado?.length}
						⚠️ {datos.degradado.join(' · ')} · mostrando el último snapshot
					{:else}
						● datos al día
					{/if}
				</span>
			</footer>
		</div>
	</div>
{/if}

<style>
	/* El contenedor real es 1920×1080 y se escala al viewport: la pantalla se
	   ve idéntica en cualquier TV y nunca aparece scroll. */
	:global(body) {
		margin: 0;
		background: #020617;
		font-family: 'Outfit', system-ui, sans-serif;
		overflow: hidden;
		cursor: none;
		user-select: none;
	}
	.kiosco { position: fixed; inset: 0; overflow: hidden; }

	.escenario {
		position: absolute;
		top: 50%;
		left: 50%;
		width: 1920px;
		height: 1080px;
		transform: translate(-50%, -50%) scale(var(--k-escala, 1)) translate(var(--anti), 0);
		transform-origin: center center;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.pantalla-caja { position: relative; flex: 1; min-height: 0; display: flex; flex-direction: column; }
	.pantalla-caja.saliendo { opacity: 0; transform: scale(0.98); transition: all 0.5s ease; }

	.area { position: relative; flex: 1; min-height: 0; }

	/* El confeti cae dentro del área de contenido (debajo del header, encima del
	   pie) y toma el tamaño de esa caja, que es la que le pasa el componente. */
	.confeti { position: absolute; inset: 56px 0 30px 0; width: 100%; height: calc(100% - 86px); pointer-events: none; z-index: 45; }

	.pie {
		display: flex; justify-content: space-between; align-items: center;
		padding: 0 28px; height: 30px; flex-shrink: 0;
		font-size: 12.5px; color: #475569;
		border-top: 1px solid rgba(255,255,255,0.05);
		background: rgba(2,6,23,0.5); z-index: 20;
	}

	.negro { position: fixed; inset: 0; background: #000; z-index: 999; }

	.cargando { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; gap: 16px; color: #475569; }
	.spinner {
		width: 54px; height: 54px; border: 5px solid rgba(255,107,0,0.2);
		border-top-color: var(--color-primary); border-radius: 50%;
		animation: girar 0.8s linear infinite;
	}
	@keyframes girar { to { transform: rotate(360deg); } }
</style>
