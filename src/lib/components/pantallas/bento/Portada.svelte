<script lang="ts">
	// Portada del mes: la «escena» del sistema, en la retícula bento.
	//
	// UNA sola celda 4×3 con la imagen a sangre y el rótulo del mes. No es un
	// tablero: es la pantalla que se usa para anunciar algo (Innovations, el
	// Buen Fin, la posada) y por eso no lleva más cifras que el mes.
	//
	// Por qué NO usa `<Celda>`: la celda base trae 24 px de relleno y su
	// rótulo pequeño, y aquí la imagen tiene que llegar al borde. Se copia el
	// aspecto exterior (radio, sombra, animación de caída) y el rótulo pasa a
	// ser una etiqueta sobre la foto. El componente del sistema no se toca.
	//
	// La imagen la sube una persona desde el módulo Notas de Admon
	// (`HUB_PantallaImagenes`, clave PORTADA) y el snapshot publica su ruta
	// LOCAL (`/media/panel/…`): cero peticiones a internet.
	//
	// SIN IMAGEN NO HAY LIENZO VACÍO: se pinta una placa de tinta con el mes y
	// la instrucción de dónde se sube. Un fondo de Bing con un texto encima
	// parecería una portada de verdad y no lo es. Tampoco se usa
	// `datos.fondos`: esos wallpapers son el ambiente del kiosco, no contenido.
	//
	// RESERVA DE VOLT: la escena ocupa toda la retícula, pero el rótulo vive
	// abajo a la IZQUIERDA y su ancho se corta antes del cuadro de Volt
	// (448 px a la derecha). La placa y su globo flotan sobre la foto sin
	// tapar una sola letra.
	import Bento from '$lib/rediseno/Bento.svelte';
	import Marco from '$lib/rediseno/Marco.svelte';
	import '$lib/rediseno/tokens.css';
	import { relojKiosco } from '$lib/rediseno/relojKiosco.svelte';
	import { nombreMes } from '$lib/kiosk/format';

	interface Props {
		/** Snapshot del kiosco. Solo se lee `imagen`. */
		datos?: any;
		/** Hora `HH:MM` ya formateada. Sin ella la toma del reloj. */
		reloj?: string;
		/** Fecha larga. Sin ella, la de hoy. */
		fecha?: string;
		/** «datos de hace 1 min». Sin ella, se calcula de `generado_en`. */
		antiguedad?: string;
		/** Posición en la rotación (`4/10`). Sin ella, un guion. */
		posicion?: string;
		/** Frase del pie. Sin ella, se arma del dato. */
		volt?: string;
	}
	let { datos, reloj, fecha, antiguedad, posicion, volt }: Props = $props();

	const img = $derived(datos?.imagen ?? null);
	const ruta = $derived(String(img?.ruta ?? ''));
	const titulo = $derived(String(img?.titulo ?? '').trim());
	const subida = $derived(String(img?.subida ?? '').trim());

	/** La imagen existe en el snapshot… hasta que el archivo no está: si el
	 *  navegador no la puede leer, se cae al estado honesto en vez de dejar un
	 *  rectángulo roto. Se reinicia cuando el snapshot publica otra ruta. */
	let fallo = $state(false);
	const hay = $derived(!!(img?.hay && ruta) && !fallo);
	$effect(() => {
		if (ruta) fallo = false;
	});

	// Reloj, fecha y antigüedad: el mismo módulo en todas las pantallas bento.
	const k = relojKiosco(() => ({ reloj, fecha, antiguedad, generadoEn: datos?.generado_en }));

	/**
	 * El mes del rótulo sale de `k.fecha` («miércoles 25 de noviembre»), que es
	 * la fecha del kiosco ya formateada. Se lee para que el rótulo cambie al
	 * cambiar el día aunque la pantalla quede fija con `?pantalla=portada`
	 * toda la noche; el año, del reloj del navegador.
	 */
	const mesAnio = $derived.by(() => {
		const f = k.fecha ?? '';
		const m = / de ([^\s]+)\s*$/i.exec(f);
		const mes = (m ? m[1] : nombreMes()).toUpperCase();
		return { mes, anio: String(new Date().getFullYear()) };
	});

	/** `2026-11-12 12:10` → «12 de noviembre · 12:10». A mano, sin `new
	 *  Date(iso)` (UTC: de noche cambiaría de día). */
	function fechaSubida(iso: string): string {
		const g = /^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2}))?/.exec(iso);
		if (!g) return '';
		const mes = Number(g[2]);
		if (!(mes >= 1 && mes <= 12)) return '';
		const dia = String(Number(g[3]));
		const nombre = nombreMes(new Date(2000, mes - 1, 1)).toLowerCase();
		return `subida el ${dia} de ${nombre}${g[4] && g[5] ? ` · ${g[4]}:${g[5]}` : ''}`;
	}

	const frase = $derived.by(() => {
		if (!hay) return 'No hay imagen de portada; se sube desde Notas de Admon, en «Pantalla de la TV».';
		const cuando = fechaSubida(subida);
		const quien = titulo ? `«${titulo}»` : `La portada de ${mesAnio.mes.toLowerCase()}`;
		return cuando ? `${quien}, ${cuando}.` : `${quien}.`;
	});
	const linea = $derived(volt ?? frase);
</script>

<Marco
	titulo="Portada del mes"
	reloj={k.hora}
	fecha={k.fecha}
	antiguedad={k.antiguedad}
	temperatura={datos?.clima?.actual?.temperatura}
	posicion={posicion ?? '—'}
	volt={linea}
	degradado={datos?.degradado ?? []}
