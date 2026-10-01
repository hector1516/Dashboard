<!--
	Fondo de la pantalla: capa de imagen + viñeta + efectos de clima.

	El fondo SIEMPRE es local: la lista viene del snapshot (rutas /media/...).
	Nunca una URL de internet — si no hay fondos descargados se usa el
	gradiente por hora del día, que es lo que se ve hoy en Field.

	El crossfade entre fondos evita el parpadeo que da el `background-image`
	de una sola pasada: dos capas y se interpola la opacidad.
-->
<script lang="ts">
	interface Props {
		fondos: string[];
		periodo: 'dawn' | 'day' | 'dusk' | 'night';
		lluvioso: boolean;
		soleado: boolean;
		nublado: boolean;
		/** Atenúa todo (modo noche 23:00–06:00). */
		tenue: boolean;
		/**
		 * Tema del mes: una capa PNG con la silueta del mes, muy tenue. Va
		 * ENCIMA de la foto y DEBAJO de la viñeta, para que las pantallas se
		 * vean como siempre. `?tema=<1-12>` fuerza otro mes para revisarlos.
		 */
		tema?: { capa: string; tinte: string; nombre: string; icono: string } | null;
	}

	let { fondos, periodo, lluvioso, soleado, nublado, tenue, tema = null }: Props = $props();

	// Índice del fondo visible y el que se estáfundiendo: se avanza desde
	// fuera (el orquestador) para que el cambio coincida con la rotación.
	let actual = $state(0);
	let siguiente = $state(-1);
	let progreso = $state(1);
	let duracion = $state(1600);

	// Cuando llega un snapshot con otra lista de fondos se reinicia el índice.
	// El guardia por REFERENCIA es lo que evita el bucle: el efecto lee `fondos`
	// y escribe estado, así que sin esto se realimentaría.
	let baseFondos: string[] = [];
	$effect(() => {
		if (fondos === baseFondos) return;
		baseFondos = fondos;
		actual = 0;
		siguiente = -1;
		progreso = 1;
	});

	/** Llamado por el orquestador en cada rotación de pantalla. */
	export function cambiarFondo(nuevoIndice: number, ms = 1600) {
		if (!fondos.length) return;
		siguiente = ((nuevoIndice % fondos.length) + fondos.length) % fondos.length;
		duracion = ms;
		progreso = 0;
		const t0 = performance.now();
		const paso = (t: number) => {
			const p = Math.min(1, (t - t0) / duracion);
			progreso = p;
			if (p < 1) requestAnimationFrame(paso);
			else {
				actual = siguiente;
				siguiente = -1;
			}
		};
		requestAnimationFrame(paso);
	}

	export function fondoActual(): string {
		return fondos[actual] ?? '';
	}

	let gotas = $state<{ x: number; dur: number; delay: number; op: number }[]>([]);
	$effect(() => {
		gotas = lluvioso
			? Array.from({ length: 90 }, () => ({
					x: Math.random() * 100,
					dur: 0.55 + Math.random() * 0.6,
					delay: Math.random() * 1.2,
					op: 0.25 + Math.random() * 0.5
				}))
			: [];
	});
</script>

