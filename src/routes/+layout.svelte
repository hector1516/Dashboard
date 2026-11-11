<!--
	Layout raiz del kiosco.

	Ni splash ni banner: las dos cosas que_FIELD_ pone bien en un celular son
	ruido en una TV del pasillo

	  - el splash con frases geek tarda 3.6 s en una pantalla que se enciende
	    sola cada manana, y
	  - el banner `.sync-header` del ECCSA-Shell es un BOTON de sincronizacion
	    de una app con sesion: en el kiosco no hay ni usuario ni cola (la
	    sincronizacion es del servidor), as que no se monta.

	Lo que si se cumple del contrato del shell es lo que importa: `src/app.css`
	es el CSS del shell (tokens y componentes), la tipografia es la del shell
	(self-hosted), y `GET /api/shell/state` existe y responde. La version de
	app y de shell se ven en el pie de la pantalla, que es el lugar donde
	sirven cuando no hay nadie que haga clic.
	Ver ECCSA-Shell/docs/CONTRATO.md 2b.
-->
<script lang="ts">
	// ORDEN IMPORTA: primero el CSS del ECCSA-Shell (tokens + componentes) y
	// despues kiosk.css, que se apoya en esos tokens y solo anade lo propio de
	// la pantalla. Sin este import los `var(--color-*)` no existian y los
	// colores Salientes se veian grises (el circulo de los avatares, el nombre
	// del autor en fotos, los estados del header).
	import '../app.css';
	import '$lib/kiosk/kiosk.css';
	import VoltComentario from '$lib/components/VoltComentario.svelte';

	let { children } = $props();

	// Wobnimo: mascota 3D Volt para el kiosco
	import { mascotState } from '$lib/kiosk/mascot';
	import { voltPosition, startWalking, stopWalking, prefersReducedMotion } from '$lib/kiosk/voltWalker';
	import { onMount, onDestroy } from 'svelte';

	let mascotContainer: HTMLDivElement | null = $state(null);
	let mascotInstance: any = null;
	let currentState = $state('idle');
	let walkerX = $state(0);
	let walkerY = $state(0);

	// Sync store to local state
	$effect(() => {
		currentState = $mascotState;
		if (mascotInstance && typeof mascotInstance.setState === 'function') {
			mascotInstance.setState(currentState);
		}
	});

	// Sync walker position to CSS transform
	$effect(() => {
		const pos = $voltPosition;
		walkerX = pos.x;
		walkerY = pos.y;
	});

	// Cargar Wobnimo al montar
	onMount(async () => {
		try {
			const [wobnimo, voltModule] = await Promise.all([
				import('https://cdn.jsdelivr.net/npm/wobnimo@0.2/dist/wobnimo.js'),
				import('https://cdn.jsdelivr.net/npm/wobnimo@0.2/dist/characters/volt.js')
			]);
			if (mascotContainer && voltModule.volt && wobnimo.mount) {
				mascotInstance = wobnimo.mount(mascotContainer, voltModule.volt);
				mascotInstance.setState(currentState);
			}
		} catch (e) {
			console.error('Wobnimo load error:', e);
		}

		// Iniciar caminata si no hay preferencia de movimiento reducido
		if (!prefersReducedMotion()) {
			startWalking();
		}
	});

	onDestroy(() => {
		stopWalking();
	});

	// Actualizar estado de la mascota
	$effect(() => {
		if (mascotInstance && typeof mascotInstance.setState === 'function') {
			mascotInstance.setState(mascotState);
		}
	});
</script>

{@render children()}

<!-- Mascota Volt (camina por la pantalla) -->
<div class="wobnimo-kiosk" bind:this={mascotContainer} style="transform: translate({walkerX}px, {walkerY}px);">
</div>

<!-- Comentarios aleatorios de Volt -->
<VoltComentario />

<style>
	.wobnimo-kiosk {
		position: fixed;
		top: 0;
		left: 0;
		width: 180px;
		height: 180px;
		z-index: 9999;
		pointer-events: none;
		transition: transform 0.05s linear;
		will-change: transform;
	}
	.wobnimo-kiosk .mascot-fallback {
		font-size: 3rem;
		opacity: 0.5;
	}
</style>