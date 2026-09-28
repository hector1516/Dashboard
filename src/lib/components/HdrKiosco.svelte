<!--
	Header del kiosco: marca, pantalla actual, reloj, estado del snapshot y
	controles de sonido.

	La franja de estado usa los MISMOS tokens y colores que el banner del
	ECCSA-Shell (`.sync-header`): verde/ámbar/rojo con el punto de estado. No
	importa el componente del shell porque ese es un botón de sincronización
	con usuario y sesión, y aquí no hay ninguno: esto es solo la lectura del
	estado, que es lo que el contrato pide para una app sin sesión
	(docs/CONTRATO.md §2b).
-->
<script lang="ts">
	interface Props {
		pantallaIcono: string;
		pantallaLabel: string;
		reloj: string;
		fecha: string;
		/** Índice 1..N de la rotación, para el "3/10" del footer. */
		posicion: string;
		/** Estado de salud del snapshot. */
		degradado: string[];
		generadoEn: string;
		antiguedad: string;
		silenciado: boolean;
		volumen: number;
		bloqueado: boolean;
		onSilenciar: () => void;
		onVolumen: (v: number) => void;
		onAudioDesbloquear: () => void;
	}

	let {
		pantallaIcono,
		pantallaLabel,
		reloj,
		fecha,
		posicion,
		degradado,
		generadoEn,
		antiguedad,
		silenciado,
		volumen,
		bloqueado,
		onSilenciar,
		onVolumen,
		onAudioDesbloquear
	}: Props = $props();

	let abierto = $state(false);

	const ok = $derived(degradado.length === 0);
	const aviso = $derived(degradado.length > 0 && !degradado.includes('bd'));

	/**
	 * "datos de hace 4 min" / "datos viejos": el texto que evita que alguien
	 * tome los ceros de una pantalla sin refresco como si fueran reales.
	 */
	function datosLabel(): string {
		return degradado.length ? `datos viejos · ${antiguedad}` : `datos de ${antiguedad}`;
	}
</script>

<header class="hdr">
	<div class="izq">
		<span class="marca">ECCSA</span>
		<span class="sep">|</span>
		<span class="pantalla"><span class="ic">{pantallaIcono}</span> {pantallaLabel}</span>
	</div>

	<div class="centro">
		<span class="reloj">{reloj}</span>
		<span class="fecha">{fecha}</span>
	</div>

	<div class="der">
		<!-- Salud del snapshot: si algo falló, se ve, no se disimula. -->
		<span class="salud" class:ok class:aviso title={ok ? 'Todos los refrescos bien' : `Degradado: ${degradado.join(', ')}`}>
			<span class="punto" class:ok class:aviso></span>
			{datosLabel()}
		</span>
		<span class="sep">|</span>
		<span class="pos">{posicion}</span>
		<span class="sep">|</span>

		<button class="icono" onclick={onSilenciar} title={silenciado ? 'Activar sonido' : 'Silenciar'}>
			{silenciado ? '🔇' : '🔊'}
		</button>
		<button class="icono slider" onclick={() => (abierto = !abierto)} title="Volumen">
			<div class="barra" style="--v:{silenciado ? 0 : volumen}">
				<span class="relleno" style="width:{silenciado ? 0 : volumen * 100}%"></span>
			</div>
		</button>
		{#if abierto}
			<div class="pop">
				<input
					type="range"
					min="0"
					max="1"
					step="0.05"
					value={volumen}
					oninput={(e) => onVolumen(parseFloat((e.currentTarget as HTMLInputElement).value))}
				/>
				<span class="vol-texto">{Math.round(volumen * 100)}%</span>
			</div>
		{/if}
	</div>
</header>

{#if bloqueado}
	<button class="chip-audio" onclick={onAudioDesbloquear}>
		🔇 Toca para activar el sonido
	</button>
{/if}

<style>
	.hdr {
		display: flex; align-items: center; justify-content: space-between;
		padding: 0 28px; height: 56px; flex-shrink: 0;
		background: rgba(15, 23, 42, 0.72);
		backdrop-filter: blur(18px);
		border-bottom: 1px solid rgba(255, 107, 0, 0.18);
		color: var(--color-text-muted);
		position: relative; z-index: 20;
	}
	.izq, .der { display: flex; align-items: center; gap: 14px; }
	.centro { display: flex; align-items: baseline; gap: 16px; }
	.marca {
		font-size: 20px; font-weight: 900; letter-spacing: 0.06em;
		background: linear-gradient(90deg, var(--color-primary), var(--color-primary-light));
		-webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
	}
	.sep { color: #334155; }
	.pantalla { font-size: 17px; font-weight: 600; color: var(--color-text); }
	.ic { font-size: 20px; }
	.reloj {
		font-size: 30px; font-weight: 800; color: var(--color-primary-light);
		font-variant-numeric: tabular-nums; letter-spacing: 1px; line-height: 1;
	}
	/* Sin `capitalize`: en español solo va mayúscula el día, no cada palabra. */
	.fecha { font-size: 16px; }
	.pos { font-size: 15px; font-variant-numeric: tabular-nums; }

	/* Estado de salud: mismos colores que los estados del banner del shell. */
	.salud {
		display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 600;
		padding: 5px 12px; border-radius: 999px;
		background: rgba(245, 158, 11, 0.16); color: #FCD34D;
		border: 1px solid rgba(245, 158, 11, 0.35);
	}
	.salud.ok { background: rgba(30, 41, 59, 0.58); color: var(--color-text-muted); border-color: rgba(255,255,255,0.1); }
	.punto { width: 9px; height: 9px; border-radius: 50%; background: var(--color-danger); }
	.punto.aviso { background: var(--color-warning); }
	.punto.ok { background: var(--color-success); box-shadow: 0 0 8px rgba(34, 197, 94, 0.6); }

	.icono {
		background: transparent; border: 1px solid rgba(255,255,255,0.12);
		color: var(--color-text); border-radius: 8px; cursor: pointer;
		font-size: 15px; padding: 4px 8px; line-height: 1; min-height: 30px;
	}
	.icono:hover { background: rgba(255,255,255,0.08); }
	.slider { display: flex; align-items: center; padding: 8px; }
	.barra { display: block; width: 54px; height: 6px; border-radius: 3px; background: rgba(255,255,255,0.15); overflow: hidden; }
	.relleno { display: block; height: 100%; background: linear-gradient(90deg, var(--color-primary), var(--color-primary-light)); transition: width 0.2s; }

	.pop {
		position: absolute; right: 20px; top: 50px; z-index: 40;
		display: flex; align-items: center; gap: 10px;
		background: var(--color-surface); border: 1px solid rgba(255,107,0,0.3);
		border-radius: 12px; padding: 10px 14px; box-shadow: 0 12px 30px rgba(0,0,0,0.5);
	}
	.pop input { width: 140px; accent-color: var(--color-primary); }
	.vol-texto { font-size: 13px; color: var(--color-text-muted); min-width: 34px; }

	.chip-audio {
		position: absolute; right: 24px; top: 68px; z-index: 60;
		background: rgba(255,107,0,0.2); color: var(--color-primary-light);
		border: 1px solid rgba(255,107,0,0.5); border-radius: 999px;
		padding: 8px 16px; font-size: 14px; font-weight: 700; cursor: pointer;
		animation: latirChip 2s ease-in-out infinite;
	}
	@keyframes latirChip { 0%,100% { opacity: 0.75; } 50% { opacity: 1; } }
</style>