<div class="fondo">
	<!--
		OJO CON EL ORDEN DE ESTAS CAPAS, que es de lo más fácil de arruinar:

		1. `.capa-gradiente` — el fondo de la hora del día. Va PRIMERO, abajo de
		   todo, porque su trabajo es el que se ve cuando NO hay foto: es el
		   cielo. Es opaco (colores sólidos, sin alfa) y para abajo estaba mal
		   el orden, con lo que tapaba por completo la foto de Bing Y la capa del
		   tema del mes. Eso era lo que hacía que "no se viera el fondo": aquí no
		   se veía nunca porque nada de lo de abajo era visible a través de él.
		   Si algún día se toca este orden, se revisa con la foto puesta.
		2. `.capa-img` — la foto de Bing, sobre el cielo, al 0.6 para que se lea
		   desde el otro lado de la oficina (estaba al 0.34 y con el gradiente
		   encima ni se notaba que estaba).
		3. `.capa-tema` + `.tinte-tema` — el tema del mes, como adorno encima.
		4. `.capa-vineta` — la que protege la legibilidad del texto.
	-->
	<div class="capa-gradiente g-{periodo}" aria-hidden="true"></div>
	{#if fondoActual()}
		<div class="capa-img" style="background-image:url('{fondoActual()}')" aria-hidden="true"></div>
	{/if}
	{#if siguiente >= 0 && siguiente !== actual}
		<div class="capa-img encima" style="background-image:url('{fondos[siguiente] ?? ''}');opacity:{progreso}" aria-hidden="true"></div>
	{/if}
	<!--
		Tema del mes: tinte radial + la capa de motivos, sobre la foto y antes
		del gradiente/vineta. Con la viñeta encima, el texto de las pantallas se
		lee igual de bien que sin tema: es una capa de ambiente, no un filtro.
	-->
	{#if tema?.capa}
		<div class="capa-tema" style="background-image:url('{tema.capa}')" aria-hidden="true"></div>
		<div class="tinte-tema" style="--tinte:{tema.tinte}" aria-hidden="true"></div>
	{/if}
	<div class="capa-vineta" class:tenue aria-hidden="true"></div>

	<!-- Efectos de clima: ambiente, no decoración. Movimientos lentos. -->
	<div class="clima" aria-hidden="true">
		{#if soleado}
			<div class="sol-rayos"></div>
			<div class="sol-resplandor"></div>
		{/if}
		{#if nublado}
			<div class="nube n1"></div>
			<div class="nube n2"></div>
			<div class="nube n3"></div>
		{/if}
		{#if lluvioso}
			{#each gotas as g}
				<div class="gota" style="left:{g.x}%;animation-duration:{g.dur}s;animation-delay:{g.delay}s;opacity:{g.op}"></div>
			{/each}
			<div class="lluvia-velo"></div>
		{/if}
	</div>
</div>

<style>
	.fondo { position: absolute; inset: 0; overflow: hidden; background: #0F172A; }
	.capa-img {
		position: absolute; inset: -2%;
		background-size: cover; background-position: center; background-repeat: no-repeat;
		/* 0.6 y no 0.34: la foto de Bing es de las pocas cosas que le dan
		   carácter a la pantalla, y al 0.34 no se veía ni de cerca. El gradiente
		   de la hora va DEBAJO (ver el orden en el markup), así que ya no hace
		   falta bajar tanto la foto para que el texto se lea: para eso está la
		   viñeta, que va encima de todo. */
		opacity: 0.6; filter: saturate(1.08);
		transition: opacity 0.8s ease;
	}
	/* El crossfade lo lleva el inline style (rAF), no una transición: si
	   hubiera transición, las dos capas se pelearían por la opacidad. */
	.capa-img.encima { transition: none; }

	.capa-tema {
		position: absolute; inset: 0;
		background-size: cover; background-position: center; background-repeat: no-repeat;
		/* 1.0 a propósito: los motivos se generan con opacidad baja, y con la
		   viñeta encima (que es fuerte) un 0.55 aquí los volvía invisibles
		   desde el otro lado de la oficina. La viñeta es la que protege la
		   legibilidad del texto, no esta capa. */
		opacity: 1;
	}
	/* Segundo velo de tinte, encima del que ya trae el PNG. Con 34%/24% los dos
	   juntos tapaban la foto de Bing por completo: la imagen del fondo tiene que
	   seguir siendo lo que se ve, el tema sólo va de adorno encima. */
	.tinte-tema {
		position: absolute; inset: 0;
		background:
			radial-gradient(120% 85% at 12% 8%, color-mix(in srgb, var(--tinte) 12%, transparent) 0%, transparent 55%),
			radial-gradient(110% 80% at 88% 92%, color-mix(in srgb, var(--tinte) 9%, transparent) 0%, transparent 55%);
	}

	/* Gradiente base por hora del día: es el fondo cuando no hay imagen local. */
	.capa-gradiente { position: absolute; inset: 0; }
	.capa-gradiente.g-dawn  { background: linear-gradient(180deg, #1a1033 0%, #2d1b4e 20%, #4a2066 40%, #7b3f72 60%, #c4724e 80%, #f0a050 100%); }
	.capa-gradiente.g-day   { background: linear-gradient(180deg, #0c1929 0%, #132743 30%, #1a3a5c 60%, #1E293B 100%); }
	.capa-gradiente.g-dusk  { background: linear-gradient(180deg, #0F172A 0%, #1a1033 20%, #4a1942 45%, #8b2500 70%, #cc5500 100%); }
	.capa-gradiente.g-night { background: linear-gradient(180deg, #020617 0%, #0a0f1e 30%, #0F172A 60%, #111827 100%); }

	/* Velo oscuro: sin esto el texto compite con la foto de Bing. */
	.capa-vineta {
		position: absolute; inset: 0;
		background:
			radial-gradient(120% 90% at 50% 0%, rgba(15,23,42,0.25) 0%, rgba(15,23,42,0.72) 60%, rgba(2,6,23,0.92) 100%),
			linear-gradient(180deg, rgba(15,23,42,0.5) 0%, rgba(15,23,42,0.75) 100%);
		transition: opacity 1.2s ease;
	}
	.capa-vineta.tenue { opacity: 0.72; }

	.clima { position: absolute; inset: 0; pointer-events: none; }

	.sol-rayos {
		position: absolute; top: -240px; right: -240px; width: 680px; height: 680px;
		background: conic-gradient(from 0deg, transparent, rgba(255,200,50,0.13), transparent, rgba(255,150,0,0.09), transparent, rgba(255,200,50,0.13), transparent);
		border-radius: 50%; animation: girar 70s linear infinite;
	}
	.sol-resplandor {
		position: absolute; top: 70px; right: 110px; width: 150px; height: 150px;
		background: radial-gradient(circle, rgba(255,220,100,0.28) 0%, rgba(255,180,50,0.09) 50%, transparent 70%);
		border-radius: 50%; animation: latir 5s ease-in-out infinite;
	}
	.nube {
		position: absolute; width: 340px; height: 90px; border-radius: 60px;
		background: rgba(148,163,184,0.05); filter: blur(26px);
	}
	.n1 { top: 12%; left: -340px; animation: derivar 55s linear infinite; }
	.n2 { top: 34%; left: -440px; animation: derivar 72s linear infinite; animation-delay: 12s; width: 440px; }
	.n3 { top: 62%; left: -280px; animation: derivar 64s linear infinite; animation-delay: 28s; }

	.gota {
		position: absolute; top: -24px; width: 2px; height: 22px;
		background: linear-gradient(180deg, transparent, rgba(120,190,255,0.7));
		border-radius: 0 0 2px 2px; animation-name: caer; animation-timing-function: linear;
		animation-iteration-count: infinite;
	}
	.lluvia-velo { position: absolute; inset: 0; background: rgba(6,14,32,0.22); }

	@keyframes girar { to { transform: rotate(360deg); } }
	@keyframes latir { 0%,100% { transform: scale(1); opacity: 0.8; } 50% { transform: scale(1.14); opacity: 1; } }
	@keyframes derivar { from { transform: translateX(0); } to { transform: translateX(calc(100vw + 800px)); } }
	@keyframes caer { 0% { transform: translateY(-24px); } 100% { transform: translateY(1080px); } }
</style>
