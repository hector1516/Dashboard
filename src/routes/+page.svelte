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
import CapaSalida from '$lib/components/CapaSalida.svelte';
import CuentaRotacion from '$lib/components/CuentaRotacion.svelte';
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
import Asistencia from '$lib/components/pantallas/Asistencia.svelte';
import Portada from '$lib/components/pantallas/Portada.svelte';

/* ── Configuración de la pantalla ─────────────────────────────── */
const ROTACION_MS = 45_000;      // 45 s por pantalla
const REFRESCO_MS = 30_000;      // pedir el snapshot
const SHELL_MS = 60_000;         // preguntar por versión del build
const MAX_BANDAS = 3;            // avisos simultáneos abajo
const APAGADO_DESDE = 0;         // 00:00
const APAGADO_HASTA = 6;         // 06:00
const NOCHE_DESDE = 23;          // modo noche (brillo) desde las 23
const TICK_EVENTO_MS = 20_000;   // cuánto vive una banda

/* ── Marca de salida (lun–vie) ─────────────────────────────────
   A las 18:30 la gente se va. Los últimos 10 segundos salen a pantalla
   completa con cuenta regresiva y, al llegar, el 18:30 en números gigantes.
   Es deliberadamente lo más escandaloso del kiosco: en una pantalla de
   pasillo, un aviso discreto no existe. */
const SALIDA_HORA = 18;
const SALIDA_MIN = 30;
const SALIDA_AVISO_S = 10;       // cuenta regresiva de 10 s
const SALIDA_POST_S = 45;        // el cartel de "18:30" dura 45 s

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
	{ id: 'notas', icono: '📌', label: 'Notas' },
	{ id: 'asistencia', icono: '🕘', label: 'Asistencia de hoy' },
	{ id: 'portada', icono: '🖼️', label: 'Portada del mes' }
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

/* Marca de salida: la cuenta regresiva y el cartel de las 18:30. */
let salidaModo = $state<'cuenta' | 'ya' | null>(null);
let salidaSegundos = $state(0);
let salidaSonado = $state<'cuenta' | 'ya' | null>(null);  // para no repetir el bocinazo
let salidaReloj = 0;   // sólo para `?salida=cuenta`: fin de la cuenta forzada

/* Cuenta de rotación: los segundos que le quedan a la pantalla actual. */
let restanteRotacion = $state(ROTACION_MS / 1000);
let t0Rotacion = Date.now();
const HORA_SALIDA = `${String(SALIDA_HORA).padStart(2, '0')}:${String(SALIDA_MIN).padStart(2, '0')}`;

let banda = $state<EventoKiosko[]>([]);
let toast = $state<EventoKiosko | null>(null);
/*
	Los avisos de nivel 'pantalla' van en COLA, no directo: si alguien registra
	3 kilómetros y entran 2 tickets en el mismo ciclo, cuatro pantallas
	completas seguidas son 40 segundos de pasillo sin información. Se muestran uno
	por uno y los que no caben se van de banda, que es lo que se ve sin estorbar.
*/
let colaAviso = $state<EventoKiosko[]>([]);
let aviso = $state<EventoKiosko | null>(null);
const MAX_COLA_PANTALLA = 3;
let vistos = new Set<string>();
let primerCarga = true;
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
	tickSalida(now);

	// Lo que le queda a esta pantalla. Se recalcula contra el reloj y no con
	// un contador que baja, para que si la laptop se duerme o la pestaña queda
	// en segundo plano, al volver muestre el tiempo real que queda.
	restanteRotacion = Math.max(0, (ROTACION_MS - (Date.now() - t0Rotacion)) / 1000);
}

/**
 * Cuenta regresiva de la salida, de lunes a viernes.
 *
 * Se calcula con el reloj LOCAL del navegador, no con una zona horaria fija:
 * la TV de la oficina es la que tiene que estar bien, y si el navegador no
 * supiera la hora (o el reloj se atrasara), el cartel se vería en la hora
 * incorrecta. Además el cálculo es relativo al momento, no a un temporizador
 * acumulado: si la laptop pasa dormida 20 minutos o la pestaña estuvo en
 * segundo plano, al volver se recalcula y no se queda Showing "3" para
 * siempre.
 */
