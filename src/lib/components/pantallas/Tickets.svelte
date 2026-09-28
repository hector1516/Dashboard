<!--
	🎫 Tickets OxxoGas de la semana.

	Rejilla compacta con la foto del ticket arriba: a 3 metros interesa más la
	foto que el folio. Los tres más recientes reciben un borde brillante
	("reciénregistered") para que se note la actividad del momento.
-->
<script lang="ts">
	import { anchoTickets, thumbTicket } from '$lib/kiosk/api';
	import { recortar, num } from '$lib/kiosk/format';
	import type { Snapshot, Ticket } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const t = $derived(datos.tickets);
	const ancho = $derived(anchoTickets(datos as any));
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
					{#if tk.tiene_foto}
						<div class="foto"><img class="foto-img" src={thumbTicket(tk.id_ticket, ancho)} alt={tk.folio} loading="lazy" /></div>
					{/if}
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
			<div class="kpi orange" style="min-width:200px">
				<span class="kpi-val">{num(t.total_semana)}</span>
				<span class="kpi-lab">tickets esta semana</span>
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
	.rejilla {
		flex: 1; min-height: 0; display: grid; gap: 10px; align-content: start;
		grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); overflow: hidden;
	}
	.tkt {
		display: flex; flex-direction: column; gap: 2px; padding: 10px 12px; border-radius: 12px;
		background: rgba(245,158,11,0.06); border: 1px solid rgba(245,158,11,0.14);
		animation: entrarStagger 0.45s cubic-bezier(0.16, 1, 0.3, 1) both;
		position: relative; overflow: hidden;
	}
	.tkt.reciente { border-color: rgba(255,174,0,0.55); box-shadow: 0 0 18px rgba(255,174,0,0.18); }
	.foto { margin: -10px -12px 6px; border-radius: 12px 12px 0 0; overflow: hidden; max-height: 96px; background: #0F172A; }
	.foto-img { width: 100%; height: 96px; object-fit: cover; display: block; }
	.folio { font-weight: 800; color: var(--color-primary-light); font-size: 16px; }
	.vehiculo { font-weight: 700; color: var(--color-text); font-size: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.usuario { font-size: 13px; color: #CBD5E1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.cliente { font-size: 12.5px; color: var(--color-text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.desc { font-size: 12px; color: #64748B; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.fecha { font-size: 11px; color: #475569; margin-top: 2px; }

	.pie { display: flex; align-items: center; gap: 20px; flex-shrink: 0; padding-top: 4px; }
	.barra-lateral { flex: 1; display: flex; flex-direction: column; gap: 6px; }
	.barra-lateral .bar-fila { grid-template-columns: 190px 1fr 90px; }
</style>
