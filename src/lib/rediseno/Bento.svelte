<script lang="ts">
	import type { Snippet } from 'svelte';
	interface Props { children: Snippet }
	let { children }: Props = $props();
</script>

<main class="bento">{@render children()}</main>

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