function tickSalida(now: Date) {
	// `?salida=...`: atajo de pruebas. Tiene prioridad sobre el reloj real.
	if (params?.salida) {
		if (params.salida === 'fuera') {
			salidaModo = null;
			return;
		}
		if (params.salida === 'ya') {
			salidaModo = 'ya';
			salidaSegundos = 0;
			return;
		}
		// 'cuenta': 10 segundos reales y luego salta a 'ya', para poder ver las
		// dos fases en una sola captura.
		if (salidaReloj === 0) salidaReloj = now.getTime() + SALIDA_AVISO_S * 1000;
		const quedan = Math.ceil((salidaReloj - now.getTime()) / 1000);
		if (quedan > 0) {
			salidaModo = 'cuenta';
			salidaSegundos = quedan;
		} else {
			salidaModo = 'ya';
			salidaSegundos = 0;
		}
		return;
	}

	// Domingo (0) y sábado (6) no se sale a las 18:30.
	const dia = now.getDay();
	if (dia === 0 || dia === 6) {
		salidaModo = null;
		return;
	}

	const objetivo = new Date(now);
	objetivo.setHours(SALIDA_HORA, SALIDA_MIN, 0, 0);
	const dif = (objetivo.getTime() - now.getTime()) / 1000;

	let modo: 'cuenta' | 'ya' | null = null;
	let segundos = 0;
	if (dif > 0 && dif <= SALIDA_AVISO_S) {
		modo = 'cuenta';
		segundos = Math.ceil(dif);
	} else if (dif <= 0 && dif > -SALIDA_POST_S) {
		modo = 'ya';
	}

	salidaModo = modo;
	salidaSegundos = segundos;

	// El tic de cada segundo y el bocinazo al llegar, sólo al cambiar de
	// estado: si no, la pantalla wouldn't dejar de sonar cada segundo.
	if (modo && modo !== salidaSonado) {
		salidaSonado = modo;
		tocar(modo === 'cuenta' ? 'tic' : 'salida');
	} else if (!modo) {
		salidaSonado = null;
	}
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
	// El evento puede traer su propio tono (p. ej. 'hola'/'adios' de las
	// entradas y salidas); si no, suena el del nivel.
	tocar(e.tono ?? e.nivel);

	// Aviso a pantalla completa: encola y, si no había ninguno en curso, lo saca
	// ya. El sonido va aquí (y no al mostrarlo) para que se oiga en el momento
	// en que llega la noticia, aunque haya que esperar por el que está en
	// pantalla.
	if (e.nivel === 'pantalla') {
		if (colaAviso.length >= MAX_COLA_PANTALLA) {
			// Ya hay tres esperando: este se ve de banda y no se pierde.
			banda = [e, ...banda].slice(0, MAX_BANDAS);
			timers.push(
				setTimeout(() => (banda = banda.filter((x) => x.id !== e.id)), TICK_EVENTO_MS)
			);
			return;
		}
		colaAviso = [...colaAviso, e];
		if (!aviso) sacarSiguienteAviso();
		return;
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

/**
 * Pasa al siguiente aviso de pantalla completa. Se llama al encolarlo y
 * cuando termina el que está en curso, para que la cola sea un carrusel y no
 * un montón de capas apiladas.
 */
function sacarSiguienteAviso() {
	const siguiente = colaAviso[0];
	if (!siguiente) {
		aviso = null;
		return;
	}
	colaAviso = colaAviso.slice(1);
	aviso = siguiente;
	const seg = siguiente.segundos ?? 10;
	timers.push(
		setTimeout(() => {
			aviso = null;
			// Pequeña pausa entre uno y otro para que no se encimen los avisos.
			setTimeout(sacarSiguienteAviso, 500);
		}, seg * 1000)
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
/**
 * Arranca/pausa el giro. Va en funciones y no en un `setInterval` fijo porque
 * el panel remoto lo detiene ("deja esta pantalla quieta") y lo vuelve a
 * arrancar; con el intervalo ya capturado eso no se podía hacer.
 */
let tGiro: any = null;
let pausado = $state(false);

function arrancarGiro() {
	if (tGiro) return;
	tGiro = setInterval(avanzar, ROTACION_MS);
}
function pararGiro() {
	if (tGiro) clearInterval(tGiro);
	tGiro = null;
}
function pausarGiro() {
	pausado = true;
	pararGiro();
}
function seguirGiro() {
	pausado = false;
	// Al reanudar, el contador arranca desde cero: si no, la pantalla
	// cambiaría a los 3 segundos de volver.
	t0Rotacion = Date.now();
	arrancarGiro();
}

function barajar(): number[] {
	const a = PANTALLAS.map((_, i) => i);
	for (let i = a.length - 1; i > 0; i--) {
		const j = Math.floor(Math.random() * (i + 1));
		[a[i], a[j]] = [a[j], a[i]];
	}
	return a;
}

function avanzar() {
	// Un aviso a pantalla completa en curso manda: no se cambia lo que se está
	// leyendo. Y tampoco la marca de salida, que encima se come la pantalla.
	if (aviso || colaAviso.length || salidaModo) return;
	saliendo = true;
	setTimeout(() => {
		pos = (pos + 1) % orden.length;
		// La cuenta de segundos arranca con la pantalla nueva, no con el giro.
		t0Rotacion = Date.now();
		if (pos === 0) orden = barajar();   // vuelta nueva, orden nuevo
		saliendo = false;
		// Fondo nuevo en cada giro (aleatorio de los locales).
		if (fondoRef?.cambiarFondo && datos.fondos.length) {
			fondoRef.cambiarFondo(Math.floor(Math.random() * datos.fondos.length), 1600);
		}
	}, 520);
}

/**
 * Ir a una pantalla concreta y reiniciar el contador. Lo usa el panel remoto
 * ("muéstrame Legends") y también `?pantalla=` al arrancar.
 *
 * El reinicio del contador es la mitad del asunto: sin él, pedir una pantalla
 * a mitad de vuelta dejaría 3 segundos de esa pantalla, que es justo lo que uno
 * NO quiere cuando la pidió para mostrar algo.
 */
function irAPantalla(id: string) {
	const destino = PANTALLAS.findIndex((p) => p.id === id);
	if (destino < 0) return false;
	// La nueva pantalla va al frente de la lista y `pos` se queda en 0: así el
	// resto sigue barajado y no se repite hasta que le toque por orden.
	orden = [destino, ...orden.filter((i) => i !== destino)];
	pos = 0;
	t0Rotacion = Date.now();
	restanteRotacion = ROTACION_MS / 1000;
	saliendo = false;
	return true;
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

/* ── Panel remoto: esta pantalla obedece ──────────────────────── */
const CLAVE_PANEL = 'dashboard:panel:id';

/**
 * La TV se registra en el panel y escucha órdenes.
 *
 * - Al arrancar publica su lista de pantallas, para que el módulo Notas de
 *   Admon pueda dibujar los botones sin duplicar la lista en dos repos.
 * - Avisa que sigue viva (`/latido`) una vez por minuto: Admon lo usa para
 *   decir "la TV está desconectada" en vez de mandar comandos al vacío.
 * - Consulta el comando pendiente cada 3 s y lo aplica. Sin secreto: leer no
 *   mueve nada, lo mueve `POST /api/panel/comando`, que sí lo exige.
 *
 * El `id` del último comando applied se guarda en localStorage para que un
 * reinicio de la página no repita la orden (y para que la misma orden no se
 * aplique dos veces si el poll se solapa).
 */
async function latirPanel() {
	try {
		await fetch('/api/panel/latido', { method: 'POST' });
	} catch {
		// La TV funciona igual sin panel: es una comodidad, no una dependencia.
	}
}

async function publicarPantallas() {
	try {
		await fetch('/api/panel/pantallas', {
			method: 'POST',
			headers: { 'content-type': 'application/json' },
			body: JSON.stringify({
				pantallas: PANTALLAS.map((p) => ({ id: p.id, label: p.label, icono: p.icono }))
			})
		});
	} catch {
		/* sin panel, sin problema */
	}
}

async function obeyecerPanel() {
	let estado: any;
	try {
		const r = await fetch('/api/panel/estado', { cache: 'no-store' });
		if (!r.ok) return;
		estado = await r.json();
	} catch {
		return;
	}
	const cmd = estado?.comando;
	if (!cmd?.id) return;
	let ultimo = 0;
	try {
		ultimo = Number(localStorage.getItem(CLAVE_PANEL) || 0);
	} catch {
		/* localStorage bloqueado: se aplica igual, sólo se repite */
	}
	if (Number(cmd.id) <= ultimo) return;

	switch (cmd.accion) {
		case 'ver':
			irAPantalla(cmd.pantalla);
			break;
		case 'avanzar':
			avanzar();
			break;
		case 'pausa':
			pausarGiro();
			break;
		case 'seguir':
			seguirGiro();
			break;
		default:
			// 'salida' y lo que se agregue: se acepta sin hacer nada, para que
			// un comando nuevo no se quede dando vueltas en el panel.
			break;
	}
	try {
		localStorage.setItem(CLAVE_PANEL, String(cmd.id));
	} catch {
		/* sin localStorage no se recuerda, no pasa nada */
	}
	try {
		await fetch('/api/panel/confirmado', {
			method: 'POST',
			headers: { 'content-type': 'application/json' },
			body: JSON.stringify({ id: cmd.id })
		});
	} catch {
		/* el acuse es cortesía */
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
/** Parámetros de URL admitidos, ya validados. */
interface ParamsUrl {
	/** Índice de la pantalla fija, o null si sigue rotando. */
	fija: number | null;
	sinAnim: boolean;
	debug: boolean;
	/** Fuerza la cuenta de rotación aunque la pantalla esté fija. */
	reloj?: boolean;
	/**
	 * Muestra un aviso de pantalla completo de ejemplo, sin esperar a que
	 * pase: km | ticket | firmado | presencia. Es lo que se usa para
	 * revisar el diseño de los avisos y para capturar cómo se ven.
	 */
	aviso?: 'km' | 'ticket' | 'firmado' | 'presencia';
	replay?: boolean;
	salida?: 'cuenta' | 'ya' | 'fuera';
}

function leerParams(): ParamsUrl | null {
	if (typeof location === 'undefined') return null;
	const q = new URLSearchParams(location.search);
	// OJO: se leen TODOS los parámetros; no hay return temprano. Con
	// `?pantalla=legends&sinanim=1` el `sinanim` se ignoraba (el `if` de
	// pantalla salía antes) y las capturas salían a medio camino de las
	// animaciones de entrada, lo que hacía parecer que faltaban tarjetas.
	const id = q.get('pantalla');
	const congelar = !!(id && PANTALLAS.some((p) => p.id === id));
	const out: ParamsUrl = {
		// `null` = la pantalla queda fija donde esté (para capturar o revisar).
		fija: congelar ? PANTALLAS.findIndex((p) => p.id === id) : null,
		sinAnim: q.get('sinanim') === '1',
		debug: q.get('debug') === '1',
		// `?aviso=km|ticket|firmado|presencia`: un aviso de ejemplo a pantalla
		// completa, para revisarlo sin esperar a que alguien registre algo.
		aviso: (['km', 'ticket', 'firmado', 'presencia'].includes(q.get('aviso') ?? '')
			? q.get('aviso')
			: undefined) as 'km' | 'ticket' | 'firmado' | 'presencia' | undefined,
		// `?reloj=1`: muestra la cuenta de segundos aunque la pantalla esté
		// fija. Se esconde justamente cuando no hay rotación (pantalla anclada
		// por URL), así que sin este atajo no hay forma de revisarla.
		reloj: q.get('reloj') === '1',
		// OJO: sin esta línea `?replay=1` no hacía nada (el campo estaba
		// declarado en el tipo pero nunca se llenaba) y las capturas salían
		// sin aviso, lo que parecía un fallo del snapshot.
		replay: q.get('replay') === '1',
		// `?salida=cuenta` / `?salida=ya` / `?salida=fuera`: fuerza la marca de
		// salida para revisarla y capturarla sin esperar a las 18:30 de un
		// martes. Con 'cuenta' corre de 10 a 1 y se pasa sola a 'ya'.
		salida: (['cuenta', 'ya', 'fuera'].includes(q.get('salida') ?? '')
			? q.get('salida')
			: undefined) as 'cuenta' | 'ya' | 'fuera' | undefined
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

	t0Rotacion = Date.now();
	tickReloj();
	refrescar();
	leerShell();

	// ?sinanim=1: sin animaciones de entrada (capturas y revisión de diseño).
	sinAnim = params?.sinAnim === true;
	if (params?.debug) setTimeout(dibujarDebug, 1500);
	if (params?.replay) setTimeout(replayEventos, 2500);
	if (params?.aviso) setTimeout(() => anunciar(avisoDeEjemplo(params.aviso as string)), 1500);

	const tReloj = setInterval(tickReloj, 1000);
	const tDatos = setInterval(refrescar, REFRESCO_MS);
	// Con ?pantalla=... la pantalla queda fija (no gira): es el modo de prueba.
	// El giro es un interval manejable y no una constante: el panel remoto
	// puede pausarlo y reanudarlo. Con la pantalla anclada por URL no hay giro.
	const anclada = params?.fija !== null && params?.fija !== undefined;
	if (!anclada) arrancarGiro();

	// Panel remoto: registro, latido y escucha de órdenes.
	latirPanel();
	publicarPantallas();
	const tPanel = setInterval(obeyecerPanel, 3_000);
	timers.push(tPanel);
	const tLatido = setInterval(latirPanel, 60_000);
	timers.push(tLatido);
	const tShell = setInterval(leerShell, 60_000);
	const tBuild = setInterval(vigilarBuild, SHELL_MS);
	const tAnti = setInterval(moverAntiQuemado, 4 * 60 * 1000);
	const tFps = setInterval(medirFps, 1000);
	timers.push(tReloj, tDatos, tShell, tBuild, tAnti, tFps);
	if (tGiro) timers.push(() => clearInterval(tGiro));

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
/** Avisos de ejemplo para `?aviso=…`. Mismos datos que los de verdad, para que
 *  al revisar el diseño se vea exactamente lo que se verá en la TV. */
function avisoDeEjemplo(cual: string): EventoKiosko {
	const base = { id: `ejemplo:${cual}:${Date.now()}`, nivel: 'pantalla' as const, segundos: 10 };
	if (cual === 'presencia') {
		return {
			...base,
			tono: 'hola',
			icono: '👋',
			modulo: 'Red de la oficina',
			titulo: 'Entró',
			persona: 'Priscila Urbina',
			texto: 'iPhone Priscila',
			meta: 'entró a la oficina',
			ts: new Date().toISOString()
		};
	}
	if (cual === 'firmado') {
		return {
			...base,
			tono: 'aviso',
			icono: '✍️',
			modulo: 'Field · Reportes',
			titulo: 'Reporte firmado',
			persona: 'Víctor Jerónimo',
			texto: 'RS-00050 · Papeles y Conversiones de México',
			meta: 'firmado por el cliente',
			ts: new Date().toISOString()
		};
	}
	if (cual === 'ticket') {
		return {
			...base,
			tono: 'aviso',
			icono: '🎫',
			modulo: 'HUB · OxxoGas',
			titulo: 'Ticket 324745780',
			persona: 'Ricardo Barajas',
			texto: 'Kia Rio 21 · SAJ-721-D',
			meta: 'Carga de combustible',
			ts: new Date().toISOString()
		};
	}
	return {
		...base,
		tono: 'aviso',
		icono: '🛣️',
		modulo: 'HUB · Kilómetros',
		titulo: '3,902 km',
		persona: 'Héctor Peña',
		texto: 'Honda City Gris · SAJ-722-B',
		meta: 'lectura registrada hoy a las 11:14',
		ts: new Date().toISOString()
	};
}

/**
 * ?replay=1 — vuelve a sacar los últimos avisos uno por uno.
 * Sirve para ver y ESCUCHAR cómo se ven las alertas (una entrada, una salida,
 * un cumpleaños) sin tener que provocarlas. Los marca como vistos para que no
 * se repitan en el ciclo normal.
 */
function replayEventos() {
	const ultimos = (datos.eventos ?? []).slice(0, 4).reverse();
	if (!ultimos.length) return;
	// Se marcan como vistos para que el ciclo normal no los vuelva a sacar.
	ultimos.forEach((e) => vistos.add(e.id));
	ultimos.forEach((e, i) => setTimeout(() => anunciar(e), i * 3500));
}

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

<!--
	Marca de salida. Va FUERA del `{#if apagado}` a propósito: el apagado es de
	00:00 a 06:00 y la cuenta de las 18:30 nunca cae ahí, pero si algún día se
	adelanta la ventana de apagado, la cuenta de salida debe verse igual.
-->
<CapaSalida modo={salidaModo} segundos={salidaSegundos} hora={HORA_SALIDA} sinAnim={sinAnim} />

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
							{:else if pantalla.id === 'asistencia'}<Asistencia {datos} />
							{:else if pantalla.id === 'portada'}<Portada {datos} />
							{/if}
						{/key}
					{/if}
				</div>
			</div>

			<!-- Canvas único de confeti, sobre todo lo demás -->
			<canvas class="confeti" bind:this={canvasRef} aria-hidden="true"></canvas>

			<CapaAlertas {banda} {toast} {aviso} onCerrarAviso={sacarSiguienteAviso} />

			<!--
				Cuenta de rotación. Se oculta cuando la pantalla está fija por URL
				(no hay cambio que anunciar), cuando hay un aviso a pantalla completa
				o la marca de salida (mandan ellos, no el reloj), y con `?sinanim=1`
				para que las capturas salgan sin cromo.
			-->
			{#if !sinAnim && !aviso && !salidaModo && (params?.reloj || params?.fija === null)}
				<CuentaRotacion restante={restanteRotacion} />
			{/if}

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
