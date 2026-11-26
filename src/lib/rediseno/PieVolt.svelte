<script lang="ts">
	// Pie del marco: la línea de The Penguin a la izquierda y la versión a la
	// derecha. 42 px de alto y 20 px de letra (nada baja de 20 px).
	//
	// Ya no reserva el rincón derecho: el personaje flotante se retiró y su
	// hueco lo ocupa la celda `CeldaVolt` dentro de la retícula. La portada
	// pasa `sinVolt`, porque ahí The Penguin no aparece en ninguna parte.
	import { APP_VERSION } from '$lib/shell.js';

	interface Props {
		/** Lo que dice The Penguin. Puede venir vacío: entonces solo firma. */
		linea: string;
		/** Sin la firma de The Penguin (portada). Queda solo la versión. */
		sinVolt?: boolean;
	}
	let { linea, sinVolt = false }: Props = $props();
</script>

<footer class="pie">
	{#if !sinVolt}
		<span class="volt">
			— <b>The Penguin</b>{#if linea}: {linea}{/if}
		</span>
	{/if}
	<span class="fin">ECCSA · Centro de Operaciones · v{APP_VERSION}</span>
</footer>

<style>
	.pie {
		height: var(--k-pie);
		flex: 0 0 var(--k-pie);
		display: flex;
		align-items: center;
		gap: 14px;
		padding: 0 32px;
		font-size: var(--k-f-strip);
		font-weight: 600;
		opacity: 0.62;
	}

	.volt {
		font-style: italic;
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.volt b {
		font-style: normal;
		font-weight: 800;
		opacity: 0.85;
	}

	.fin {
		margin-left: auto;
		flex: 0 0 auto;
		white-space: nowrap;
	}
</style>
