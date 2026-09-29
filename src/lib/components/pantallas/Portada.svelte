<!--
	🖼️ Portada — imagen a pantalla completa con el título encima.

	La imagen la sube una persona desde el módulo Notas de Admon (tabla
	`HUB_PantallaImagenes`, clave PORTADA) y la TV la toma sola: es la pantalla
	que se usa para Innovations, Económicos, o lo que toque. Sirve para
	anunciar cosas que la pantalla no tiene dónde más.

	El título va encima, en el centro, gigante —no es un pie de foto: es el
	contenido—. Si nadie escribe un título, el backend arma "ECCSA en
	<mes>" con la fecha de hoy, así que la pantalla nunca sale vacía.

	La imagen se sirve desde /media/panel/ (nginx, desde el volumen), NO desde
	el snapshot: son 400 KB y el snapshot se pide cada 30 s.
-->
<script lang="ts">
	import type { Snapshot } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const img = $derived(datos.imagen);

	/**
	 * El tamaño del título se elige por lo largo del texto, no por CSS puro: el
	 * escenario es de 1920 px fijos y "ECCSA en Septiembre" a 168 px ya toca los
	 * bordes; un "Innovations Económicos 2026" se salía de la pantalla. Con
	 * `min(168px, Xvw)` el problema es peor: en el escenario escalado, Xvw se
	 * calcula contra el viewport y no contra los 1920 px de diseño.
	 */
	const tamTitulo = $derived.by(() => {
		const n = (img?.titulo ?? '').length;
		if (n > 26) return 96;
		if (n > 20) return 118;
		if (n > 14) return 142;
		return 168;
	});
	const proporcionesOk = $derived(
		img?.hay ? img.ancho === 1920 && img.alto === 1080 : false
	);
</script>

<div class="screen">
	{#if img?.hay && img.ruta}
		<img class="fondo" src={img.ruta} alt="" />

		<!--
			El velo es para que el título se lea sobre CUALQUIER imagen: una foto
			clara con texto blanco encima es ilegible, y no se puede obligar a
			quien sube la imagen a que deje la parte central oscura.
		-->
		<div class="velo" aria-hidden="true"></div>

		<div class="texto">
			<h1 class="titulo" style="--tam:{tamTitulo}px">{img.titulo}</h1>
			{#if img.subida}
				<span class="pie">subida el {img.subida}</span>
			{/if}
			{#if !proporcionesOk && img.ancho && img.alto}
				<!--
					Ojo en la vista, no un error en la TV: si la imagen no es
					1920x1080 se ve estirada y quien la subió es quien puede
					arreglarlo. Aquí se avisa y ya.
				-->
				<span class="aviso">⚠ la imagen mide {img.ancho}×{img.alto}, se ve estirada</span>
			{/if}
		</div>
	{:else}
		<div class="vacio">
			No hay imagen de portada
			<span class="vacio-sub">
				Se sube desde el módulo Notas de Admon, en la pestaña "Pantalla de la TV"
			</span>
		</div>
	{/if}
</div>

<style>
	.screen { padding: 0; }

	.fondo {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: cover;
		/* Sin `object-fit: contain`: si la imagen no es 16:9 se recorta, y una
		   portada recortada se ve mejor que una portada estirada. El aviso de
		   proporción le avisa a quien la subió. */
		animation: entrarPantalla 0.6s ease both;
	}

	.velo {
		position: absolute;
		inset: 0;
		/* Oscurece el centro (donde va el texto) y respeta los bordes. */
		background:
			radial-gradient(ellipse at 50% 50%, rgba(0, 0, 0, 0.72) 0%, rgba(0, 0, 0, 0.18) 58%, rgba(0, 0, 0, 0.45) 100%);
	}

	.texto {
		position: absolute;
		inset: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 18px;
		text-align: center;
		padding: 0 90px;
	}

	.titulo {
		margin: 0;
		font-size: var(--tam, 168px);
		font-weight: 800;
		line-height: 1.02;
		letter-spacing: -0.02em;
		color: #fff;
		/* Un título larguísimo no puede romper la pantalla ni salirse: baja de
		   tamaño hasta que quepa y, si aun así no, parte en dos líneas. */
		max-width: 100%;
		overflow-wrap: break-word;
		text-shadow:
			0 4px 30px rgba(0, 0, 0, 0.8),
			0 0 90px rgba(0, 0, 0, 0.5);
		animation: golpe 0.9s cubic-bezier(0.16, 1, 0.3, 1) both;
	}
	@keyframes golpe {
		from { opacity: 0; transform: scale(0.94); }
		to   { opacity: 1; transform: none; }
	}

	.pie {
		font-size: 26px;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.5);
		text-shadow: 0 2px 12px rgba(0, 0, 0, 0.7);
	}

	.aviso {
		font-size: 20px;
		font-weight: 800;
		color: #fca5a5;
		background: rgba(0, 0, 0, 0.5);
		padding: 7px 16px;
		border-radius: 999px;
		border: 1px solid rgba(248, 113, 113, 0.4);
	}
</style>
