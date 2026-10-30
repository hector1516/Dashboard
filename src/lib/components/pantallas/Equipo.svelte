<!-- Equipo.svelte - Pantalla fusionada: Legends + Celebraciones + Notas -->
<script lang="ts">
	import { onMount } from 'svelte';
	import type { Snapshot } from '$lib/kiosk/types';
	import Legends from '$lib/components/pantallas/Legends.svelte';
	import Celebraciones from '$lib/components/pantallas/Celebraciones.svelte';
	import Notas from '$lib/components/pantallas/Notas.svelte';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	let seccion = $state(0);
	const secciones = ['Legends', 'Celebraciones', 'Notas'];

	let timer: ReturnType<typeof setInterval>;
	onMount(() => {
		timer = setInterval(() => {
			seccion = (seccion + 1) % secciones.length;
		}, 15000);
		return () => clearInterval(timer);
	});
</script>

<div class="screen equipo">
	<div class="screen-titulo">
		<span class="ic">👥</span> Equipo — {secciones[seccion]}
		<div class="tabs">
			{#each secciones as s, i}
				<button class="tab" class:active={seccion === i} onclick={() => (seccion = i)}>{s}</button>
			{/each}
		</div>
	</div>

	<div class="contenido">
		{#if seccion === 0}
			<Legends {datos} />
		{:else if seccion === 1}
			<Celebraciones {datos} />
		{:else if seccion === 2}
			<Notas {datos} />
		{/if}
	</div>
</div>

<style>
	.equipo { display: flex; flex-direction: column; height: 100%; }
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
