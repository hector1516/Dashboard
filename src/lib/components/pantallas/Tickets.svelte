<!--
	🎫 Tickets OxxoGas de la semana.

	Rejilla de tarjetas de texto, SIN foto del ticket (decisión del 2026-09-28):
	la imagen de `HUB_OxxoGasTickets.ImagenTicket` no sirve en varios registros
	—viene con 15 bytes basura antes del JPEG— y a 3 metros el folio, el vehículo
	y el cliente se leen mejor que una foto chiquita. Los tres más recientes
	reciben un borde brillante para que se note la actividad del momento.
-->
<script lang="ts">
	import { recortar, num } from '$lib/kiosk/format';
	import type { Snapshot, Ticket } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const t = $derived(datos.tickets);
	const lista = $derived(t.ultimos ?? []);
	const maxTickets = $derived(Math.max(1, ...(t.por_vehiculo ?? []).map((x) => x.total_tickets || 0)));

	/** Los 3 primeros de la lista son los más nuevos: se marcan. */
	function esReciente(i: number): boolean {
		return i < 3;
	}
</script>

<div class="screen">
	<div class="screen-titulo"><span class="ic">🎫</span> Tickets OxxoGas — Esta Semana</div>

	{#if lista.length}
		<div class="rejilla">
			{#each lista as tk, i}
				<div class="tkt" class:reciente={esReciente(i)} style="animation-delay:{i * 0.05}s">
					<div class="folio">{tk.folio}</div>
					<div class="vehiculo">{tk.vehiculo}</div>
					<div class="usuario">👤 {tk.usuario}</div>
					<div class="cliente">{recortar(tk.cliente, 28) || '—'}</div>
					<div class="desc">{recortar(tk.descripcion, 34) || '—'}</div>
					<div class="fecha">{tk.fecha?.replace('T', ' ')}</div>
				</div>
			{/each}
		</div>

		<div class="pie">
			<div class="kpi orange" style="min-width:210px">
				<span class="kpi-val">{num(t.total_semana)}</span>
				<span class="kpi-lab">{t.total_semana === 1 ? 'ticket esta semana' : 'tickets esta semana'}</span>
			</div>
			<div class="barra-lateral">
				{#each (t.por_vehiculo ?? []).slice(0, 5) as x, i}
					{@const p = Math.round(((x.total_tickets || 0) / maxTickets) * 100)}
					<div class="bar-fila" style="animation-delay:{i * 0.06}s">
						<span class="bar-lab">{x.vehiculo}</span>
						<div class="bar-pista"><div class="bar-relleno ticket" style="width:{Math.max(p, 4)}%"></div></div>
						<span class="bar-val ticket">{x.total_tickets} tkt</span>
					</div>
				{/each}
			</div>
		</div>
	{:else}
		<div class="vacio">
			Sin tickets esta semana
			<span class="vacio-sub">Se muestran los registrados o sincronizados desde el correo</span>
		</div>
	{/if}
</div>

<style>
	/* Sin foto la tarjeta es sólo texto: se angosta y caben más por pantalla.
	   `auto-fit` + `justify-content: center` para que con POCOS tickets (lunes a
	   la mañana suele haber uno o dos) el bloque quede centrado y no perdido
	   contra el borde izquierdo. */
	.rejilla {
		flex: 1; min-height: 0; display: grid; gap: 12px; align-content: center;
		grid-template-columns: repeat(auto-fit, minmax(215px, 250px));
		justify-content: center; overflow: hidden;
	}
	.tkt {
		display: flex; flex-direction: column; justify-content: center; gap: 3px;
		padding: 12px 14px; border-radius: 12px; min-height: 104px;
		background: rgba(245,158,11,0.06); border: 1px solid rgba(245,158,11,0.14);
		animation: entrarStagger 0.45s cubic-bezier(0.16, 1, 0.3, 1) both;
		position: relative; overflow: hidden;
	}
	.tkt.reciente { border-color: rgba(255,174,0,0.55); box-shadow: 0 0 18px rgba(255,174,0,0.18); }
	.folio { font-weight: 800; color: var(--color-primary-light); font-size: 17px; }
	.vehiculo { font-weight: 700; color: var(--color-text); font-size: 16px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.usuario { font-size: 13.5px; color: #CBD5E1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.cliente { font-size: 13px; color: var(--color-text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.desc { font-size: 12.5px; color: #64748B; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.fecha { font-size: 11.5px; color: #475569; margin-top: 3px; }

	.pie { display: flex; align-items: center; gap: 20px; flex-shrink: 0; padding-top: 4px; }
	.barra-lateral { flex: 1; display: flex; flex-direction: column; gap: 6px; }
	.barra-lateral .bar-fila { grid-template-columns: 190px 1fr 90px; }
</style>
