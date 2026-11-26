/*
	Barrido de cifras del kiosco.

	Antes sólo el ancla contaba (`<Numero>`): el resto de los números —cifras,
	montos, puntos, días, porcentajes— aparecía seco. Esto recorre el escenario
	después de montar cada pantalla y anima el nodo de texto de los elementos
	que contienen UN número formateado y nada más.

	Qué cuenta (y qué no):

	  · Sólo elementos con un único nodo de texto cuyo contenido, ya recortado,
	    sea `$1,234.50`, `23`, `18°` o `45 %`. Un texto con palabras
	    (`23 vales · promedio $500`, `datos de hace 1 min`) no es una cifra: se
	    salta entero, para no animar media frase ni romper la lectura.
	  · Se respeta el formato original: prefijo `$`, separador de miles,
	    decimales y sufijo (`%`, `°`, `°C`).
	  · No toca lo que esté dentro de `[data-numero]` (el ancla ya usa
	    `<Numero>`) ni de `[data-sin-contar]` (relojes y cuentas que cambian
	    solos, como la cuenta de rotación).

	Se apaga con `prefers-reduced-motion: reduce`, con `.sin-anim` en el
	escenario y con `?sinanim=1`: en esos casos el texto se deja tal cual, que
	es lo que necesitan una captura y una persona con sensibilidad al
	movimiento.
*/

/** Un número formateado y nada más. `°C` va antes que `°` para no dejar la C. */
const NUMERO = /^(\s*)(\$?)(\d+(?:,\d{3})*)(\.\d+)?(\s?(?:°C|°|%))?(\s*)$/;

interface Formato {
	/** Espacios iniciales y finales del texto original. */
	antes: string;
	despues: string;
	prefijo: string;
	entero: string;
	decimales: string;
	sufijo: string;
	/** El texto original, para dejarlo EXACTO al terminar. */
	texto: string;
}

/**
 * Nodos ya animados. Un nodo es nuevo en cada montaje de pantalla (Svelte
 * recrea el DOM), así que esto sólo evita contar dos veces el mismo texto si
 * una pantalla se re-evalúa mientras todavía está en el crossfade.
 */
const animados = new WeakSet<Text>();

function leer(texto: string): Formato | null {
	const m = NUMERO.exec(texto);
	if (!m) return null;
	return {
		antes: m[1],
		prefijo: m[2],
		entero: m[3],
		decimales: m[4] ?? '',
		sufijo: m[5] ?? '',
		despues: m[6],
		texto
	};
}

/** Pinta `n` con el mismo formato del texto original. */
function pintar(f: Formato, n: number): string {
	const dec = f.decimales.length > 0 ? f.decimales.length - 1 : 0;
	let [ent, frac] = (dec > 0 ? n.toFixed(dec) : String(Math.round(n))).split('.');

	// `05` original: el relleno se mantiene mientras el número es menor.
	const digitos = f.entero.replace(/,/g, '').length;
	if (digitos > 1 && f.entero.startsWith('0')) ent = ent.padStart(digitos, '0');
	if (f.entero.includes(',')) ent = ent.replace(/\B(?=(\d{3})+(?!\d))/g, ',');

	const cuerpo = `${ent}${frac ? '.' + frac : ''}`;
	const numero = `${f.prefijo}${cuerpo}${f.sufijo}`;
	return `${f.antes}${numero}${f.despues}`;
}

/**
 * ¿La cifra está metida en una frase?
 *
 * El padre es quien lo dice: si tiene texto propio además del nodo (el «·
 * promedio » de «23 vales · promedio $5,400»), el número es una palabra de la
 * oración y animarlo deja la frase mintiendo a media cuenta. Un `.cifra`
 * dentro de `.cuerpo` no tiene ese texto alrededor: ahí sí se cuenta.
 */
function enFrase(el: HTMLElement, nodo: Text): boolean {
	const padre = el.parentElement;
	if (!padre) return false;
	for (const hijo of padre.childNodes) {
		if (hijo !== nodo && hijo.nodeType === Node.TEXT_NODE && (hijo as Text).data.trim()) return true;
	}
	return false;
}

/** ¿Hay que dejar el texto quieto? */
function sinAnimacion(raiz: HTMLElement): boolean {
	if (raiz.classList.contains('sin-anim') || raiz.closest('.sin-anim')) return true;
	if (typeof window === 'undefined') return true;
	if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return true;
	// `?sinanim=1` es el interruptor de capturas. Se mira la URL además de la
	// clase porque el efecto puede correr antes de que `+page.svelte` la ponga.
	return new URLSearchParams(window.location.search).get('sinanim') === '1';
}

export interface OpcionesContar {
	/** Duración de la cuenta, en ms. */
	duracion?: number;
}

/**
 * Anima de 0 a su valor cada cifra que haya dentro de `raiz`.
 *
 * Una sola animación por elemento (un `requestAnimationFrame` compartido) y se
 * acaba: sin `setInterval` ni bucles infinitos.
 */
export function contarNumeros(raiz: HTMLElement, opciones: OpcionesContar = {}): void {
	if (!raiz || sinAnimacion(raiz)) return;

	const duracion = opciones.duracion ?? 700;
	const cifras: Array<{ nodo: Text; formato: Formato; valor: number }> = [];

	for (const el of raiz.querySelectorAll<HTMLElement>('*')) {
		// Un solo nodo de texto y ningún hijo con forma de elemento. Los
		// comentarios de Svelte (`<!--[-->`, `<!---->`) que envuelven un `{#if}`
		// no cuentan como contenido: sin esto, media pantalla quedaba fuera
		// sólo porque el número venía de un bloque condicional.
		let nodo: Text | null = null;
		let soloTexto = true;
		for (const hijo of el.childNodes) {
			if (hijo.nodeType === Node.TEXT_NODE) {
				if (nodo) {
					soloTexto = false;
					break;
				}
				nodo = hijo as Text;
			} else if (hijo.nodeType === Node.ELEMENT_NODE) {
				soloTexto = false;
				break;
			}
		}
		if (!soloTexto || !nodo) continue;
		if (animados.has(nodo)) continue;
		// El propio elemento o un ancestro marcado: el ancla (`Numero`), los
		// relojes y lo que cambia solo quedan fuera.
		if (el.closest('[data-numero], [data-sin-contar]')) continue;
		// Si el padre tiene texto propio alrededor (`23 vales · promedio
		// $5,400`, con el monto en un `<b>`), la cifra es parte de una frase:
		// contarla haría leer «promedio $32» a media animación. Se salta.
		if (enFrase(el, nodo)) continue;

		const formato = leer(nodo.data);
		if (!formato) continue;

		const valor = Number(formato.entero.replace(/,/g, '') + formato.decimales);
		if (!Number.isFinite(valor)) continue;

		animados.add(nodo);
		cifras.push({ nodo, formato, valor });
	}

	if (cifras.length === 0) return;

	const t0 = performance.now();
	const paso = (t: number) => {
		// El reloj del `requestAnimationFrame` puede venir un pelo ANTES del
		// `performance.now()` con el que se tomó `t0`; sin el tope en 0, el
		// primer fotograma pintaba un valor negativo.
		const k = Math.max(0, Math.min(1, (t - t0) / duracion));
		for (const c of cifras) {
			// El último fotograma escribe el texto original, no un redondeo:
			// la cifra termina en su valor exacto, con su formato exacto.
			c.nodo.data = k >= 1 ? c.formato.texto : pintar(c.formato, c.valor * (1 - Math.pow(1 - k, 3)));
		}
		if (k < 1) requestAnimationFrame(paso);
	};
	requestAnimationFrame(paso);
}
