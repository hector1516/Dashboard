<!--
	🆕 Pulso — "la oficina ahora".

	La pantalla que hace que el kiosco parezca vivo: no es un tablero de la
	semana, es el momento. Último evento, movimiento de la última hora, quién
	está trabajando y en qué clientes. Se apoya en los MISMOS datos que ya se
	consumían en las otras pantallas (no agrega queries nuevas): es una
	recomposición, no un módulo de datos nuevo.

	Entra dos veces por vuelta de rotación: es el latido de fondo.
-->
<script lang="ts">
	import { num, hhmm } from '$lib/kiosk/format';
	import type { Snapshot } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	let ahora = $state(Date.now());
	// Latido propio: las etiquetas "hace X min" se refrescan aunque el snapshot
	// no cambie (lo cual pasa cuando la BD está lenta, no debería notarse).
	$effect(() => {
		const t = setInterval(() => (ahora = Date.now()), 5000);
		return () => clearInterval(t);
	});

	const km = $derived(datos.kilometros);
	const activos = $derived(
		km.por_vehiculo.filter((v) => {
			if (!v.ultimo_registro) return false;
			const h = (ahora - Date.parse(v.ultimo_registro.replace(' ', 'T'))) / 3600000;
			return h <= 24;
		})
	);

	/** Cuántos eventos hubo en los últimos 60 min, a partir del pulso horario. */
	const porHora = $derived(datos.metricas.pulso ?? []);
	const horaActual = $derived(new Date(ahora).getHours());
	const diaActual = $derived(new Date(ahora).getDay());
	const actividad = $derived(porHora.find((p) => p.dia === diaActual && p.hora === horaActual)?.valor ?? 0);
</script>

<div class="screen">
	<div class="screen-titulo"><span class="ic">⚡</span> La Oficina Ahora</div>

	<div class="cuerpo">
		<!-- Última actividad -->
		<div class="card grande">
			<div class="etiqueta">Último movimiento en ECCSA</div>
			{#if datos.metricas.ultimo_evento}
				<div class="evento-texto">{datos.metricas.ultimo_evento.texto}</div>
				<!-- `meta` ya viene formateado por el backend ("hace 4 min") -->
				<div class="evento-meta">{datos.metricas.ultimo_evento.meta}</div>
			{:else}
				<div class="evento-texto tenue">Sin movimientos registrados</div>
			{/if}
			<div class="rejilla-mini">
				<div class="mini">
					<span class="mini-val">{num(actividad)}</span>
					<span class="mini-lab">eventos en esta hora</span>
				</div>
				<div class="mini">
					<span class="mini-val">{num(km.hoy)}</span>
					<span class="mini-lab">km hoy</span>
				</div>
				<div class="mini">
					<span class="mini-val">{num(datos.reportes.hoy)}</span>
					<span class="mini-lab">reportes hoy</span>
				</div>
			</div>
		</div>

		<!-- Flota activa -->
		<div class="card lista">
			<div class="etiqueta">Flota con registro en las últimas 24 h · {activos.length}</div>
			<div class="scroll">
				{#each activos as v, i}
					<div class="fila-veh" style="animation-delay:{i * 0.05}s">
						<span class="luz"></span>
						<div class="veh-info">
							<span class="veh-nom">{v.MarcaModelo}</span>
							<span class="veh-placas">{v.Placas}</span>
						</div>
						<div class="veh-dato">+{num(v.consumo_7d ?? v.consumo_semana)} km</div>
						<div class="veh-hora">{hhmm(v.ultimo_registro)}</div>
					</div>
				{/each}
				{#if !activos.length}
					<div class="tenue vacio-mini">Nadie ha registrado kilómetros en 24 h</div>
				{/if}
			</div>
		</div>

		<!-- Lo que se está haciendo ahora -->
		<div class="card lista">
			<div class="etiqueta">Últimos tickets y reportes</div>
			<div class="scroll">
				{#each datos.tickets.ultimos.slice(0, 6) as t, i}
					<div class="fila-ev" style="animation-delay:{i * 0.05}s">
						<span class="ev-ic">🎫</span>
						<div class="ev-info">
							<span class="ev-tit">{t.folio} · {t.vehiculo}</span>
							<span class="ev-sub">{t.cliente || '—'} · {t.usuario}</span>
						</div>
						<div class="ev-hora">{hhmm(t.fecha)}</div>
					</div>
				{/each}
				{#each datos.reportes.ultimos.slice(0, 6) as r, i}
					<div class="fila-ev" style="animation-delay:{(i + 6) * 0.05}s">
						<span class="ev-ic">📊</span>
						<div class="ev-info">
							<span class="ev-tit">{r.Folio} · {r.Cliente}</span>
							<span class="ev-sub">{r.ingeniero} · {r.Estatus}</span>
						</div>
						<div class="ev-hora">{r.fecha}</div>
					</div>
				{/each}
			</div>
		</div>
	</div>
</div>

<style>
	.cuerpo { flex: 1; min-height: 0; display: grid; grid-template-columns: 1.15fr 1fr 1fr; gap: 16px; }
	.etiqueta { font-size: 14px; font-weight: 800; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
	.tenue { color: #475569; }

	/* El texto del último evento va centrado verticalmente: si queda pegado al
	   borde superior con 700 px de tarjetas abajo, se ve roto. */
	.grande { padding: 24px 28px; display: flex; flex-direction: column; gap: 14px; justify-content: space-between; }
	.evento-texto { font-size: 34px; font-weight: 800; color: var(--color-text); line-height: 1.25; flex: 1; display: flex; align-items: center; }
	.evento-meta { font-size: 16px; color: var(--color-text-muted); }
	.rejilla-mini { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: auto; }
	.mini {
		display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 14px 8px;
		border-radius: 14px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07);
	}
	.mini-val { font-size: 32px; font-weight: 900; color: var(--color-primary-light); font-variant-numeric: tabular-nums; }
	.mini-lab { font-size: 12.5px; color: var(--color-text-muted); text-align: center; }

	.lista { padding: 18px 20px; display: flex; flex-direction: column; gap: 10px; min-height: 0; }
	.scroll { flex: 1; min-height: 0; display: flex; flex-direction: column; gap: 8px; overflow: hidden; justify-content: flex-start; }
	.fila-veh, .fila-ev {
		display: flex; align-items: center; gap: 12px; padding: 9px 12px; border-radius: 11px;
		background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06);
		animation: entrarStagger 0.45s cubic-bezier(0.16, 1, 0.3, 1) both;
	}
	.luz { width: 10px; height: 10px; border-radius: 50%; background: #22C55E; box-shadow: 0 0 9px rgba(34,197,94,0.65); flex-shrink: 0; }
	.veh-info, .ev-info { flex: 1; min-width: 0; display: flex; flex-direction: column; }
	.veh-nom, .ev-tit { font-weight: 700; font-size: 16px; color: var(--color-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.veh-placas, .ev-sub { font-size: 13px; color: var(--color-text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.veh-dato { font-size: 15px; font-weight: 800; color: #4ADE80; font-variant-numeric: tabular-nums; }
	.veh-hora, .ev-hora { font-size: 13px; color: #64748B; font-variant-numeric: tabular-nums; flex-shrink: 0; }
	.ev-ic { font-size: 22px; }
	.vacio-mini { font-size: 16px; padding: 20px 0; text-align: center; }
</style>
