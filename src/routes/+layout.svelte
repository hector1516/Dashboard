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

	let { children } = $props();
</script>

{@render children()}
