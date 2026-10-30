<!-- Actividad.svelte - Pantalla fusionada: Reportes + Tickets + Fotos + Metricas -->
<script lang="ts">
	import { onMount } from 'svelte';
	import type { Snapshot } from '$lib/kiosk/types';
	import Reportes from '$lib/components/pantallas/Reportes.svelte';
	import Tickets from '$lib/components/pantallas/Tickets.svelte';
	import Fotos from '$lib/components/pantallas/Fotos.svelte';
	import Metricas from '$lib/components/pantallas/Metricas.svelte';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	let seccion = $state(0);
	const secciones = ['Reportes', 'Tickets', 'Fotos', 'Métricas'];

	let timer: ReturnType<typeof setInterval>;
	onMount(() => {
		timer = setInterval(() => {
			seccion = (seccion + 1) % secciones.length;
		}, 15000);
		return () => clearInterval(timer);
	});
</script>

<div class="screen actividad">
	<div class="screen-titulo">
		<span class="ic">📊</span> Actividad — {secciones[seccion]}
		<div class="tabs">
			{#each secciones as s, i}
				<button class="tab" class:active={seccion === i} onclick={() => (seccion = i)}>{s}</button>
			{/each}
		</div>
	</div>

	<div class="contenido">
		{#if seccion === 0}
			<Reportes {datos} />
		{:else if seccion === 1}
			<Tickets {datos} />
		{:else if seccion === 2}
			<Fotos {datos} />
		{:else if seccion === 3}
			<Metricas {datos} />
		{/if}
	</div>
</div>

<style>
	.actividad { display: flex; flex-direction: column; height: 100%; }
	.screen-titulo { display: flex; align-items: center; gap: 0.5rem; }
	.tabs { display: flex; gap: 0.25rem; margin-left: auto; }
	.tab {
		padding: 0.25rem 0.6rem; border: none; background: transparent;
		color: var(--color-text-muted); font-size: 0.75rem; font-weight: 600;
		border-radius: 6px; cursor: pointer;
	}
	.tab.active { background: rgba(255, 107, 0, 0.15); color: var(--color-primary-light); }
	.tab:hover:not(.active) { color: var(--color-text); }
	.contenido { flex: 1; min-height: 0; overflow: hidden; }
</style>
