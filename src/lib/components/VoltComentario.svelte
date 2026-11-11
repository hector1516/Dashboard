<script lang="ts">
	import { mascotState } from '$lib/kiosk/mascot';
	import { getVoltComentario, getVoltComentarioPantalla } from '$lib/kiosk/voltComentarios';
	import { pauseWalking, resumeWalking, voltPosition } from '$lib/kiosk/voltWalker';
	import { currentScreen } from '$lib/kiosk/currentScreen';

	// Muestra comentarios aleatorios de Volt cada 30-60 segundos
	let visible = $state(false);
	let texto = $state('');
	let reaccion = $state('💬');
	let timer: ReturnType<typeof setTimeout>;
	let bubbleX = $state(0);
	let bubbleY = $state(0);

	const REACCIONES = ['💬', '🤔', '😊', '⚡', '🤖', '💡', '🎯', '👀', '🔥', '✨', '🎉', '☕'];

	function mostrarComentario() {
		// 50% probabilidad de comentario sobre la pantalla actual, 50% idle/usuario
		const screen = $currentScreen;
		if (Math.random() < 0.5 && screen) {
			texto = getVoltComentarioPantalla(screen);
		} else {
			// Mezclar entre idle y comentarios de usuarios
			const tipos = ['idle', 'entrada', 'salida', 'usuario_nuevo', 'usuario_inactivo'];
			const tipo = tipos[Math.floor(Math.random() * tipos.length)];
			texto = getVoltComentario(tipo);
		}
		reaccion = REACCIONES[Math.floor(Math.random() * REACCIONES.length)];
		visible = true;
		pauseWalking();
		mascotState.set('speaking');
		// Ocultar despues de 12 segundos
		setTimeout(() => {
			visible = false;
			mascotState.set('idle');
			resumeWalking();
		}, 12000);
		// Programar siguiente comentario (10-20s)
		const delay = 10000 + Math.random() * 10000;
		timer = setTimeout(mostrarComentario, delay);
	}

	// Seguir la posicion de Volt
	$effect(() => {
		const pos = $voltPosition;
		// Posicionar el globo encima de Volt (180px de ancho)
		bubbleX = pos.x + 90; // centro de Volt
		bubbleY = pos.y - 20; // encima de Volt
	});

	import { onMount, onDestroy } from 'svelte';
	onMount(() => {
		// Primer comentario despues de 5s
		timer = setTimeout(mostrarComentario, 5000);
	});
	onDestroy(() => {
		clearTimeout(timer);
	});
</script>

{#if visible}
	<div class="volt-comentario" style="left: {bubbleX}px; top: {bubbleY}px; transform: translate(-50%, -100%);">
		<div class="comentario-avatar">
			<span class="avatar-icon">🤖</span>
		</div>
		<div class="comentario-bubble">
			<span class="comentario-reaccion">{reaccion}</span>
			<span class="comentario-texto">{texto}</span>
		</div>
		<div class="comentario-flecha"></div>
	</div>
{/if}

<style>
	.volt-comentario {
		position: fixed;
		z-index: 50;
		max-width: 480px;
		pointer-events: none;
		transition: left 0.1s linear, top 0.1s linear;
		animation: entraComentario 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 4px;
	}

	.comentario-avatar {
		width: 40px;
		height: 40px;
		border-radius: 50%;
		background: rgba(255, 107, 0, 0.2);
		border: 2px solid rgba(255, 107, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.4rem;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
	}

	.comentario-bubble {
		background: rgba(15, 23, 42, 0.92);
		border: 1px solid rgba(255, 255, 255, 0.15);
		border-radius: 16px;
		padding: 14px 20px;
		color: var(--color-text);
		font-size: 16px;
		font-style: italic;
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
		backdrop-filter: blur(8px);
		display: flex;
		align-items: flex-start;
		gap: 8px;
		max-width: 440px;
	}

	.comentario-reaccion {
		font-size: 1.3rem;
		flex-shrink: 0;
		line-height: 1.2;
	}

	.comentario-texto {
		line-height: 1.4;
	}

	.comentario-flecha {
		width: 0;
		height: 0;
		border-left: 8px solid transparent;
		border-right: 8px solid transparent;
		border-top: 8px solid rgba(15, 23, 42, 0.92);
		margin-top: -1px;
	}

	@keyframes entraComentario {
		from { opacity: 0; transform: translate(-50%, -80%) scale(0.9); }
		to { opacity: 1; transform: translate(-50%, -100%) scale(1); }
	}
</style>