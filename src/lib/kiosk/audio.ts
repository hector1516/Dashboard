/**
 * Audio del kiosco — sintetizado con WebAudio, cero archivos.
 *
 * Por qué no MP3/WAV: un kiosco se ve 24/7 y cualquier archivo de audio es un
 * archivo más que puede faltar, weighs 200KB o no cargar. Con osciladores no
 * hay nada que servir: 0 KB, 0 peticiones, y el tono se puede cambiar sin
 * redesplegar.
 *
 * Reglas:
 *   · Volumen discreto por default (0.35): se oye en el pasillo, no en la sala.
 *   · Silencio automático de 22:00 a 07:00 (tonos apagados, efectos de clima
 *     siguen: son ambiente, no avisos).
 *   · Panic-mute con cualquier tecla o clic: `apagar()`.
 *   · Si el navegador bloquea el AudioContext (autoplay sin gesto), el chip
 *     🔇 de la pantalla avisa; con Edge en modo kiosco
 *     (--autoplay-policy=no-user-gesture-required) no hace falta.
 */

const CLAVE_MUTE = 'dashboard:muted';
const CLAVE_VOL = 'dashboard:volumen';

/** Ventana sin tonos: de 22:00 a 07:00. */
const HORA_SILENCIO_INICIO = 22;
const HORA_SILENCIO_FIN = 7;

let ctx: AudioContext | null = null;
let master: GainNode | null = null;
let silenciado = false;
let volumen = 0.35;
let bloqueado = false; // el navegador no dejó crear/resumir el contexto
let lluviaGain: GainNode | null = null;

function recursos(): { c: AudioContext; m: GainNode } | null {
	if (typeof window === 'undefined') return null;
	if (!ctx) {
		const AC = window.AudioContext || (window as any).webkitAudioContext;
		if (!AC) return null;
		try {
			ctx = new AC();
			master = ctx.createGain();
			master.gain.value = 0;
			master.connect(ctx.destination);
		} catch {
			return null;
		}
	}
	return { c: ctx, m: master! };
}

/** Silencio nocturno (no bloqueo del navegador): decide si toca sonar. */
export function enHorarioSilencioso(d = new Date()): boolean {
	const h = d.getHours();
	return h >= HORA_SILENCIO_INICIO || h < HORA_SILENCIO_FIN;
}

export function initAudio() {
	// El estado persiste entre recargas: una TV que reinició y quedó muda
	// porque alguien la silenció hace tres días es un bug, no una preferencia.
	try {
		silenciado = localStorage.getItem(CLAVE_MUTE) === '1';
		const v = parseFloat(localStorage.getItem(CLAVE_VOL) ?? '');
		if (!Number.isNaN(v) && v >= 0 && v <= 1) volumen = v;
	} catch {
		/* modo privado: se queda con los defaults */
	}
	// El primer gesto (o el arranque con la política de autoplay) abre el ctx.
	const despertar = () => {
		desbloquear();
		if (typeof window !== 'undefined') {
			window.removeEventListener('pointerdown', despertar);
			window.removeEventListener('keydown', despertar);
		}
	};
	if (typeof window !== 'undefined') {
		window.addEventListener('pointerdown', despertar, { once: false });
		window.addEventListener('keydown', despertar, { once: false });
	}
	desbloquear();
}

export function desbloquear() {
	const r = recursos();
	if (!r) return;
	if (r.c.state === 'suspended') {
		r.c.resume().then(() => {
			bloqueado = false;
			aplicarVolumen();
		}).catch(() => {
			bloqueado = true;
		});
	} else {
		bloqueado = false;
		aplicarVolumen();
	}
}

/** ¿El navegador dejó el audio bloqueado? La pantalla lo avisa con un chip. */
export function audioBloqueado(): boolean {
	return bloqueado;
}

export function estaSilenciado(): boolean {
	return silenciado;
}

export function getVolumen(): number {
	return volumen;
}

export function setVolumen(v: number) {
	volumen = Math.max(0, Math.min(1, v));
	try {
		localStorage.setItem(CLAVE_VOL, String(volumen));
	} catch { /* nada */ }
	aplicarVolumen();
}

