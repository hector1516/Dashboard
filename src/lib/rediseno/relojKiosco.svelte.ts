// Reloj, fecha y antigüedad del kiosco, compartidos por las pantallas bento.
//
// Las pantallas traen su propio `<Marco>`, y el marco es tonto a propósito:
// recibe la hora, la fecha y la antigüedad ya formateadas. Este módulo arma
// esas tres cosas para que cada pantalla se pueda montar con solo `datos`
// (sin props de reloj) y para que las nueve pantallas digan lo mismo:
//
//   · hora      → la prop manda; si no, el reloj del navegador
//   · fecha     → la prop manda; si no, «miércoles 25 de noviembre»
//   · antigüedad→ la prop manda; si no, se calcula de `datos.generado_en`
//
// Se escribe DESPUÉS de hidratar: si no, el HTML estático del build llevaría
// la hora del build y la pantalla tarda un segundo en refrescar.
//
// Uso, dentro del `<script>` de una pantalla:
//
//   const k = relojKiosco(() => ({ reloj, fecha, antiguedad, generadoEn: datos?.generado_en }));
//   <Marco reloj={k.hora} fecha={k.fecha} antiguedad={k.antiguedad} … />
//
// Las props van en un lector (`() => ({…})`) para que sigan siendo reactivas
// dentro del módulo; un objeto plano las congelaría al montar.
import { haceCuanto, nombreDia, nombreMes } from '$lib/kiosk/format';

export interface RelojEntrada {
	/** Hora en 12 h ya formateada (`5:34 p.m.`). */
	reloj?: string;
	/** Fecha larga (`miércoles 25 de noviembre`). */
	fecha?: string;
	/** Antigüedad ya redactada (`datos de hace 1 min`). */
	antiguedad?: string;
	/** `datos.generado_en` del snapshot: de ahí sale la antigüedad. */
	generadoEn?: string | null;
}

const dos = (n: number) => String(n).padStart(2, '0');

/** «5:34 p.m.». 12 h con a.m./p.m., como se lee un reloj de pared; la
 *  medianoche es `12:00 a.m.` y el mediodía `12:00 p.m.`. */
function horaCorta(d: Date): string {
	const h24 = d.getHours();
	const h = h24 % 12 === 0 ? 12 : h24 % 12;
	const sufijo = h24 < 12 ? 'a.m.' : 'p.m.';
	return `${h}:${dos(d.getMinutes())} ${sufijo}`;
}

/** «miércoles 25 de noviembre». Se arma a mano: `toLocaleDateString`
 *  depende del locale del navegador y en el kiosco no es el mismo siempre. */
function fechaLarga(d: Date): string {
	return `${nombreDia(d).toLowerCase()} ${d.getDate()} de ${nombreMes(d).toLowerCase()}`;
}

/** «datos de hace 1 min». Un snapshot ilegible no es «ahora»: es «sin datos». */
export function antiguedadDe(iso: string | null | undefined, cuando: Date | null): string {
	if (!cuando) return '';
	const h = haceCuanto(iso, cuando.getTime());
	if (h === '—') return 'sin datos';
	if (h === 'ahora') return 'datos al día';
	return `datos de ${h}`;
}

/**
 * Los tres datos del marco, reactivos. Se llama una vez por pantalla, en el
 * `<script>` del componente (usa `$state`, `$derived` y `$effect`, que son de
 * inicialización).
 */
export function relojKiosco(leer: () => RelojEntrada) {
	const props = $derived(leer());
	let ahora = $state<Date | null>(null);

	// Solo en el navegador: en SSR no hay reloj que valga y el HTML del build
	// no puede llevar una hora congelada.
	$effect(() => {
		ahora = new Date();
		const t = setInterval(() => (ahora = new Date()), 1000);
		return () => clearInterval(t);
	});

	return {
		get hora(): string {
			return props.reloj ?? (ahora ? horaCorta(ahora) : '--:--');
		},
		get fecha(): string {
			return props.fecha ?? (ahora ? fechaLarga(ahora) : '');
		},
		get antiguedad(): string {
			return props.antiguedad ?? antiguedadDe(props.generadoEn, ahora);
		}
	};
}
