<!--
	📍 Ingenieros en Campo — dónde está cada quien HOY.

	El mapa NO se dibuja en el navegador, a propósito. Podría hacerse con Leaflet
	(marcadores y `fitBounds`), pero eso obligaría a que la TV bajara las teselas
	de internet, y no hay garantía de que salga: el fondo de Bing, el clima y las
	fotos los baja la API. Si la TV no tiene internet, un mapa client-side se ve
	gris y vacío en una pantalla de 6 metros. Así que la API arma un PNG de
	1920x1080 (`api/mapa.py`) y aquí sólo se muestra.

	Lo que se ve: el pin de cada persona con su nombre. Ni hora, ni fecha, ni
	distancia, ni precisión. Se pidió así a propósito —"sólo ver la ubicación y
	el usuario"— y además es lo que hace falta desde el otro lado de la oficina:
	un mapa con marcas de tiempo se vuelve una hoja de cálculo con colores.

	El zoom lo decide el mapa generado, que usa el recuadro que abarcan todos los
	pines: con una persona se acerca mucho, y conforme se reparten por el país se
	aleja hasta que quepan todas.
-->
<script lang="ts">
	import type { Snapshot } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const ubic = $derived((datos as any).ubicaciones ?? null);
	const personas = $derived(ubic?.personas ?? []);
	const mapa = $derived(ubic?.mapa ?? null);
</script>

<div class="campo">
	{#if mapa}
		<img class="mapa" src={mapa} alt="Mapa con la ubicación de los ingenieros en campo" />

		<!--
			Lista de nombres aparte del mapa. Es redundante a propósito: el mapa
			dice dónde, la lista dice quiénes, y a 6 metros el texto chico de un
			mapa no se lee. Con muchos nombres se reparte en columnas.
		-->
		{#if personas.length}
			<div class="nombres" class:muchos={personas.length > 10}>
				{#each personas as p (p.nombre)}
					<span class="nombre"><i></i>{p.nombre}</span>
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
	}

	/*
		Franja de nombres sobre el mapa, abajo. Va con fondo translúcido porque el
		mapa puede ser claro u oscuro según dónde caiga y el texto tiene que leerse
		en los dos casos.
	*/
	.nombres {
		position: absolute;
		left: 0;
		right: 0;
		bottom: 0;
		display: flex;
		flex-wrap: wrap;
		gap: 8px 22px;
		padding: 14px 26px;
		background: linear-gradient(to top, rgb(15 23 42 / 0.92), rgb(15 23 42 / 0));
		font-size: calc(27px * var(--k-escala, 1));
		font-weight: 600;
		color: #f8fafc;
		line-height: 1.15;
	}
	.nombres.muchos { font-size: calc(23px * var(--k-escala, 1)); }

	.nombre { display: inline-flex; align-items: center; gap: 9px; white-space: nowrap; }
	.nombre i {
		width: calc(11px * var(--k-escala, 1));
		height: calc(11px * var(--k-escala, 1));
		border-radius: 50%;
		background: #ff6b00;
		flex: none;
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
	.globo { font-size: calc(120px * var(--k-escala, 1)); opacity: 0.5; }
	.txt { font-size: calc(52px * var(--k-escala, 1)); font-weight: 700; color: #e2e8f0; }
	.sub { font-size: calc(28px * var(--k-escala, 1)); color: #94a3b8; }
</style>
