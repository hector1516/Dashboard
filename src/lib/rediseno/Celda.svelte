<script lang="ts">
	import { onMount, type Snippet } from 'svelte';
	import { fade } from 'svelte/transition';
	import { fotoActual } from './fotosFondo';
	interface Props {
		area: string;
		rotulo: string;
		tono?: '' | 'dark' | 'red' | 'azul';
		i?: number;
		/**
		 * Fondo de foto de los reportes de servicio (anclas 2×2).
		 *
		 * La foto la publica el store global `fotoActual`, que precarga todas
		 * las rutas UNA vez y las rota con un solo temporizador compartido:
		 * cambiar de pantalla no reinicia el índice ni vuelve a pedir la
		 * imagen. Encima va un velo del tono de la celda, para que el texto y
		 * las cifras sigan leyéndose (≥4.5:1) sin que la foto compita.
		 */
		fondo?: boolean;
		children: Snippet;
	}
	let { area, rotulo, tono = '', i = 0, fondo = false, children }: Props = $props();

	/** Sin fundido si el sistema pide menos movimiento: el cambio es seco. */
	let sinMovimiento = $state(false);
	onMount(() => {
		const mq = matchMedia('(prefers-reduced-motion: reduce)');
		const aplicar = () => (sinMovimiento = mq.matches);
		aplicar();
		mq.addEventListener('change', aplicar);
		return () => mq.removeEventListener('change', aplicar);
	});
</script>

<section
	class="cell {tono}"
	class:con-foto={fondo}
	style="grid-area:{area};--i:{i}"
>
	{#if fondo}
		<!-- Foto de los reportes por detrás del contenido. `z-index` negativo
		     dentro del `isolation` de la celda: queda sobre el fondo y debajo
		     del texto. -->
		<div class="foto" aria-hidden="true">
			{#if $fotoActual}
				{#key $fotoActual}
					<img
						class="foto-img"
						src={$fotoActual}
						alt=""
						decoding="async"
						transition:fade={{ duration: sinMovimiento ? 0 : 700 }}
					/>
				{/key}
			{/if}
			<div class="foto-velo"></div>
		</div>
	{/if}
	<div class="lbl">{rotulo}</div>
	{@render children()}
</section>

<style>
	.cell {
		position: relative;
		/* El `isolation` deja pintar la foto con `z-index` negativo: queda
		   ENCIMA del fondo de la celda y DEBAJO del contenido, en vez de irse
		   detrás de la celda y desaparecer. */
		isolation: isolate;
		min-height: 0; border-radius: var(--k-radio); background: var(--k-sup);
		padding: 24px 28px; display: flex; flex-direction: column; gap: 10px;
		box-shadow: 0 2px 0 rgba(18,20,26,.05), 0 22px 44px -26px rgba(18,20,26,.5);
		overflow: hidden;
		animation: caer .45s cubic-bezier(.2,.9,.3,1.2) both;
		animation-delay: calc(var(--i, 0) * 35ms);
	}
	/* Capa de foto: por detrás del contenido, con `z-index` negativo dentro
	   del `isolation` de la celda. */
	.foto {
		position: absolute;
		inset: 0;
		z-index: -2;
		pointer-events: none;
	}
	.foto-img {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
	/* Velo del tono de la celda: deja ver la foto pero manda el color y
	   garantiza el contraste del texto. Medido con el peor píxel de la caja
	   de cada texto, sobre las fotos reales y con una foto blanca forzada
	   (2026-11-26): tinta ≥8:1, azul ≥5.4:1, naranja ≥4.6:1 con el texto
	   opaco (ver la regla del ancla naranja más abajo). */
	.foto-velo {
		position: absolute;
		inset: 0;
		background: linear-gradient(to bottom, rgba(18, 20, 26, 0.8), rgba(18, 20, 26, 0.84));
	}
	.cell.red .foto-velo {
		background: linear-gradient(to bottom, rgba(242, 109, 38, 0.86), rgba(242, 109, 38, 0.84));
	}
	/* Azul un punto más oscuro que `--k-azul`: sobre el azul plano el texto
	   secundario ya iba justo y la foto le quitaba margen. */
	.cell.azul .foto-velo {
		background: linear-gradient(to bottom, rgba(28, 37, 90, 0.86), rgba(28, 37, 90, 0.89));
	}
	.cell:not(.dark):not(.red):not(.azul) .foto-velo {
		background: linear-gradient(to bottom, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.88));
	}
	/* Con foto, el contenido lleva una sombra corta: separa la cifra y el
	   texto de la textura sin apagar la foto. La sombra hereda a todo lo que
	   hay dentro de la celda. Sobre el naranja (texto en tinta) se usa una
	   sombra cálida, para no ensuciar el trazo con negro. */
	.cell.con-foto {
		text-shadow:
			0 1px 2px rgba(9, 10, 14, 0.55),
			0 4px 18px rgba(9, 10, 14, 0.4);
	}
	.cell.con-foto.red {
		text-shadow:
			0 1px 1px rgba(96, 34, 4, 0.42),
			0 3px 14px rgba(96, 34, 4, 0.3);
	}
	/* En el ancla naranja el texto va en tinta y ahí la translucidez cuesta
	   contraste: la tinta al 82 % sobre la naranja plana da 4.8:1, pero una
	   zona oscura de la foto la baja a 3.8:1. Medido con el peor píxel de la
	   caja del texto, opaco se queda en 4.5–6:1 en TODO el rango de la foto
	   (negro a blanco), así que sobre foto esos tres textos van sin veladura
	   y la jerarquía la da el tamaño, no la opacidad. */
	.cell.con-foto.red .lbl,
	.cell.con-foto.red :global(.sub),
	.cell.con-foto.red :global(.delta) {
		opacity: 1;
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
	/* Con foto de fondo el rótulo necesita otro punto: el velo lo deja en
	   ~4.1:1 al .55 y en 7:1 al .82. */
	.cell.con-foto .lbl { opacity: .82; }
</style>
