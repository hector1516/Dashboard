<script lang="ts">
	// Marco común de las pantallas del rediseño: barra de 76 px arriba,
	// contenido en medio y pie de Volt abajo. Es tonto a propósito: no
	// consulta el snapshot ni el reloj; todo le llega por props, para que
	// cada pantalla pueda probarse con datos de ejemplo.
	//
	// El rincón inferior derecho ya no se reserva: ahí va la celda `CeldaVolt`
	// dentro de la retícula. El pie ocupa todo el ancho.
	import type { Snippet } from 'svelte';
	import PieVolt from './PieVolt.svelte';

	interface Props {
		/** Nombre de la pantalla que se está viendo. */
		titulo: string;
		/** Hora del kiosco, ya formateada en 12 h (`5:34 p.m.`). */
		reloj: string;
		/** Fecha larga, ya formateada (`miércoles 25 de noviembre`). */
		fecha: string;
		/** Cuánto hace que se generó el snapshot (`datos de hace 1 min`). */
		antiguedad: string;
		/** Temperatura de ahora, a la derecha del reloj. Sin dato no se pinta. */
		temperatura?: number | null;
		/** Posición en la rotación (`1/9`). */
		posicion: string;
		/** Bloques degradados del snapshot (`['bd']`, `['clima']`…). */
		degradado?: string[];
		/** La frase de Volt del pie. Sin ella el pie queda en «— Volt». */
		volt?: string;
		/** Portada: sin la firma de Volt en el pie (ahí Volt no aparece). */
		sinVolt?: boolean;
		children: Snippet;
	}
	let {
		titulo,
		reloj,
		fecha,
		antiguedad,
		temperatura = null,
		posicion,
		degradado = [],
		volt = '',
		sinVolt = false,
		children
	}: Props = $props();

	/**
	 * ¿El snapshot tiene más de ~10 min? Se lee del texto ya armado («datos de
	 * hace 12 min»): el marco no consulta el reloj ni `generado_en`. A partir de
	 * ahí el chip de antigüedad se pinta ámbar, porque un tablero de hace un
	 * cuarto de hora ya no es «la oficina ahora mismo».
	 */
	const viejo = $derived.by(() => {
		const m = /(\d+)\s*(min|h|d)/i.exec(antiguedad ?? '');
		if (!m) return false;
		const n = Number(m[1]);
		const u = m[2].toLowerCase();
		return u === 'h' || u === 'd' || (u === 'min' && n >= 10);
	});
	/** El punto solo es verde si no hay nada degradado: ámbar cuando sí. */
	const hayDegradado = $derived((degradado ?? []).length > 0);
</script>

<div class="marco">
	<header class="top">
		<div class="marca">
			<!-- La marca, no el icono de la app: el engranaje ECCSA a 56 px,
			     sin marco redondeado, y el nombre al lado. Los
			     `icon-*.png` del proyecto siguen siendo placeholders. -->
			<img src="/eccsa-mark.svg" alt="ECCSA" width="56" height="56" />
			<b>ECCSA</b>
		</div>
		<span class="sep"></span>
		<div class="donde">
			<div class="pant">{titulo}</div>
			<div class="fecha">{fecha}</div>
		</div>
		<div class="centro">
			<div class="reloj">{reloj}</div>
			{#if temperatura != null && Number.isFinite(temperatura)}
				<span class="sep-temp"></span>
				<!-- Entero: el kiosco no muestra «18.7°». El decimal no se lee a
				     3 metros y ensancha la barra sin decir nada más. -->
				<div class="temp">{Math.round(temperatura)}°</div>
			{/if}
		</div>
		<div class="der">
			<div class="chip punto" class:ambar={hayDegradado || viejo}>
				{antiguedad}
			</div>
			<div class="chip borde">{posicion}</div>
		</div>
	</header>

	<div class="contenido">
		{@render children()}
	</div>

	<PieVolt linea={volt} {sinVolt} />
</div>

<style>
	.marco {
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
		width: 56px;
		height: 56px;
		/* Sin marco redondeado: es la marca, no el icono de una app. */
		object-fit: contain;
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

	.centro {
		position: absolute;
		left: 50%;
		top: 12px;
		transform: translateX(-50%);
		display: flex;
		align-items: baseline;
		gap: 16px;
	}
	.reloj {
		font-size: 48px;
		font-weight: 900;
		line-height: 1.1;
		letter-spacing: -1.5px;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}
	/* Separador fino entre la hora y la temperatura. */
	.sep-temp {
		align-self: center;
		width: 1px;
		height: 30px;
		background: rgba(18, 20, 26, 0.18);
	}
	.temp {
		font-size: 34px;
		font-weight: 800;
		line-height: 1.1;
		letter-spacing: -1px;
		font-variant-numeric: tabular-nums;
		opacity: 0.85;
		white-space: nowrap;
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
	/* Snapshots degradados o viejos: el punto deja de ser verde y el chip se
	   tiñe de ámbar. El verde es «todo bien», y eso no se finge. */
	.chip.punto.ambar {
		background: rgba(217, 154, 0, 0.18);
	}
	.chip.punto.ambar::before {
		background: var(--k-ambar);
	}

	/* ── contenido ─────────────────────────────────────────────── */
	.contenido {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
	}
</style>
