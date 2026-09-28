/** Formateo para la pantalla: todo en es-MX y sin dependencias de Intl raras. */

const MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
const DIAS = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];

export function nombreMes(d = new Date()): string {
	return MESES[d.getMonth()];
}

export function nombreDia(d = new Date()): string {
	return DIAS[d.getDay()];
}

/** "hace 4 min", "hace 2 h", "hace 3 d". Para los que no cabe la fecha. */
export function haceCuanto(iso: string | null | undefined, ahora = Date.now()): string {
	if (!iso) return '—';
	const t = Date.parse(iso.replace(' ', 'T'));
	if (Number.isNaN(t)) return '—';
	const min = Math.max(0, Math.floor((ahora - t) / 60000));
	if (min < 1) return 'ahora';
	if (min < 60) return `hace ${min} min`;
	const h = Math.floor(min / 60);
	if (h < 24) return `hace ${h} h`;
	const d = Math.floor(h / 24);
	if (d < 30) return `hace ${d} d`;
	const fecha = new Date(t);
	return `${fecha.getDate()} de ${MESES[fecha.getMonth()]}`;
}

export function num(n: number | null | undefined, dec = 0): string {
	if (n === null || n === undefined || Number.isNaN(n)) return '—';
	return n.toLocaleString('es-MX', { minimumFractionDigits: dec, maximumFractionDigits: dec });
}

export function pct(n: number | null | undefined): string {
	if (n === null || n === undefined) return '—';
	return `${Math.round(n)}%`;
}

export function money(n: number | null | undefined): string {
	if (n === null || n === undefined) return '—';
	return n.toLocaleString('es-MX', { style: 'currency', currency: 'MXN' });
}

/** Corta un texto largo sin partir palabras rare feas (para notas y clientes). */
export function recortar(s: string | null | undefined, n: number): string {
	const t = (s ?? '').trim();
	if (t.length <= n) return t;
	return t.slice(0, n - 1).trimEnd() + '…';
}

export function hhmm(iso: string | null | undefined): string {
	if (!iso) return '—';
	const t = Date.parse(iso.replace(' ', 'T'));
	if (Number.isNaN(t)) return '—';
	const d = new Date(t);
	return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

export function hhmmDiff(segundos: number): string {
	if (segundos <= 0) return '00:00';
	const h = Math.floor(segundos / 3600);
	const m = Math.floor((segundos % 3600) / 60);
	const s = Math.floor(segundos % 60);
	return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

/** Emoji de medalla por posición del podio Legends. */
export function medalla(pos: number): string {
	return pos === 1 ? '🥇' : pos === 2 ? '🥈' : pos === 3 ? '🥉' : `#${pos}`;
}

export const NIVEL_EMOJI: Record<string, string> = {
	Diamante: '💎',
	Oro: '🥇',
	Plata: '🥈',
	Bronce: '🥉'
};

/**
 * Escala del podio: 1.00 → 0.55 de forma cóncava, para que el 1º se lea
 * gigante sin que el #10 quede ilegible a 3 metros.
 */
export function rankScale(pos: number): number {
	const t = Math.max(0, Math.min(9, pos - 1)) / 9;
	return +(1 - 0.45 * Math.pow(t, 0.75)).toFixed(3);
}

/** Semáforo del clima por código WMO. */
export function esLluvioso(codigo: number): boolean {
	return codigo >= 51 && codigo <= 99;
}
export function esSoleado(codigo: number, esDia: boolean): boolean {
	return codigo <= 2 && esDia;
}
export function esNublado(codigo: number): boolean {
	return codigo === 3 || (codigo >= 45 && codigo <= 48);
}
