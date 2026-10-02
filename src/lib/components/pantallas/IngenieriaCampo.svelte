<!--
	📍 Ingenieros en Campo — dónde está cada quien HOY.

	El mapa NO se dibuja en el navegador, a propósito. Podría hacerse con Leaflet
	(marcadores y `fitBounds`), pero eso obligaría a que la TV bajara las teselas
	de internet, y no hay garantía de que salga: el fondo de Bing, el clima y las
	fotos los baja la API. Si la TV no tiene internet, un mapa client-side se ve
	gris y vacío en una pantalla de 6 metros. Así que la API arma un PNG de
	1920x1080 (`api/mapa.py`) y aquí sólo se muestra.

	LA DIVISIÓN DEL TRABAJO, y por qué está donde está:
	  · la API pone la foto de cada persona en su pin, agrupa a quien reporta
	    desde el mismo sitio y calcula el zoom;
	  · el navegador pone encima lo que una imagen no puede tener: el pulso, la
	    entrada escalonada, el brillo de los grupos.

	Es decir: el PNG ya tiene las caras dibujadas y estas capas NO las vuelven a
	dibujar, sólo laten encima. Si se dibujaran dos veces, los pines se verían
	doblados y medio transparente.

	Lo que se ve: el pin de cada persona con su nombre. Ni hora, ni fecha, ni
	distancia, ni precisión. Se pidió así a propósito —"sólo ver la ubicación y
	el usuario"— y además es lo que hace falta desde el otro lado de la oficina:
	un mapa con marcas de tiempo se vuelve una hoja de cálculo con colores.
-->
<script lang="ts">
	import type { Snapshot } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const ubic = $derived((datos as any).ubicaciones ?? null);
	const personas = $derived(ubic?.personas ?? []);
	const mapa = $derived(ubic?.mapa ?? null);
	const pins = $derived<{x: number; y: number; n: number; i?: number | number[]}[]>(
		ubic?.pins ?? []
	);

	/*
		Entrada escalonada: cada pin aparece con un desfase según su posición, de
		arriba hacia abajo. Se ve como un barrido que "carga" el mapa en vez de
		que todo aparezca de golpe, que es lo que hace un `v-if` normal.

		El retardo sale de la fila, no de un número aleatorio, para que la animación
		sea siempre la misma: si uno llega 200 ms más tarde, los pines no deben
		saltar de sitio.
	*/
	const entrada = (i: number) => `${Math.min(i * 0.16, 1.6)}s`;

	/*
		Con más de un grupo, el pulso va escalonado para que no late todo al mismo
		tiempo: un solo anillo que se expande se lee como un "cargando"; varios
		desfasados se leen como "varios signals activos".
	*/
	const desfase = (i: number) => `${(i % 4) * 0.7}s`;
</script>