export function setSilenciado(v: boolean) {
	silenciado = v;
	try {
		localStorage.setItem(CLAVE_MUTE, v ? '1' : '0');
	} catch { /* nada */ }
	if (!v) desbloquear();
}

/** Panic-mute. Devuelve el estado nuevo. */
export function apagar(): boolean {
	setSilenciado(!silenciado);
	return silenciado;
}

function aplicarVolumen() {
	const r = recursos();
	if (!r) return;
	const efectiva = silenciado || enHorarioSilencioso() ? 0 : volumen;
	// Rampa corta: un gain que salta de 0 a 0.35 se oye como clic.
	r.m.gain.cancelScheduledValues(r.c.currentTime);
	r.m.gain.setValueAtTime(r.m.gain.value, r.c.currentTime);
	r.m.gain.linearRampToValueAtTime(efectiva, r.c.currentTime + 0.08);
}

/** Una nota: frecuencia, duración, volumen relativo y momento de arranque. */
function nota(freq: number, dur: number, vol: number, atraso = 0, tipo: OscillatorType = 'sine') {
	const r = recursos();
	if (!r) return;
	const t0 = r.c.currentTime + atraso;
	const osc = r.c.createOscillator();
	const g = r.c.createGain();
	osc.type = tipo;
	osc.frequency.setValueAtTime(freq, t0);
	g.gain.setValueAtTime(0.0001, t0);
	g.gain.exponentialRampToValueAtTime(Math.max(0.0002, vol), t0 + 0.015);
	g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
	osc.connect(g);
	g.connect(r.m);
	osc.start(t0);
	osc.stop(t0 + dur + 0.05);
}

export type Tono = 'info' | 'exito' | 'destaque' | 'alerta' | 'click' | 'hola' | 'adios' | 'tic' | 'salida' | 'aviso' | 'pantalla';

/**
 * Tonos del kiosco. Cortos y de poca información: son un "algo pasó" para
 * voltear la cabeza, no un anuncio. El-pitched grave es lo que más se escucha
 * a 3 metros.
 */
export function tocar(tono: Tono) {
	if (silenciado || enHorarioSilencioso()) return;
	desbloquear();
	switch (tono) {
		case 'info':
			nota(880, 0.09, 0.18);
			break;
		case 'exito':
			nota(660, 0.1, 0.16);
			nota(990, 0.14, 0.14, 0.11);
			break;
		case 'destaque':
			// Arpegio ascendente + una octava al final: es el que levanta la vista.
			[523.25, 659.25, 783.99, 1046.5].forEach((f, i) => nota(f, 0.16, 0.15, i * 0.1));
			nota(2093, 0.3, 0.06, 0.45);
			break;
		case 'alerta':
			[392, 349.23, 293.66].forEach((f, i) => nota(f, 0.22, 0.16, i * 0.15, 'triangle'));
			break;
		case 'click':
			nota(1200, 0.03, 0.07);
			break;
		case 'hola':
			// Saludo: tres notas que suben. Amable, no estridente: es un "hola"
			// a la oficina, no una alarma.
			[523.25, 659.25, 783.99].forEach((f, i) => nota(f, 0.13, 0.13, i * 0.075));
			break;
		case 'adios':
			// Despedida: dos notas que bajan, más suaves que el saludo.
			[659.25, 440].forEach((f, i) => nota(f, 0.16, 0.11, i * 0.1, 'triangle'));
			break;
		case 'aviso':
		case 'pantalla':
			// El aviso a pantalla completa: tres notas claras con cola, más una
			// quinta arriba. Es el sonido que tiene que levantar la vista a 6
			// metros, así que va más alto y más largo que los demás, y termina
			// en una nota que se sostiene en vez de apagarse de golpe.
			[523.25, 659.25, 783.99].forEach((f, i) => nota(f, 0.2, 0.2, i * 0.13));
			nota(1046.5, 0.55, 0.18, 0.42, 'triangle');
			nota(1567.98, 0.7, 0.09, 0.5);
			break;
		case 'tic':
			// Un solo "tic" seco: es el segundero de la cuenta de salida. Corto y
			// grave a propósito, para que 10 de ellos seguidos canse menos.
			nota(1046.5, 0.05, 0.16);
			break;
		case 'salida':
			// Las 18:30: dos golpes de bocina con la quinta arriba, largo. Es
			// lo único de todo el kiosco que se oye en otra habitación.
			[220, 220, 329.63, 220, 220].forEach((f, i) =>
				nota(f, i === 4 ? 0.7 : 0.2, 0.2, [0, 0.28, 0.56, 0.9, 1.2][i], 'sawtooth'));
			[220, 329.63, 440].forEach((f, i) => nota(f, 0.9, 0.1, 1.6 + i * 0.02, 'triangle'));
			break;
	}
}

