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
		<!--
			Trama de puntos (el "screentone" del manga) en la franja del título.
			Es lo que separa una portada de comic de una que sólo tiene letras
			negras encima, y se hace con un radial-gradient repetido: cero
			imágenes, cero peticiones.
		-->
		<div class="trama" aria-hidden="true"></div>

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

	/* Puntitos de screentone: se van a la nada hacia abajo con la máscara. */
	.trama {
		position: absolute;
		left: 0;
		right: 0;
		top: 0;
		height: 300px;
		background-image: radial-gradient(rgba(255, 255, 255, 0.6) 22%, transparent 23%);
		background-size: 17px 17px;
		-webkit-mask-image: linear-gradient(180deg, #000 0%, transparent 78%);
		mask-image: linear-gradient(180deg, #000 0%, transparent 78%);
		opacity: 0.42;
		pointer-events: none;
	}

	/* La tinta del rótulo: casi negro con un punto de azul, que es lo que hace
	   que un negro puro sobre una foto se vea "digital". */
	.texto { --tinta: #0a0a12; --tinta-2: #12121c; --sombra-roja: #c81a1a; }

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

	/*
		Estilo cómic/manga con CSS puro, sin bajar otra fuente.

		Por qué no una fuente de manga de verdad: el kiosco es OFFLINE y todo lo
		que se sirve es local (AGENTS.md §Offline). Meter un woff2 de Google
		Fonts o de otro lado sería una dependencia de internet en una pantalla
		de pasillo, y si el día que falte el archivo el título se ve en otra
		tipografía. La receta CSS de abajo da el mismo aire y no puede fallar.

		Los cuatro ingredientes del rótulo de cómic:
		  1. CONTORNO negro grueso (ocho `text-shadow` en cruz + dos en diagonal),
		     porque el trazo es lo que hace que se lea sobre cualquier foto.
		  2. SOMBRA DURA desplazada (sin difuminado): una sombra difusa se ve
		     "bonita"; la dura es la que dice "dibujado a mano".
		  3. INCLINACIÓN (skew): los rótulos de manga casi nunca van verticales.
		  4. SOMBRA DE APOYO suave para que no se apague contra el fondo claro.
	*/
	.titulo {
		margin: 0;
		font-size: var(--tam, 168px);
		/* 900 es el peso más pesado de Outfit: con contorno negro encima, un
		   peso medio deja los letters finos y "tornillosos". */
		font-weight: 900;
		line-height: 1.02;
		letter-spacing: -0.015em;
		color: #fff;
		/* 1 · contorno: DOS capas. La primera (0.018em) es el trazo de la
		   letra; la segunda (0.034em, más difusa) es el "relleno" de tinta
		   alrededor, que es lo que separa de verdad un rótulo de cómic de
		   una letra normal con sombra. Con una sola capa el borde se veía
		   finísimo en la TV. */
		text-shadow:
			-0.018em -0.018em 0 var(--tinta),
			 0.018em -0.018em 0 var(--tinta),
			-0.018em  0.018em 0 var(--tinta),
			 0.018em  0.018em 0 var(--tinta),
			-0.030em  0.000em 0 var(--tinta),
			 0.030em  0.000em 0 var(--tinta),
			 0.000em -0.030em 0 var(--tinta),
			 0.000em  0.030em 0 var(--tinta),
			-0.034em -0.034em 0 var(--tinta-2),
			 0.034em -0.034em 0 var(--tinta-2),
			-0.034em  0.034em 0 var(--tinta-2),
			 0.034em  0.034em 0 var(--tinta-2),
			/* 2 · sombra dura, desplazada y en rojo: el relieve del cómic. El
			   rojo es el truco de los rótulos dibujados, y además avisa que
			   la foto de abajo no es parte de la tipografía. */
			 0.05em 0.05em 0 var(--sombra-roja),
			/* 4 · apoyo suave para que el blanco no se apague */
			 0 0 0.45em rgba(0, 0, 0, 0.55);
		transform: skewX(-7deg);
		/* El skew desplaza la sombra dura, así que la caja tiene que crecer
		   para que la "f" o la "j" no se salgan del recuadro. */
		padding: 0 0.06em;
		/* Un título larguísimo no puede romper la pantalla ni salirse: baja de
		   tamaño hasta que quepa y, si aun así no, parte en dos líneas. */
		max-width: 100%;
		overflow-wrap: break-word;
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