<div class="campo">
	{#if mapa}
		<img class="mapa" src={mapa} alt="Mapa con la ubicación de los ingenieros en campo" />

		<!--
			Capa de efectos. Va ENCIMA del mapa y NO dibuja pines: sólo anillos que
			se expanden desde cada posición, para que el mapa se sienta vivo sin
			tapar las caras que el backend ya puso.
		-->
		<div class="efectos" aria-hidden="true">
			{#each pins as p, i (i)}
				<span
					class="pulso"
					class:grupo={p.n > 1}
					style="left:{p.x / 1920 * 100}%; top:{p.y / 1080 * 100}%;
					       animation-delay:{entrada(i)}"
				></span>
				{#if p.n > 1}
					<span
						class="pulso doble"
						style="left:{p.x / 1920 * 100}%; top:{p.y / 1080 * 100}%;
						       animation-delay:{desfase(i)}"
					></span>
				{/if}
			{/each}
		</div>

		<!--
			Lista de nombres aparte del mapa. Es redundante a propósito: el mapa dice
			dónde, la lista dice quiénes, y a 6 metros el texto chico de un mapa no
			se lee. Con muchos nombres se achica la letra en vez de cortar la lista:
			cortar información en una pantalla es peor que letra más chica.
		-->
		{#if personas.length}
			<div class="nombres" class:muchos={personas.length > 10} class:muchos2={personas.length > 20}>
				{#each personas as p, i (p.id_usuario ?? p.nombre)}
					<span class="nombre" style="animation-delay:{0.4 + i * 0.07}s">
						<i style="background:{(ubic?.colores?.[i % (ubic?.colores?.length || 1)]) || '#ff6b00'}"></i>
						{p.nombre}
					</span>
				{/each}
			</div>
		{/if}
	{:else}
		<div class="vacio">
			<div class="globo">📍</div>
			<div class="txt">Sin reportes de ubicación</div>
			<div class="sub">Cada ingeniero publica la suya con el botón «Aquí estoy» de la app</div>
		</div>
	{/if}
</div>

<style>
	.campo {
		position: relative;
		height: 100%;
		width: 100%;
		overflow: hidden;
		border-radius: 18px;
		background: #1e293b;
	}

	.mapa {
		width: 100%;
		height: 100%;
		object-fit: cover;
		display: block;
		animation: aparecer 0.7s ease both;
	}

	@keyframes aparecer {
		from { opacity: 0; transform: scale(1.015); }
		to   { opacity: 1; transform: none; }
	}

	/* Capa de efectos: cubre todo y no captura clics. */
	.efectos { position: absolute; inset: 0; pointer-events: none; }

	/*
		Anillo que se expande y se desvanece, como un radar. Va desde el tamaño
		del pin hasta poco más del doble: si se estirara mucho, se vería el momento
		en que se borra, que es lo que hace que un efecto parezca de plantilla.
	*/
	.pulso {
		position: absolute;
		width: 96px;
		height: 96px;
		margin: -48px 0 0 -48px;
		border-radius: 50%;
		border: 3px solid rgb(255 107 0 / 0.85);
		animation: radar 3.4s cubic-bezier(0.22, 0.61, 0.36, 1) infinite;
		box-shadow: 0 0 22px rgb(255 107 0 / 0.35);
	}
	.pulso.grupo { border-color: rgb(37 99 235 / 0.85); box-shadow: 0 0 22px rgb(37 99 235 / 0.35); }

	@keyframes radar {
		0%   { transform: scale(0.42); opacity: 0; }
		18%  { opacity: 0.95; }
		100% { transform: scale(2.1); opacity: 0; }
	}

	.pulso.doble { animation-duration: 4.6s; border-width: 2px; }

	/*
		Franja de nombres sobre el mapa. Fondo translúcido porque el mapa puede ser
		claro u oscuro según dónde caiga, y el texto tiene que leerse en los dos.
	*/
	.nombres {
		position: absolute;
		left: 0;
		right: 0;
		bottom: 0;
		display: flex;
		flex-wrap: wrap;
		gap: 8px 22px;
		padding: 16px 26px;
		background: linear-gradient(to top, rgb(15 23 42 / 0.93), rgb(15 23 42 / 0));
		font-size: calc(27px * var(--k-escala, 1));
		font-weight: 600;
		color: #f8fafc;
		line-height: 1.15;
	}
	.nombres.muchos  { font-size: calc(23px * var(--k-escala, 1)); }
	.nombres.muchos2 { font-size: calc(20px * var(--k-escala, 1)); }

	.nombre {
		display: inline-flex;
		align-items: center;
		gap: 9px;
		white-space: nowrap;
		animation: subir 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
	}
	.nombre i {
		width: calc(11px * var(--k-escala, 1));
		height: calc(11px * var(--k-escala, 1));
		border-radius: 50%;
		flex: none;
	}

	@keyframes subir {
		from { opacity: 0; transform: translateY(14px); }
		to   { opacity: 1; transform: none; }
	}

	.vacio {
		height: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 14px;
		background: radial-gradient(120% 90% at 50% 20%, #1e293b, #0f172a);
	}
	.globo { font-size: calc(120px * var(--k-escala, 1)); opacity: 0.5; animation: flotar 4s ease-in-out infinite; }
	.txt { font-size: calc(52px * var(--k-escala, 1)); font-weight: 700; color: #e2e8f0; }
	.sub { font-size: calc(28px * var(--k-escala, 1)); color: #94a3b8; }

	@keyframes flotar {
		0%, 100% { transform: translateY(0); }
		50%      { transform: translateY(-14px); }
	}

	/*
		Con `?sinanim=1` la pantalla se congela para las capturas de verificación:
		nada de anillos a media expansión ni de letras a medio aparecer, o la
		captura no sirve para comparar nada.
	*/
	:global(.sin-anim) .pulso,
	:global(.sin-anim) .globo { animation: none; opacity: 0; }
	:global(.sin-anim) .mapa,
	:global(.sin-anim) .nombre { animation: none; }

	@media (prefers-reduced-motion: reduce) {
		.pulso, .globo, .mapa, .nombre { animation: none; }
	}
</style>