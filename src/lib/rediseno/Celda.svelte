<script lang="ts">
	import type { Snippet } from 'svelte';
	interface Props {
		area: string;
		rotulo: string;
		tono?: '' | 'dark' | 'red';
		i?: number;
		children: Snippet;
	}
	let { area, rotulo, tono = '', i = 0, children }: Props = $props();
</script>

<section class="cell {tono}" style="grid-area:{area};--i:{i}">
	<div class="lbl">{rotulo}</div>
	{@render children()}
</section>

<style>
	.cell {
		min-height: 0; border-radius: var(--k-radio); background: var(--k-sup);
		padding: 24px 28px; display: flex; flex-direction: column; gap: 10px;
		box-shadow: 0 2px 0 rgba(18,20,26,.05), 0 22px 44px -26px rgba(18,20,26,.5);
		overflow: hidden;
		animation: caer .45s cubic-bezier(.2,.9,.3,1.2) both;
		animation-delay: calc(var(--i, 0) * 35ms);
	}
	@keyframes caer {
		from { opacity: 0; transform: translateY(-12px) scale(.985); }
		to   { opacity: 1; transform: none; }
	}
	@media (prefers-reduced-motion: reduce) { .cell { animation: none; } }
	.cell.dark { background: var(--k-tinta); color: #f7f3ea; }
	.cell.red { background: var(--k-rojo); color: #fff; }
	.lbl { font-size: var(--k-f-strip); font-weight: 800; letter-spacing: 1.7px; text-transform: uppercase; opacity: .55; }
</style>
