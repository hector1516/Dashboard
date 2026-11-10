<script lang="ts">
	import { mascotState } from '$lib/kiosk/mascot';
	import { getVoltComentario, getTipoEvento } from '$lib/kiosk/voltComentarios';
	import type { EventoKiosko } from '$lib/kiosk/types';

	interface Props {
		aviso: EventoKiosko | null;
		onCerrar: () => void;
	}

	let { aviso, onCerrar }: Props = $props();

	let restante = $state(0);
	let visible = $state(false);
	let comentario = $state('');

	// Estado de Volt según el tipo de evento
	$effect(() => {
		if (!aviso) {
			visible = false;
			mascotState.set('idle');
			return;
		}
		visible = true;
		comentario = getVoltComentario(getTipoEvento(aviso));
		// Determinar estado de Volt según el evento
		const titulo = (aviso.titulo || '').toLowerCase();
		const nivel = aviso.nivel || '';
		if (nivel === 'pantalla') {
			if (titulo.includes('cumple') || titulo.includes('aniversario')) {
				mascotState.set('celebrating');
			} else if (titulo.includes('firmado')) {
				mascotState.set('celebrating');
			} else if (titulo.includes('entró') || titulo.includes('entro')) {
				mascotState.set('happy');
			} else if (titulo.includes('salió') || titulo.includes('salio')) {
				mascotState.set('sad');
			} else {
				mascotState.set('surprised');
			}
		} else if (nivel === 'alerta') {
			mascotState.set('error');
		} else {
			mascotState.set('thinking');
		}

		const seg = aviso.segundos ?? 15;
		const t0 = Date.now();
		const paso = () => {
			restante = Math.max(0, seg - Math.floor((Date.now() - t0) / 1000));
			if (restante > 0) requestAnimationFrame(paso);
		};
		requestAnimationFrame(paso);

		// Volver a idle cuando se cierra
		const timer = setTimeout(() => {
			visible = false;
			mascotState.set('idle');
			onCerrar();
		}, seg * 1000);

		return () => clearTimeout(timer);
	});

	function colorDe(nivel: string): string {
		return ({
			info: 'var(--color-info)',
			exito: 'var(--color-success)',
			destaque: 'var(--color-primary-light)',
			alerta: 'var(--color-warning)',
			pantalla: '#16a34a'
		} as Record<string, string>)[nivel] ?? 'var(--color-info)';
	}
</script>

{#if visible && aviso}
	<div class="volt-notif" style="--c:{colorDe(aviso.nivel || 'info')}">
		<div class="volt-notif-bubble">
			{#if aviso.modulo}
				<div class="notif-modulo">{aviso.icono} {aviso.modulo}</div>
			{/if}
			{#if aviso.persona}
				<div class="notif-persona">{aviso.persona}</div>
			{/if}
			<div class="notif-titulo">{aviso.titulo}</div>
			{#if aviso.texto}
				<div class="notif-texto">{aviso.texto}</div>
			{/if}
			{#if aviso.meta}
				<div class="notif-meta">{aviso.meta}</div>
			{/if}
			{#if comentario}
				<div class="notif-comentario">💬 {comentario}</div>
			{/if}
			<div class="notif-pie">
				<div class="notif-barra">
					<span class="lleno" style="width:{restante * 10}%"></span>
				</div>
				<button class="notif-cerrar" onclick={onCerrar}>
					Continuar <span class="cuenta">{restante}s</span>
				</button>
			</div>
		</div>
		<!-- Flecha del speech bubble hacia Volt -->
		<div class="volt-notif-flecha"></div>
	</div>
{/if}

<style>
	.volt-notif {
		position: fixed;
		bottom: 140px;
		right: 20px;
		z-index: 55;
		max-width: 480px;
		animation: entraNotif 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
	}

	.volt-notif-bubble {
		background: color-mix(in srgb, var(--c) 25%, rgba(15, 23, 42, 0.95));
		border: 2px solid color-mix(in srgb, var(--c) 60%, transparent);
		border-radius: 20px;
		padding: 20px 24px;
		color: var(--color-text);
		box-shadow: 0 14px 40px rgba(0, 0, 0, 0.55);
		backdrop-filter: blur(10px);
	}

	.notif-modulo {
		font-size: 16px;
		font-weight: 800;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: rgba(255, 255, 255, 0.72);
		margin-bottom: 4px;
	}

	.notif-persona {
		font-size: 42px;
		font-weight: 800;
		line-height: 1;
		color: #fff;
		text-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
		margin-bottom: 6px;
	}

	.notif-titulo {
		font-size: 28px;
		font-weight: 900;
		color: #fff;
		text-shadow: 0 3px 16px rgba(0, 0, 0, 0.4);
		margin-bottom: 4px;
	}

	.notif-texto {
		font-size: 18px;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.9);
		margin-bottom: 4px;
	}

	.notif-meta {
		font-size: 14px;
		color: rgba(255, 255, 255, 0.6);
		margin-bottom: 8px;
	}
	.notif-comentario {
		font-size: 16px;
		font-style: italic;
		color: rgba(255, 255, 255, 0.85);
		margin-top: 8px;
		padding: 8px 12px;
		background: rgba(255, 255, 255, 0.08);
		border-radius: 8px;
		border-left: 3px solid rgba(255, 255, 255, 0.3);
	}

	.notif-pie {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 8px;
		margin-top: 10px;
	}

	.notif-barra {
		width: 100%;
		height: 4px;
		border-radius: 999px;
		background: rgba(0, 0, 0, 0.35);
		overflow: hidden;
	}

	.notif-barra .lleno {
		display: block;
		height: 100%;
		background: rgba(255, 255, 255, 0.85);
		transition: width 0.3s linear;
	}

	.notif-cerrar {
		font-size: 14px;
		font-weight: 700;
		cursor: pointer;
		color: rgba(255, 255, 255, 0.75);
		background: rgba(0, 0, 0, 0.3);
		border: 1px solid rgba(255, 255, 255, 0.28);
		border-radius: 999px;
		padding: 6px 20px;
	}

	.notif-cerrar:hover { background: rgba(0, 0, 0, 0.5); }

	.volt-notif-flecha {
		position: absolute;
		bottom: -12px;
		right: 40px;
		width: 0;
		height: 0;
		border-left: 12px solid transparent;
		border-right: 12px solid transparent;
		border-top: 12px solid color-mix(in srgb, var(--c) 25%, rgba(15, 23, 42, 0.95));
	}

	@keyframes entraNotif {
		from { opacity: 0; transform: translateY(20px) scale(0.95); }
		to { opacity: 1; transform: none; }
	}
</style>