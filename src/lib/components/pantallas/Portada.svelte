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
		   portada recortada se ve mejor que una portada estirada. */
		animation: entrarPantalla 0.6s ease both;
	}

	.velo {
		position: absolute;
		inset: 0;
		/* Oscurece la franja de arriba, donde va el título, y respeta el resto:
		   el centro de la foto es lo que se quiere ver. Con el título pegado
		   al borde la banda oscura se acorta y se intensifica. */
		background:
			linear-gradient(180deg, rgba(0, 0, 0, 0.8) 0%, rgba(0, 0, 0, 0.45) 16%, rgba(0, 0, 0, 0.05) 38%, rgba(0, 0, 0, 0.3) 100%);
	}

	.texto {
		position: absolute;
		inset: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		/* Hasta arriba, pegado al header (que son 56 px): el título hace de
		   encabezado de la portada, no va flotando en el tercio superior. En
		   px fijos y no en %, porque el escenario mide 1920x1080 y ya está
		   escalado: un % aquí sería % del viewport, no de la pantalla. */
		justify-content: flex-start;
		gap: 10px;
		text-align: center;
		padding: 14px 90px 0;
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
		font-size: 20px;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.42);
		text-shadow: 0 2px 12px rgba(0, 0, 0, 0.7);
	}

</style>
