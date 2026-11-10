<script lang="ts">
	import { mascotState } from '$lib/kiosk/mascot';
	import { getVoltComentario } from '$lib/kiosk/voltComentarios';

	// Muestra comentarios aleatorios de Volt cada 30-60 segundos
	let visible = $state(false);
	let texto = $state('');
	let timer: ReturnType<typeof setTimeout>;

	function mostrarComentario() {
		texto = getVoltComentario('idle');
		visible = true;
		mascotState.set('speaking');
		// Ocultar después de 5 segundos
		setTimeout(() => {
			visible = false;
			mascotState.set('idle');
		}, 10000);
		// Programar siguiente comentario (30-60s)
		const delay = 30000 + Math.random() * 30000;
		timer = setTimeout(mostrarComentario, delay);
	}

	import { onMount, onDestroy } from 'svelte';
	onMount(() => {
		// Primer comentario después de 15s
		timer = setTimeout(mostrarComentario, 15000);
	});
	onDestroy(() => {
		clearTimeout(timer);
	});
</script>

{#if visible}
	<div class="volt-comentario">
		<div class="comentario-bubble">
			<span class="comentario-texto">💬 {texto}</span>
		</div>
		<div class="comentario-flecha"></div>
	</div>
{/if}

<style>
	.volt-comentario {
		position: fixed;
		bottom: 260px;
		right: 60px;
		z-index: 50;
		max-width: 480px;
		animation: entraComentario 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
	}

	.comentario-bubble {
		background: rgba(15, 23, 42, 0.92);
		border: 1px solid rgba(255, 255, 255, 0.15);
		border-radius: 16px;
		padding: 18px 24px;
		color: var(--color-text);
		font-size: 18px;
		font-style: italic;
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
		backdrop-filter: blur(8px);
	}

	.comentario-texto {
		line-height: 1.4;
	}

	.comentario-flecha {
		position: absolute;
		bottom: -8px;
		right: 40px;
		width: 0;
		height: 0;
		border-left: 8px solid transparent;
		border-right: 8px solid transparent;
		border-top: 8px solid rgba(15, 23, 42, 0.92);
	}

	@keyframes entraComentario {
		from { opacity: 0; transform: translateY(10px) scale(0.95); }
		to { opacity: 1; transform: none; }
	}
</style>