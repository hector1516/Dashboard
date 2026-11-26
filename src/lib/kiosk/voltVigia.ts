import { browser } from '$app/environment';
import { registrarVolt, tonoVolt } from './voltAviso';

/**
 * Vigilante de The Penguin, sin personaje ni globo.
 *
 * Antes esto vivía dentro de `VoltComentario` (el globo flotante). Ahora las
 * notificaciones se cuentan en la celda de «últimas notificaciones», así que
 * el sondeo, la detección de internet y el audio viven aquí, en un módulo sin
 * DOM que arranca una vez desde el layout.
 *
 * Se conservan las reglas de siempre: el primer arranque no escupe el
 * historial, el último id visto sobrevive a la recarga en localStorage y la
 * voz no suena más de una vez por minuto (`tonoVolt`).
 */
interface Aviso {
	id: number;
	texto: string;
	nivel: string;
}

const CLAVE_ULTIMO = 'volt:ultimoAviso';
const MS_SONDEO = 60_000;
const SIN_INTERNET =
	'Sin internet por aquí. Lo de la oficina sigue andando; el clima y los fondos se quedan como estaban. Te aviso en cuanto vuelva.';
const VOLVIO = '¡Volvió el internet! Ya puedo traer el clima y los fondos otra vez.';

let iniciado = false;

export function iniciarVoltVigia(): () => void {
	if (!browser || iniciado) return () => {};
	iniciado = true;

	let ultimoAviso = Number(localStorage.getItem(CLAVE_ULTIMO) || 0) || 0;
	/** null = todavía no se sabe; el primer sondeo no avisa de «volvió». */
	let sinInternet: boolean | null = null;

	function mostrar(texto: string) {
		registrarVolt(texto);
		tonoVolt();
	}

	async function cargar() {
		try {
			const r = await fetch('/api/dashboard/volt', { cache: 'no-store' });
			if (!r.ok) return;
			const d: any = await r.json();

			// El servidor manda si hay salida a internet (clima + fondos). El
			// navegador sólo puede decir si la TV perdió la red local.
			const antes = sinInternet;
			const ahora = !!d.sin_internet || (typeof navigator !== 'undefined' && navigator.onLine === false);
			sinInternet = ahora;

			const lista: Aviso[] = (d.avisos || [])
				.slice()
				.sort((a: Aviso, b: Aviso) => a.id - b.id);
			let nuevo: Aviso | null = null;
			if (lista.length) {
				if (!ultimoAviso) {
					// Primer arranque del kiosco: la historia no se cuenta.
					ultimoAviso = lista[lista.length - 1].id;
					localStorage.setItem(CLAVE_ULTIMO, String(ultimoAviso));
				} else {
					const frescos = lista.filter((a) => a.id > ultimoAviso);
					if (frescos.length) {
						// Si llegaron varios, importa el último: el resto ya es
						// historia y no se repite en cadena.
						nuevo = frescos[frescos.length - 1];
						ultimoAviso = nuevo.id;
						localStorage.setItem(CLAVE_ULTIMO, String(ultimoAviso));
					}
				}
			}

			if (nuevo) {
				mostrar(nuevo.texto);
			} else if (antes === true && !ahora) {
				mostrar(VOLVIO);
			} else if (ahora && antes !== true) {
				mostrar(SIN_INTERNET);
			}
		} catch {
			// Sin red local no se inventa nada: la celda se queda como está.
		}
	}

	void cargar();
	const reloj = setInterval(cargar, MS_SONDEO);

	const alCambiarRed = () => cargar();
	window.addEventListener('online', alCambiarRed);
	window.addEventListener('offline', alCambiarRed);

	return () => {
		clearInterval(reloj);
		window.removeEventListener('online', alCambiarRed);
		window.removeEventListener('offline', alCambiarRed);
	};
}
