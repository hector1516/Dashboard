import { writable } from 'svelte/store';
import { tocar } from './audio';

/** Una notificación de The Penguin, con la hora LOCAL en que se dijo. */
export interface AvisoVolt {
	texto: string;
	/** `HH:MM` local, para la celda de «últimas notificaciones». */
	hora: string;
}

/** Cuántas se conservan: es una celda 1×1, no un historial eterno. */
const MAX = 3;

const interno = writable<AvisoVolt[]>([]);

/**
 * Las últimas tres notificaciones de The Penguin, la más nueva arriba. La llena
 * cualquier módulo que llame a `decirVolt` (presencia, tickets) y el vigilante
 * de `/api/dashboard/volt` con sus avisos, «sin internet» y «volvió».
 */
export const voltHistorial = { subscribe: interno.subscribe };

function horaLocal(d: Date): string {
	return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

/**
 * Guarda una notificación. Sin duplicados: si el mismo texto ya está en la
 * lista se retira el viejo y la copia nueva sube al frente con su hora. Al
 * recargar la pantalla no se repite nada porque el store vive en memoria, no
 * en localStorage.
 */
export function registrarVolt(texto: string, ahora = new Date()) {
	const t = (texto ?? '').trim();
	if (!t) return;
	interno.update((lista) => {
		if (lista[0]?.texto === t) return lista;
		return [{ texto: t, hora: horaLocal(ahora) }, ...lista.filter((a) => a.texto !== t)].slice(
			0,
			MAX
		);
	});
}

/**
 * La voz de The Penguin suena como máximo una vez por minuto. Todo pasa por
 * `tocar()`, que respeta el mute y el silencio nocturno.
 */
const MS_ENTRE_VOCES = 60_000;
let ultimaVoz = 0;

export function tonoVolt() {
	const ahora = Date.now();
	if (ahora - ultimaVoz < MS_ENTRE_VOCES) return;
	ultimaVoz = ahora;
	tocar('volt');
}

/**
 * Notificación corta para The Penguin. Se guarda en el historial y suena (con el
 * tope de una voz por minuto). El `reaccion` se conserva en la firma porque
 * los módulos que avisan ya lo pasan, pero la celda muestra sólo el texto.
 */
export function decirVolt(texto: string, _reaccion = '💬') {
	registrarVolt(texto);
	tonoVolt();
}
