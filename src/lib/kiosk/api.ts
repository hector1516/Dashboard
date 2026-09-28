/**
 * Acceso a los datos del kiosco.
 *
 * El snapshot lo sirve el backend desde /data/snapshot.json. Hay dos rutas a
 * propósito:
 *   1. /api/dashboard/snapshot → el backend (lectura del snapshot, con su
 *      `origen` y su cache-control).
 *   2. /snapshot.json → nginx sirviendo el archivo crudo de /data. Sirve de
 *      respaldo si la API no está: en un kiosco la prioridad es que se vea
 *      algo, no que venga del backend.
 *
 * Nunca se llama a la base de datos desde el navegador, y nunca a internet.
 */
import type { Snapshot } from './types';

const API_SNAPSHOT = '/api/dashboard/snapshot';
const API_VERSION = '/api/dashboard/version';
const RAW_SNAPSHOT = '/snapshot.json';

/** Snapshot vacío: lo que se ve mientras no llega el primero (o si nunca llega). */
export function snapshotVacio(build = 'dev'): Snapshot {
	return {
		schema_version: 1,
		generado_en: new Date().toISOString(),
		degradado: ['cargando'],
		origen: 'cache',
		build,
		reportes: { total: 0, firmados: 0, pendientes: 0, hoy: 0, esta_semana: 0, por_ingeniero: [], ultimos: [] },
		kilometros: { total_semana: 0, hoy: 0, por_vehiculo: [], serie_7dias: [] },
		tickets: { total_semana: 0, ultimos: [], por_vehiculo: [] },
		legends: { ranking: [], ganador_semana: null, total_puntos: 0, reset_en_segundos: 0 },
		fotos: { ids: [] },
		notas: [],
		cumpleanos: { hoy: [], del_mes: [] },
		aniversarios: { hoy: [], del_mes: [] },
		metricas: {
			top_cliente: null,
			top_ingeniero: null,
			pulso: [],
			actividad_hora: 0,
			ultimo_evento: null,
			top_del_dia: null
		},
		clima: {
			actual: { temperatura: null, humedad: null, viento: null, codigo_clima: 0, descripcion: 'Sin datos', icono: '❓', es_dia: true },
			hoy: { max: null, min: null, prob_lluvia: null },
			manana: { max: null, min: null, prob_lluvia: null },
			leido_en: null
		},
		fondos: [],
		eventos: []
	};
}

/** Trae el snapshot; si la API falla, el archivo crudo. Nunca lanza. */
export async function cargarSnapshot(): Promise<{ datos: Snapshot; viaApi: boolean }> {
	try {
		const r = await fetch(API_SNAPSHOT, { cache: 'no-store' });
		if (r.ok) {
			const j = await r.json();
			if (j && typeof j.generado_en === 'string') return { datos: j as Snapshot, viaApi: true };
		}
	} catch {
		/* sin API: al archivo crudo */
	}
	try {
		const r = await fetch(RAW_SNAPSHOT, { cache: 'no-store' });
		if (r.ok) {
			const j = await r.json();
			if (j && typeof j.generado_en === 'string') return { datos: j as Snapshot, viaApi: false };
		}
	} catch {
		/* sin nada: el que llama conserva el snapshot anterior */
	}
	throw new Error('sin snapshot');
}

/**
 * Build del contenedor. Si cambia, la pantalla se recarga sola: un kiosco puede
 * estar días sin recargar y no hay nadie que le dé F5.
 */
export async function pedirBuild(): Promise<string | null> {
	try {
		const r = await fetch(API_VERSION, { cache: 'no-store' });
		if (!r.ok) return null;
		const j = await r.json();
		return typeof j?.build === 'string' ? j.build : null;
	} catch {
		return null;
	}
}

/**
 * Rutas de los thumbs.
 *
 * El ancho NO se inventa: sale de `snapshot.media`, que publica el backend con
 * los anchos que realmente generó. Pedir 1280 cuando el backend hizo 960 es un
 * 404, y en la pantalla de fotos (a pantalla completa) eso es una foto negra.
 */
export function anchoFotos(snap?: { media?: { fotos_w: number } }): number {
	return snap?.media?.fotos_w ?? 960;
}

export function anchoTickets(snap?: { media?: { tickets_w: number } }): number {
	return snap?.media?.tickets_w ?? 480;
}

export function thumbFoto(idReporte: number, orden: number, w: number): string {
	return `/media/thumbs/rep_${idReporte}_${orden}_w${w}.jpg`;
}

export function thumbTicket(idTicket: number, w: number): string {
	return `/media/thumbs/tk_${idTicket}_w${w}.jpg`;
}

/**
 * Normaliza lo que venga en `avatar`.
 *
 * El backend manda una RUTA local (`/media/avatars/u5.jpg`), porque enviar el
 * avatar como base64 dentro del snapshot inflaba la respuesta con decenas de KB
 * por persona. Antes esta función envolvía cualquier cosa en
 * `data:image/png;base64,…` y terminaba pidiendo
 * `data:image/png;base64,/media/avatars/u5.jpg`: una imagen rota (el círculo
 * vacío en Legends). Por eso distingue los tres formatos en vez de asumir uno.
 */
export function avatarSrc(avatar: string | null | undefined): string {
	if (!avatar) return '';
	if (avatar.startsWith('/') || avatar.startsWith('http') || avatar.startsWith('data:')) {
		return avatar;
	}
	// Base64 pelado: es el formato que usaba el dashboard de Field.
	return `data:image/png;base64,${avatar}`;
}
