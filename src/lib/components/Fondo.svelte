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
	}

	let { fondos, periodo, lluvioso, soleado, nublado, tenue }: Props = $props();

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
	{#if fondoActual()}
		<div class="capa-img" style="background-image:url('{fondoActual()}')" aria-hidden="true"></div>
	{/if}
	{#if siguiente >= 0 && siguiente !== actual}
		<div class="capa-img encima" style="background-image:url('{fondos[siguiente] ?? ''}');opacity:{progreso}" aria-hidden="true"></div>
	{/if}
	<div class="capa-gradiente g-{periodo}" aria-hidden="true"></div>
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
		opacity: 0.34; filter: saturate(1.05);
		transition: opacity 0.8s ease;
	}
	/* El crossfade lo lleva el inline style (rAF), no una transición: si
	   hubiera transición, las dos capas se pelearían por la opacidad. */
	.capa-img.encima { transition: none; }

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
