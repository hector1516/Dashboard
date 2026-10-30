<!--
	🎫 Tickets OxxoGas — Últimos 10 registrados.

	Rejilla de tarjetas con información ampliada: folio, vehículo, usuario,
	cliente, descripción, fecha y datos del vale asociado.
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

	/** URL de la imagen del ticket (si el backend la sirve). */
	function imagenUrl(id: number): string {
		return `/api/tickets/${id}/imagen`;
	}
</script>

<div class="screen">
	<div class="screen-titulo"><span class="ic">🎫</span> Tickets OxxoGas — Últimos 10</div>

	{#if lista.length}
		<div class="rejilla">
			{#each lista as tk, i}
				<TicketCard
					folio={tk.folio}
					vehiculo={tk.vehiculo}
					usuario={tk.usuario}
					cliente={recortar(tk.cliente, 28) || '—'}
					descripcion={recortar(tk.descripcion, 34) || '—'}
					fecha={tk.fecha}
					reciente={esReciente(i)}
					fecha_vale={tk.fecha_vale}
					estatus_vale={tk.estatus_vale}
					monto_vale={tk.monto_vale}
					imagen_url={imagenUrl(tk.id_ticket ?? 0)}
				/>
			{/each}
		</div>

		<div class="pie">
			<div class="kpi orange" style="min-width:210px">
				<span class="kpi-val">{num(t.total_semana)}</span>
				<span class="kpi-lab">{t.total_semana === 1 ? 'ticket total' : 'tickets total'}</span>
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
			Sin tickets registrados
			<span class="vacio-sub">Se muestran los registrados o sincronizados desde el correo</span>
		</div>
	{/if}
</div>

<style>
	.rejilla {
		flex: 1; min-height: 0; display: grid; gap: 14px; align-content: center;
		grid-template-columns: repeat(auto-fit, minmax(280px, 340px));
		justify-content: center; overflow: hidden;
	}
	.pie { display: flex; align-items: center; gap: 20px; flex-shrink: 0; padding-top: 4px; }
	.barra-lateral { flex: 1; display: flex; flex-direction: column; gap: 6px; }
	.barra-lateral .bar-fila { grid-template-columns: 190px 1fr 90px; }
</style>
