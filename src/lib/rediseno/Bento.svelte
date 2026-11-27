<script lang="ts">
	import type { Snippet } from 'svelte';
	interface Props {
		children: Snippet;
		/** Filas de la retícula. 3 por omisión; Uso de apps usa 4. */
		filas?: number;
	}
	let { children, filas = 3 }: Props = $props();
</script>

<main class="bento" style="grid-template-rows: repeat({filas}, 1fr)">{@render children()}</main>

<style>
	.bento {
		flex: 1; min-height: 0;
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		grid-template-rows: repeat(3, 1fr);
		gap: var(--k-gap);
		padding: var(--k-gap) 32px;
	}
</style>
