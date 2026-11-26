<script lang="ts">
	import type { Snippet } from 'svelte';
	interface Props {
		area: string;
		rotulo: string;
		tono?: '' | 'dark' | 'red' | 'azul';
		i?: number;
		/**
		 * Marca de agua opcional: una imagen de fondo, muy tenue, al pie de la
		 * celda. Es decoración, no dato: va por detrás del rótulo y del
		 * contenido, no se puede seleccionar y si el archivo no carga no pasa
		 * nada (el `background-image` falla en silencio y la celda se lee
		 * igual). La usa la celda ancla del clima con el dibujo de la oficina.
		 */
		marcaAgua?: string;
		children: Snippet;
	}
	let { area, rotulo, tono = '', i = 0, marcaAgua = '', children }: Props = $props();
</script>

<section
	class="cell {tono}"
	class:marca={!!marcaAgua}
	style="grid-area:{area};--i:{i}{marcaAgua ? `;--marca:url('${marcaAgua}')` : ''}"
>
	<div class="lbl">{rotulo}</div>
	{@render children()}
</section>

<style>
	.cell {
		position: relative;
		/* El `isolation` es lo que deja pintar la marca de agua con z-index
		   negativo: queda ENCIMA del fondo de la celda y DEBAJO del contenido,
		   en vez de irse detrás de la celda y desaparecer. */
		isolation: isolate;
		min-height: 0; border-radius: var(--k-radio); background: var(--k-sup);
		padding: 24px 28px; display: flex; flex-direction: column; gap: 10px;
		box-shadow: 0 2px 0 rgba(18,20,26,.05), 0 22px 44px -26px rgba(18,20,26,.5);
		overflow: hidden;
		animation: caer .45s cubic-bezier(.2,.9,.3,1.2) both;
		animation-delay: calc(var(--i, 0) * 35ms);
	}
	/* Marca de agua: el dibujo isométrico de la oficina, cubriendo el ancho y
	   apoyado al pie. Opacidad baja para que no se lea como una foto y se
	   desvanece hacia arriba, donde está la cifra. */
	.cell.marca::before {
		content: '';
		position: absolute;
		inset: 0;
		z-index: -1;
		background-image: var(--marca);
		background-size: cover;
		background-position: center bottom;
		background-repeat: no-repeat;
		/* La celda es tinta: el dibujo se pasa a gris y se OSCURECE para que
		   solo deje ver el trazo. Con brightness alto (2.2) los muros blancos
		   se saturaban y la marca se leía como una foto; a 0.5 y 7 % queda
		   como papel de fondo, no como imagen. */
		filter: grayscale(1) brightness(0.5) contrast(0.95);
		opacity: 0.07;
		mask-image: linear-gradient(to bottom, transparent 0%, #000 58%);
		-webkit-mask-image: linear-gradient(to bottom, transparent 0%, #000 58%);
		pointer-events: none;
	}
	@keyframes caer {
		from { opacity: 0; transform: translateY(-12px) scale(.985); }
		to   { opacity: 1; transform: none; }
	}
	@media (prefers-reduced-motion: reduce) { .cell { animation: none; } }
	.cell.dark { background: var(--k-tinta); color: #f7f3ea; }
	/* Ancla de alerta: fondo naranja de marca, texto en tinta (6.1:1).
	   Blanco sobre #F26D26 se queda en 2.9:1 y no se lee a 3 metros. */
	.cell.red { background: var(--k-rojo); color: var(--k-tinta); }
	/* Ancla informativa: azul del logo, texto blanco (10:1). */
	.cell.azul { background: var(--k-azul); color: var(--k-sup); }
	.lbl { font-size: var(--k-f-strip); font-weight: 800; letter-spacing: 1.7px; text-transform: uppercase; opacity: .55; }
	/* En las anclas de color el rótulo sube a .8: hereda tinta (naranja) o
	   blanco (azul) y al .55 se perdía contra el fondo. */
	.cell.red .lbl, .cell.azul .lbl { opacity: .8; }
</style>
