/**
 * Fotos de los reportes como fondo de las anclas bento.
 *
 * El requisito del dueño es doble: que se precarguen **todas** y que la
 * rotación sea **global y única**, no por pantalla. Si cada pantalla montara su
 * propio temporizador, volver a una pantalla ya vista reiniciaría el índice y
 * el navegador volvería a pedir el mismo `/media/thumbs/...`. Por eso el estado
 * vive aquí, fuera de los componentes: un solo `setInterval` y una sola
 * precarga por lista de rutas.
 *
 * Idempotencia: `cargarFotos` se llama en cada refresco del snapshot (30 s).
 * Si la lista es la misma que la última vez, no hace nada: ni re-precarga ni
 * reinicia el índice ni duplica el temporizador. Solo se rearma cuando el
 * snapshot publica otra lista (por ejemplo, entró un reporte nuevo).
 *
 * Si no hay rutas, no se arranca nada: la celda se queda con su color plano.
 * Una imagen que falla se ignora en silencio (`onerror` sin handler).
 */
import { writable } from 'svelte/store';

/** Rutas de foto del snapshot, en el orden en que se rotan. */
export const fotosFondo = writable<string[]>([]);

/** La URL que toca pintar ahora. `''` = sin foto (se deja el color plano). */
export const fotoActual = writable<string>('');

/** Cada cuánto avanza la foto. Pedido del dueño: ~8 s. */
const INTERVALO_MS = 8000;

let listaPrecargada: string[] = [];
let indice = 0;
let timer: ReturnType<typeof setInterval> | null = null;

function avanzar() {
	if (listaPrecargada.length === 0) return;
	indice = (indice + 1) % listaPrecargada.length;
	fotoActual.set(listaPrecargada[indice]);
}

/**
 * Guarda la lista, precarga todas las fotos y arranca el único temporizador de
 * rotación. Llamarla con la misma lista no hace nada.
 */
export function cargarFotos(urls: string[]) {
	const lista = (urls ?? []).filter((u) => typeof u === 'string' && u.length > 0);
	if (lista.length === 0) return;

	if (lista.length === listaPrecargada.length && lista.every((u, i) => u === listaPrecargada[i])) {
		return;
	}

	listaPrecargada = lista;
	fotosFondo.set(lista);

	// Precarga de TODAS: el navegador las deja en su caché y el cambio de foto
	// no pide nada a la red. Sin `await`, sin promesas que puedan romper.
	for (const url of lista) {
		const img = new Image();
		img.decoding = 'async';
		img.src = url;
	}

	indice = 0;
	fotoActual.set(lista[0]);

	if (!timer) timer = setInterval(avanzar, INTERVALO_MS);
}
