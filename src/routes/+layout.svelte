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
	import { stopWalking } from '$lib/kiosk/voltWalker';
	import { onMount, onDestroy } from 'svelte';
	import { logError, ERROR_CODES } from '$lib/audit.js';

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
	onMount(async () => {
		// Captura global de errores del kiosco (DSH-UI-001 / DSH-NET-001)
		if (typeof window !== 'undefined') {
			window.addEventListener('error', (ev) => {
				try { logError(ERROR_CODES.UI_ERROR, 'layout', ev.message || 'window error', { filename: ev.filename, lineno: ev.lineno }); } catch {}
			});
			window.addEventListener('unhandledrejection', (ev) => {
				try { logError(ERROR_CODES.NET_ERROR, 'layout', String(ev.reason?.message || ev.reason || 'unhandled rejection'), { reason: String(ev.reason) }); } catch {}
			});
		}
		// El personaje se sirve desde el propio contenedor (`static/vendor`), no
		// desde un CDN: la regla del kiosco es no depender de internet. El CDN
		// queda solo como respaldo por si el archivo local faltara.
		const baseLocal = '/vendor/wobnimo';
		const intentos: Array<[string, string]> = [
			[`${baseLocal}/wobnimo.js`, `${baseLocal}/characters/volt.js`],
			[
				'https://cdn.jsdelivr.net/npm/wobnimo@0.2/dist/wobnimo.js',
				'https://cdn.jsdelivr.net/npm/wobnimo@0.2/dist/characters/volt.js'
			]
		];
		for (const [urlLib, urlPersonaje] of intentos) {
			try {
				const [wobnimo, voltModule] = await Promise.all([
					import(/* @vite-ignore */ urlLib),
					import(/* @vite-ignore */ urlPersonaje)
				]);
				if (mascotContainer && voltModule.volt && wobnimo.mount) {
					mascotInstance = wobnimo.mount(mascotContainer, voltModule.volt);
					mascotInstance.setState(currentState);
					break;
				}
			} catch (e) {
				console.error('Wobnimo no cargó desde', urlLib, e);
			}
		}

		// Volt NO camina: vive en su esquina, siempre en el mismo lugar, para no
		// tapar datos ni obligar a nadie a seguirlo con la vista.
		stopWalking();
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

<!-- Volt: fijo en su esquina, en su placa. Nunca se mueve ni se superpone
     con el contenido porque tiene un fondo sólido propio. -->
<div class="volt-dock" aria-hidden="true">
	<div class="wobnimo-kiosk" bind:this={mascotContainer}></div>
	<div class="volt-fallback">⚡</div>
</div>

<!-- Comentarios aleatorios de Volt -->
<VoltComentario />

<style>
	/* La placa de Volt: ocupa su rincón y tapa lo que haya debajo con fondo
	   sólido, en vez de mezclarse con el dato. */
	.volt-dock {
		position: fixed;
		right: 18px;
		bottom: 18px;
		width: 112px;
		height: 112px;
		z-index: 400;
		border-radius: 22px;
		background: #fffdf8;
		border: 2px solid #141414;
		box-shadow: 4px 4px 0 #141414;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
		pointer-events: none;
	}
	.volt-fallback {
		position: absolute;
		font-size: 44px;
		line-height: 1;
		opacity: 0;
	}
	/* Sin el personaje 3D (sin internet), Volt sigue ahí como rayo. */
	.wobnimo-kiosk:empty + .volt-fallback { opacity: 1; }
	.wobnimo-kiosk {
		position: absolute;
		inset: 0;
		width: 112px;
		height: 112px;
		z-index: 1;
		pointer-events: none;
		transition: transform 0.05s linear;
		will-change: transform;
	}
	.wobnimo-kiosk .mascot-fallback {
		font-size: 3rem;
		opacity: 0.5;
	}
</style>