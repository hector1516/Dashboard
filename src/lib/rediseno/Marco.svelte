<script lang="ts">
	// Marco común de las pantallas del rediseño: barra de 76 px arriba,
	// contenido en medio y pie de Volt abajo. Es tonto a propósito: no
	// consulta el snapshot ni el reloj; todo le llega por props, para que
	// cada pantalla pueda probarse con datos de ejemplo.
	//
	// El rincón inferior derecho (148 × 148 px) se RESERVA para Volt: aquí
	// no se dibuja nada y el pie termina antes de esa zona. El tablero que
	// va en `children` también debe dejar ese cuadro libre.
	import type { Snippet } from 'svelte';
	import PieVolt from './PieVolt.svelte';

	interface Props {
		/** Nombre de la pantalla que se está viendo. */
		titulo: string;
		/** Hora del kiosco, ya formateada (`12:29`). */
		reloj: string;
		/** Fecha larga, ya formateada (`miércoles 25 de noviembre`). */
		fecha: string;
		/** Cuánto hace que se generó el snapshot (`datos de hace 1 min`). */
		antiguedad: string;
		/** Vales sin foto. Solo el número, nunca el monto. */
		sinFoto: number;
		/** Posición en la rotación (`1/9`). */
		posicion: string;
		/** La frase de Volt del pie. Sin ella el pie queda en «— Volt». */
		volt?: string;
		children: Snippet;
	}
	let { titulo, reloj, fecha, antiguedad, sinFoto, posicion, volt = '', children }: Props =
		$props();
</script>

<div class="marco">
	<header class="top">
		<div class="marca">
			<img src="/icon-192x192.png" alt="" width="38" height="38" />
			<b>ECCSA</b>
		</div>
		<span class="sep"></span>
		<div class="donde">
			<div class="pant">{titulo}</div>
			<div class="fecha">{fecha}</div>
		</div>
		<div class="reloj">{reloj}</div>
		<div class="der">
			<div class="chip punto">{antiguedad}</div>
			<div class="chip" class:rojo={sinFoto > 0}>{sinFoto} sin foto</div>
			<div class="chip borde">{posicion}</div>
		</div>
	</header>

	<div class="contenido">
		{@render children()}
	</div>

	<PieVolt linea={volt} />
</div>

<style>
	.marco {
		/* Cuadro que Volt ocupa en la esquina (dock de 112 px + márgenes).
		   Lo usan el pie y, a través de la herencia, el tablero de cada
		   pantalla: nadie dibuja dentro. */
		--k-volt: 148px;
		position: relative;
		width: 100%;
		height: 100%;
		min-height: 0;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		background: var(--k-base);
		color: var(--k-tinta);
		font-family: var(--font-family, 'Outfit', system-ui, sans-serif);
	}

	/* ── barra ─────────────────────────────────────────────────── */
	.top {
		height: var(--k-marco);
		flex: 0 0 var(--k-marco);
		display: flex;
		align-items: center;
		gap: 14px;
		padding: 0 32px;
		border-bottom: 1px solid rgba(18, 20, 26, 0.08);
	}

	.marca {
		display: flex;
		align-items: center;
		gap: 12px;
	}
	.marca img {
		width: 38px;
		height: 38px;
		border-radius: 11px;
	}
	.marca b {
		font-size: 22px;
		font-weight: 900;
		letter-spacing: 0.5px;
	}

	.sep {
		width: 1px;
		height: 26px;
		background: rgba(18, 20, 26, 0.16);
		margin: 0 8px;
	}

	.donde {
		display: flex;
		flex-direction: column;
		gap: 1px;
	}
	.pant {
		font-size: 24px;
		font-weight: 600;
		line-height: 1.15;
		opacity: 0.7;
	}
	.fecha {
		font-size: var(--k-f-strip);
		font-weight: 600;
		line-height: 1.15;
		opacity: 0.5;
	}

	.reloj {
		position: absolute;
		left: 50%;
		top: 12px;
		transform: translateX(-50%);
		font-size: 48px;
		font-weight: 900;
		line-height: 1.1;
		letter-spacing: -1.5px;
		font-variant-numeric: tabular-nums;
	}

	.der {
		margin-left: auto;
		display: flex;
		align-items: center;
		gap: 12px;
	}
	.chip {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		height: 38px;
		padding: 0 16px;
		border-radius: 999px;
		font-size: var(--k-f-strip);
		font-weight: 700;
		white-space: nowrap;
		background: rgba(18, 20, 26, 0.06);
		color: var(--k-tinta);
	}
	/* Rojo solo cuando hay algo pendiente: «0 sin foto» es una buena
	   noticia y no se pinta como alarma. */
	.chip.rojo {
		background: var(--k-rojo);
		color: #fff;
	}
	.chip.borde {
		background: transparent;
		box-shadow: inset 0 0 0 2px rgba(18, 20, 26, 0.12);
	}
	.chip.punto::before {
		content: '';
		width: 9px;
		height: 9px;
		border-radius: 50%;
		background: var(--k-verde);
	}

	/* ── contenido ─────────────────────────────────────────────── */
	.contenido {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
	}
</style>
