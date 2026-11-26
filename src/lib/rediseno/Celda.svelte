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
		 * Marca de agua opcional: una imagen de fondo, muy tenue, al pie de la
		 * celda. Es decoración, no dato: va por detrás del rótulo y del
		 * contenido, no se puede seleccionar y si el archivo no carga no pasa
		 * nada (el `background-image` falla en silencio y la celda se lee
		 * igual). La usa la celda ancla del clima con el dibujo de la oficina.
		 */
		marcaAgua?: string;
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
	let { area, rotulo, tono = '', i = 0, marcaAgua = '', fondo = false, children }: Props = $props();

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
	class:marca={!!marcaAgua}
	class:con-foto={fondo}
	style="grid-area:{area};--i:{i}{marcaAgua ? `;--marca:url('${marcaAgua}')` : ''}"
>
	{#if fondo}
		<!-- Foto de los reportes por detrás del contenido. `z-index` negativo
		     dentro del `isolation` de la celda (igual que la marca de agua):
		     queda sobre el fondo y debajo del texto. -->
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
	/* Capa de foto. Va en -2 para que la marca de agua (-1) siga contando y
	   el contenido quede por delante. */
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
	   garantiza el contraste del texto. Medido sobre el peor caso (foto
	   blanca, 255): la tinta a .80 → el `.delta` al 60 % queda en 4.8:1;
	   el azul oscurecido a .89 → el `.delta` al 62 % en 5.1:1; el naranja a
	   .86 → la tinta al 62 % en 4.3:1 (ya estaba así sobre el plano). */
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
