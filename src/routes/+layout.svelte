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

	The Penguin ya NO flota: ni personaje 3D en el rincon ni globo encima. Las
	notificaciones se cuentan en la celda `CeldaVolt` de cada pantalla y el
	sondeo que las alimenta vive en `voltVigia.ts` (sin DOM).
-->
<script lang="ts">
	// ORDEN IMPORTA: primero el CSS del ECCSA-Shell (tokens + componentes) y
	// despues kiosk.css, que se apoya en esos tokens y solo anade lo propio de
	// la pantalla. Sin este import los `var(--color-*)` no existian y los
	// colores Salientes se veian grises (el circulo de los avatares, el nombre
	// del autor en fotos, los estados del header).
	import '../app.css';
	import '$lib/kiosk/kiosk.css';
	import { onMount } from 'svelte';
	import { logError, ERROR_CODES } from '$lib/audit.js';
	import { iniciarVoltVigia } from '$lib/kiosk/voltVigia';

	let { children } = $props();

	onMount(() => {
		// Captura global de errores del kiosco (DSH-UI-001 / DSH-NET-001)
		if (typeof window !== 'undefined') {
			window.addEventListener('error', (ev) => {
				try { logError(ERROR_CODES.UI_ERROR, 'layout', ev.message || 'window error', { filename: ev.filename, lineno: ev.lineno }); } catch {}
			});
			window.addEventListener('unhandledrejection', (ev) => {
				try { logError(ERROR_CODES.NET_ERROR, 'layout', String(ev.reason?.message || ev.reason || 'unhandled rejection'), { reason: String(ev.reason) }); } catch {}
			});
		}

		// El sondeo de The Penguin (avisos del vigilante, internet, audio) corre una
		// sola vez para todo el kiosco: el historial sobrevive a la rotación.
		return iniciarVoltVigia();
	});
</script>

{@render children()}
