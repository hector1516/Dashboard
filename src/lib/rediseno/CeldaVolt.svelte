<script lang="ts">
	// La celda que llena el hueco inferior derecho de la retícula: The Penguin
	// y sus últimas tres notificaciones, cada una con su hora.
	//
	// Es la ÚNICA representación de The Penguin en las pantallas del bento (el
	// personaje 3D y el globo flotante se retiraron). Por eso la marca es el
	// pingüino en un círculo naranja: pesa cero y no tapa nada.
	//
	// El historial lo llena `voltAviso.ts`: presencia, tickets, avisos del
	// vigilante y «sin internet». Aquí sólo se pinta, sin peticiones propias.
	import { onMount } from 'svelte';
	import Celda from './Celda.svelte';
	import { voltHistorial, type AvisoVolt } from '$lib/kiosk/voltAviso';

	interface Props {
		/**
		 * Área de la retícula. El hueco normal es 3/4/4/5; en Equipo el hueco
		 * es de dos columnas (3/3/4/5) y se pasa ese valor para no dejar un
		 * segundo recuadro vacío.
		 */
		area?: string;
		/** Orden de la animación de caída. Va al final de la retícula. */
		i?: number;
	}
	let { area = '3/4/4/5', i = 9 }: Props = $props();

	let avisos = $state<AvisoVolt[]>([]);
	onMount(() => voltHistorial.subscribe((v) => (avisos = v)));
</script>

<Celda {area} {i} rotulo="The Penguin · últimas notificaciones">
	<div class="volt">
		<div class="marca" aria-hidden="true">
			<!-- La marca de The Penguin: el emoji 🐧 dentro del círculo
			     naranja. Sin rayos. -->
			<span class="pinguino">🐧</span>
		</div>

		{#if avisos.length === 0}
			<div class="sin-avisos">
				<b>Sin novedades</b>
				<span>Los avisos de The Penguin aparecerán aquí.</span>
			</div>
		{:else}
			<div class="lista">
				{#each avisos as a, n (a.texto + n)}
					<div class="fila">
						<span class="texto">{a.texto}</span>
						<span class="hora">{a.hora}</span>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</Celda>

<style>
	.volt {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	/* El pingüino en un círculo naranja de marca. Con 30 px deja sitio a
	   las tres filas: la celda 1×1 mide ~289 px de alto. */
	.marca {
		width: 30px;
		height: 30px;
		flex: 0 0 30px;
		border-radius: 50%;
		background: var(--k-rojo);
		color: var(--k-tinta);
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 2px 0 rgba(18, 20, 26, 0.08);
	}
	.pinguino {
		font-size: 20px;
		line-height: 1;
	}

	.lista {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
		justify-content: flex-start;
		gap: 0;
	}
	.fila {
		display: flex;
		align-items: flex-start;
		gap: 12px;
		padding: 4px 0;
		border-bottom: 1px solid rgba(18, 20, 26, 0.08);
	}
	.fila:last-child {
		border-bottom: 0;
	}
	/* 20 px: el mínimo del sistema. Dos líneas como tope y elipsis; la hora
	   no se parte ni se recorta. */
	.texto {
		flex: 1;
		min-width: 0;
		font-size: 20px;
		font-weight: 600;
		line-height: 1.2;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	.hora {
		flex: 0 0 auto;
		font-size: 20px;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
		/* Gris legible sobre blanco: 4.6:1. */
		color: rgba(18, 20, 26, 0.55);
		padding-top: 1px;
	}

	.sin-avisos {
		margin: auto 0;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.sin-avisos b {
		font-size: 24px;
		font-weight: 800;
		opacity: 0.45;
	}
	.sin-avisos span {
		font-size: 20px;
		font-weight: 600;
		opacity: 0.4;
	}
</style>
