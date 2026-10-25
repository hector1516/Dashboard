<!--
	Avatar ECCSA — personaje simple que reacciona a eventos del kiosco.
	Estilo: mascota minimalista (círculo + ojos + boca) con animaciones suaves.
	Se monta una sola vez en +page.svelte y vive en una esquina.
-->
<script lang="ts">
	import { onMount, onDestroy } from 'svelte';

	interface Props {
		/** Tipo de evento actual para reaccionar. */
		evento?: string | null;
		/** Nombre de la persona a saludar (opcional). */
		persona?: string | null;
	}

	let { evento = null, persona = null }: Props = $props();

	// Posición del mouse (para seguir el cursor)
	let mouseX = $state(0);
	let mouseY = $state(0);
	let avatarX = $state(0);
	let avatarY = $state(0);

	// Transform calculada para el inline style
	let avatarTransform = $state('translate(0px, 0px)');

	// Estado emocional
	let estado = $state<'idle' | 'feliz' | 'alerta' | 'celebrando'>('idle');
	let mensaje = $state('');

	// Reaccionar a eventos
	$effect(() => {
		if (!evento) {
			estado = 'idle';
			mensaje = '';
			return;
		}
		const e = evento.toLowerCase();
		if (e.includes('firmado') || e.includes('reporte')) {
			estado = 'feliz';
			mensaje = '¡Reporte firmado!';
		} else if (e.includes('cumple') || e.includes('aniversario')) {
			estado = 'celebrando';
			mensaje = persona ? `¡Feliz cumple, ${persona}!` : '¡Celebración!';
		} else if (e.includes('entrada') || e.includes('salida')) {
			estado = 'alerta';
			mensaje = persona ? `${persona} ${e.includes('entrada') ? 'entró' : 'salió'}` : '';
		} else {
			estado = 'idle';
			mensaje = '';
		}
	});

	// Seguir el mouse suavemente
	let rafId: number | null = null;
	function seguirMouse() {
		avatarX += (mouseX - avatarX) * 0.08;
		avatarY += (mouseY - avatarY) * 0.08;
		avatarTransform = `translate(${avatarX}px, ${avatarY}px)`;
		rafId = requestAnimationFrame(seguirMouse);
	}

	function onMouseMove(e: MouseEvent) {
		mouseX = (e.clientX / window.innerWidth - 0.5) * 20;
		mouseY = (e.clientY / window.innerHeight - 0.5) * 20;
	}

	onMount(() => {
		window.addEventListener('mousemove', onMouseMove);
		rafId = requestAnimationFrame(seguirMouse);
	});

	onDestroy(() => {
		window.removeEventListener('mousemove', onMouseMove);
		if (rafId) cancelAnimationFrame(rafId);
	});
</script>

<div class="avatar-wrap" style="transform: {avatarTransform}">
	<svg class="avatar" class:estado-{estado} viewBox="0 0 120 120" width="120" height="120">
		<!-- Cuerpo (blob) -->
		<ellipse cx="60" cy="70" rx="40" ry="35" class="cuerpo" />
		<!-- Cabeza -->
		<circle cx="60" cy="45" r="30" class="cabeza" />
		<!-- Ojos -->
		<g class="ojos">
			<circle cx="50" cy="40" r="5" class="ojo" />
			<circle cx="70" cy="40" r="5" class="ojo" />
			<circle cx="50" cy="40" r="2.5" class="pupila" />
			<circle cx="70" cy="40" r="2.5" class="pupila" />
		</g>
		<!-- Boca -->
		<path class="boca" d="M 48 52 Q 60 62 72 52" />
		<!-- Brillo (glow) -->
		<circle cx="60" cy="45" r="32" class="glow" />
	</svg>
	{#if mensaje}
		<div class="burbuja">{mensaje}</div>
	{/if}
</div>

<style>
	.avatar-wrap {
		position: fixed;
		bottom: 24px;
		right: 24px;
		z-index: 50;
		pointer-events: none;
		transition: transform 0.1s ease-out;
	}

	.avatar {
		filter: drop-shadow(0 4px 12px rgba(255, 107, 0, 0.3));
	}

	.cuerpo {
		fill: #1E293B;
		stroke: #FF6B00;
		stroke-width: 2;
	}

	.cabeza {
		fill: #334155;
		stroke: #FFAE00;
		stroke-width: 2;
	}

	.ojo {
		fill: #F8FAFC;
	}

	.pupila {
		fill: #0F172A;
	}

	.boca {
		fill: none;
		stroke: #F8FAFC;
		stroke-width: 2;
		stroke-linecap: round;
	}

	.glow {
		fill: none;
		stroke: rgba(255, 107, 0, 0.15);
		stroke-width: 3;
	}

	/* Idle: respiración suave */
	.avatar.estado-idle .cabeza {
		animation: respirar 3s ease-in-out infinite;
	}
	.avatar.estado-idle .pupila {
		animation: parpadear 4s ease-in-out infinite;
	}

	/* Feliz: sonrisa */
	.avatar.estado-feliz .boca {
		d: path("M 48 50 Q 60 65 72 50");
		animation: sonreir 0.5s ease;
	}
	.avatar.estado-feliz .glow {
		stroke: rgba(34, 197, 94, 0.4);
	}

	/* Celebrando: rebote */
	.avatar.estado-celebrando {
		animation: celebrar 0.6s ease-in-out 3;
	}
	.avatar.estado-celebrando .boca {
		d: path("M 45 48 Q 60 68 75 48");
	}
	.avatar.estado-celebrando .glow {
		stroke: rgba(255, 174, 0, 0.6);
		animation: glow-pulso 0.6s ease-in-out infinite;
	}

	/* Alerta: ojos grandes */
	.avatar.estado-alerta .ojo {
		r: 6;
	}
	.avatar.estado-alerta .pupila {
		r: 3;
	}
	.avatar.estado-alerta .glow {
		stroke: rgba(59, 130, 246, 0.4);
	}

	@keyframes respirar {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-2px); }
	}
	@keyframes parpadear {
		0%, 90%, 100% { transform: scaleY(1); }
		95% { transform: scaleY(0.1); }
	}
	@keyframes sonreir {
		0% { transform: scale(1); }
		50% { transform: scale(1.1); }
		100% { transform: scale(1); }
	}
	@keyframes celebrar {
		0%, 100% { transform: translateY(0) rotate(0deg); }
		25% { transform: translateY(-8px) rotate(-5deg); }
		75% { transform: translateY(-8px) rotate(5deg); }
	}
	@keyframes glow-pulso {
		0%, 100% { opacity: 0.4; }
		50% { opacity: 1; }
	}

	.burbuja {
		position: absolute;
		bottom: 130px;
		right: 0;
		background: rgba(30, 41, 59, 0.9);
		color: #F8FAFC;
		padding: 8px 14px;
		border-radius: 12px;
		font-size: 14px;
		font-weight: 600;
		white-space: nowrap;
		border: 1px solid rgba(255, 107, 0, 0.3);
		animation: aparecer 0.3s ease;
	}

	@keyframes aparecer {
		0% { opacity: 0; transform: translateY(10px); }
		100% { opacity: 1; transform: translateY(0); }
	}
</style>