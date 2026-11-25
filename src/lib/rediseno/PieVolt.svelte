<script lang="ts">
	// Pie del marco: la línea de Volt a la izquierda y la versión a la
	// derecha. 42 px de alto y 20 px de letra (nada baja de 20 px).
	//
	// No llega hasta el borde derecho: el último tramo es el cuadro que
	// Volt ocupa en su esquina, así que el pie termina antes. Es el único
	// elemento del marco que se mete hacia dentro por ese motivo.
	import { APP_VERSION } from '$lib/shell.js';

	interface Props {
		/** Lo que dice Volt. Puede venir vacío: entonces solo firma. */
		linea: string;
	}
	let { linea }: Props = $props();
</script>

<footer class="pie">
	<span class="volt">
		— <b>Volt</b>{#if linea}: {linea}{/if}
	</span>
	<span class="fin">ECCSA · Centro de Operaciones · v{APP_VERSION}</span>
</footer>

<style>
	.pie {
		height: var(--k-pie);
		flex: 0 0 var(--k-pie);
		display: flex;
		align-items: center;
		gap: 14px;
		/* 32 px de margen + el cuadro de Volt (148 px) y 12 px de aire:
		   nada se dibuja bajo el personaje. */
		padding: 0 calc(var(--k-volt, 148px) + 12px) 0 32px;
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