/* ── Efectos de ambiente por clima ──────────────────────────────────────────
   No son avisos: son el "ruido de fondo" de la pantalla. Se mezclan muy
   bajo y se puede apagar con el mismo mute.                              */

function ruidoRosa(ctx: AudioContext): AudioBuffer {
	const largo = ctx.sampleRate * 2;
	const buf = ctx.createBuffer(1, largo, ctx.sampleRate);
	const d = buf.getChannelData(0);
	let b0 = 0, b1 = 0, b2 = 0;
	for (let i = 0; i < largo; i++) {
		const blanco = Math.random() * 2 - 1;
		b0 = 0.99765 * b0 + blanco * 0.099046;
		b1 = 0.963 * b1 + blanco * 0.2965164;
		b2 = 0.57555 * b2 + blanco * 1.0526913;
		d[i] = (b0 + b1 + b2 + blanco * 0.1848) * 0.16;
	}
	return buf;
}

/** Lluvia: ruido rosa filtrado en loop. `nivel` 0 la apaga. */
export function ambienteLluvia(nivel: number) {
	const r = recursos();
	if (!r) return;
	if (nivel <= 0) {
		if (lluviaGain) {
			try { lluviaGain.gain.linearRampToValueAtTime(0, r.c.currentTime + 0.4); } catch { /* noop */ }
			lluviaGain = null;
		}
		return;
	}
	if (!lluviaGain) {
		const src = r.c.createBufferSource();
		src.buffer = ruidoRosa(r.c);
		src.loop = true;
		const filtro = r.c.createBiquadFilter();
		filtro.type = 'lowpass';
		filtro.frequency.value = 1400;
		const g = r.c.createGain();
		g.gain.value = 0;
		src.connect(filtro);
		filtro.connect(g);
		g.connect(r.m);
		src.start();
		lluviaGain = g;
	}
	lluviaGain.gain.linearRampToValueAtTime(0.05 * nivel, r.c.currentTime + 1.2);
}

/** Viento: mismo ruido, más grave y más lento. */
export function ambienteViento(nivel: number) {
	if (nivel <= 0) return ambienteLluvia(0);
	ambienteLluvia(nivel * 0.6);
}

/**
 * Mantiene el ambiente|Clima alineado con el snapshot. Se llama cuando cambia
 * el clima, no en cada render.
 */
export function ambienteClima(codigo: number, esDia: boolean) {
	ambienteLluvia(0);
	const lluvia = codigo >= 51 && codigo <= 67;
	const tormenta = codigo >= 80 && codigo <= 99;
	const viento = codigo >= 45 && codigo <= 48;
	if (tormenta) ambienteLluvia(1);
	else if (lluvia) ambienteViento(0.8);
	else if (viento) ambienteViento(0.5);
	else if (esDia && codigo === 0) {
		// Día despejado: pad cálido muy bajo, para que el silencio no sea plano.
		const r = recursos();
		if (r) {
			const osc = r.c.createOscillator();
			const g = r.c.createGain();
			osc.type = 'sine';
			osc.frequency.value = 196;
			g.gain.value = 0;
			osc.connect(g);
			g.connect(r.m);
			osc.start();
			g.gain.linearRampToValueAtTime(0.012, r.c.currentTime + 2);
		}
	}
}

/** Limpia timers/loops al desmontar (la pantalla es de una sola vida, pero
    igual: si el componente se recarga, no queremos dos ambientes sonando). */
export function detenerAmbiente() {
	ambienteLluvia(0);
}
