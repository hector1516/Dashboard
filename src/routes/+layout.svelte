<!--
	Layout raíz del kiosco.

	Ni splash ni banner: las dos cosas que_FIELD_ pone bien en un celular son
	ruido en una TV del pasillo —

	  · el splash con frases geek tarda 3.6 s en una pantalla que se enciende
	    sola cada mañana, y
	  · el banner `.sync-header` del ECCSA-Shell es un BOTÓN de sincronización
	    de una app con sesión: en el kiosco no hay ni usuario ni cola (la
	    sincronización es del servidor), así que no se monta.

	Lo que sí se cumple del contrato del shell es lo que importa: `src/app.css`
	es el CSS del shell (tokens y componentes), la tipografía es la del shell
	(self-hosted), y `GET /api/shell/state` existe y responde. La versión de
	app y de shell se ven en el pie de la pantalla, que es el lugar donde
	sirven cuando no hay nadie que haga clic.
	Ver ECCSA-Shell/docs/CONTRATO.md §2b.
-->
<script lang="ts">
	// ORDEN IMPORTA: primero el CSS del ECCSA-Shell (tokens + componentes) y
	// después kiosk.css, que se apoya en esos tokens y sólo añade lo propio de
	// la pantalla. Sin este import los `var(--color-*)` no existían y los
	// colores Salientes se veían grises (el círculo de los avatares, el nombre
	// del autor en fotos, los estados del header).
	import '../app.css';
	import '$lib/kiosk/kiosk.css';
	import VoltComentario from '$lib/components/VoltComentario.svelte';

	let { children } = $props();

	// Wobnimo: mascota 3D Volt para el kiosco
	import { mascotState } from '$lib/kiosk/mascot';
	let mascotContainer: HTMLDivElement | null = $state(null);
	let mascotInstance: any = null;
	let currentState = $state('idle');

	// Sync store to local state
	$effect(() => {
		currentState = $mascotState;
		if (mascotInstance && typeof mascotInstance.setState === 'function') {
			mascotInstance.setState(currentState);
		}
	});

	// Cargar Wobnimo al montar
	import { onMount } from 'svelte';
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
	});

	// Actualizar estado de la mascota
	$effect(() => {
		if (mascotInstance && typeof mascotInstance.setState === 'function') {
			mascotInstance.setState(mascotState);
		}
	});
</script>

{@render children()}

<!-- Mascota Volt (esquina inferior derecha, todas las pantallas) -->
<div class="wobnimo-kiosk" bind:this={mascotContainer}>
</div>

<!-- Comentarios aleatorios de Volt -->
<VoltComentario />

<style>
	.wobnimo-kiosk {
		position: fixed;
		bottom: 80px;
		right: 60px;
		width: 180px;
		height: 180px;
		z-index: 9999;
		pointer-events: none;
	}
	.wobnimo-kiosk .mascot-fallback {
		font-size: 3rem;
		opacity: 0.5;
	}
</style>