>
	<Bento>
		<!-- Una sola celda 4×3: la escena. -->
		<section class="cell escena" class:sin-foto={!hay} style="grid-area:1/1/4/5;--i:0">
			{#if hay}
				<!-- `object-fit: cover`: si la imagen no es 16:9 se recorta, que se
				     ve mejor que estirada. El velo de abajo es para que el rótulo
				     se lea sobre cualquier foto. -->
				<img
					class="fondo"
					src={ruta}
					alt=""
					decoding="async"
					onerror={() => (fallo = true)}
				/>
				<div class="velo" aria-hidden="true"></div>

				<div class="rotulo">
					<div class="mes-linea">
						<span class="mes">{mesAnio.mes}</span>
						<span class="anio">{mesAnio.anio}</span>
					</div>
					{#if titulo}<div class="titulo">{titulo}</div>{/if}
					{#if subida}<div class="pie">{fechaSubida(subida)}</div>{/if}
				</div>
			{:else}
				<div class="sin-portada">
					<div class="mes-linea">
						<span class="mes">{mesAnio.mes}</span>
						<span class="anio">{mesAnio.anio}</span>
					</div>
					<div class="aviso">
						<b>Sin imagen de portada</b>
						<span>
							Se sube desde el módulo Notas de Admon, en la pestaña «Pantalla de la TV».
						</span>
					</div>
				</div>
			{/if}
		</section>
	</Bento>
</Marco>

<style>
	/* Mismo exterior que `Celda` (radio, sombra, caída) pero sin relleno: la
	   imagen va a sangre. */
	.cell {
		position: relative;
		min-height: 0;
		border-radius: var(--k-radio);
		background: var(--k-sup);
		box-shadow: 0 2px 0 rgba(18, 20, 26, 0.05), 0 22px 44px -26px rgba(18, 20, 26, 0.5);
		overflow: hidden;
		animation: caer 0.45s cubic-bezier(0.2, 0.9, 0.3, 1.2) both;
	}
	@keyframes caer {
		from {
			opacity: 0;
			transform: translateY(-12px) scale(0.985);
		}
		to {
			opacity: 1;
			transform: none;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.cell {
			animation: none;
		}
	}

	.fondo {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: cover;
		display: block;
	}
	/* Oscurece solo el pie de la foto: el resto se ve tal cual. */
	.velo {
		position: absolute;
		inset: 0;
		background: linear-gradient(
			180deg,
			rgba(18, 20, 26, 0.34) 0%,
			rgba(18, 20, 26, 0) 22%,
			rgba(18, 20, 26, 0) 52%,
			rgba(18, 20, 26, 0.82) 100%
		);
	}

	/* El rótulo de la celda NO se pinta: el título «Portada del mes» ya está en
	   la barra del marco y repetirlo aquí era ruido sobre la foto. El dato de la
	   escena es el mes, que va abajo en grande. */

	/* El rótulo del mes: abajo a la izquierda y cortado antes del rincón de
	   Volt (448 px de ancho en el borde derecho). */
	.rotulo,
	.sin-portada {
		position: absolute;
		left: 32px;
		right: 480px;
		bottom: 30px;
		display: flex;
		flex-direction: column;
		gap: 8px;
		min-width: 0;
		text-align: left;
	}
	.mes-linea {
		display: flex;
		align-items: baseline;
		gap: 18px;
		flex-wrap: nowrap;
		min-width: 0;
	}
	.mes {
		font-size: 148px;
		font-weight: 900;
		line-height: 0.9;
		letter-spacing: -6px;
		white-space: nowrap;
	}
	.anio {
		font-size: 52px;
		font-weight: 800;
		letter-spacing: -1px;
		opacity: 0.75;
	}
	.titulo {
		font-size: 34px;
		font-weight: 800;
		letter-spacing: -0.4px;
		line-height: 1.1;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.pie {
		font-size: 20px;
		font-weight: 600;
		opacity: 0.72;
	}
	.rotulo {
		color: #fff;
		text-shadow: 0 3px 18px rgba(0, 0, 0, 0.55);
	}

	/* ── sin imagen: placa de tinta, no un lienzo vacío ───────── */
	.escena.sin-foto {
		background: var(--k-tinta);
		color: #f7f3ea;
	}
	/* Un degradado muy suave para que la placa no parezca un div de relleno. */
	.escena.sin-foto::before {
		content: '';
		position: absolute;
		inset: 0;
		background: radial-gradient(
			120% 90% at 8% 100%,
			rgba(228, 0, 43, 0.16) 0%,
			rgba(228, 0, 43, 0) 58%
		);
	}
	.escena.sin-foto .sin-portada {
		top: 0;
		justify-content: center;
		gap: 18px;
	}
	/* El mes va sólido: sin foto, la placa ES la portada tipográfica. Un mes
	   al 25 % parecería una imagen que no cargó. */
	.escena.sin-foto .mes {
		opacity: 1;
	}
	.escena.sin-foto .anio {
		opacity: 0.55;
	}
	.aviso {
		display: flex;
		flex-direction: column;
		gap: 8px;
		max-width: 760px;
		margin-top: 4px;
		padding-top: 20px;
		border-top: 1px solid rgba(247, 243, 234, 0.22);
	}
	.aviso b {
		font-size: 34px;
		font-weight: 800;
		letter-spacing: -0.4px;
	}
	.aviso span {
		font-size: 21px;
		font-weight: 600;
		line-height: 1.35;
		opacity: 0.66;
	}
</style>
