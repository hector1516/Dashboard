<!-- Actividad.svelte - Pantalla unificada: Reportes + Tickets + Fotos + Métricas -->
<script lang="ts">
	import { recortar, num, money, pct } from '$lib/kiosk/format';
	import type { Snapshot, Reporte, Ticket } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const r = $derived(datos.reportes);
	const t = $derived(datos.tickets);
	const f = $derived(datos.fotos);
	const m = $derived(datos.metricas);
	const k = $derived(datos.kilometros);

	const reportes = $derived(r.ultimos ?? []);
	const tickets = $derived(t.ultimos ?? []);
	const fotos = $derived(f.ids ?? []);
	const topCliente = $derived(m.top_cliente);
	const topIng = $derived(m.top_ingeniero);
	const tasaFirma = $derived(m.tasa_firma ?? 0);
	const kmSemana = $derived(k.total_semana ?? 0);

	function estatusColor(est: string): string {
		const e = String(est || '').toUpperCase();
		if (e === 'FIRMADO') return '#22C55E';
		if (e === 'EN CURSO') return '#F59E0B';
		if (e === 'BORRADOR') return '#64748B';
		if (e === 'CANCELADO') return '#EF4444';
		return '#3B82F6';
	}
</script>

<div class="screen actividad">
	<div class="screen-titulo"><span class="ic">📊</span> Actividad</div>

	<!-- KPIs superiores -->
	<div class="kpis">
		<div class="kpi">
			<span class="kpi-val">{num(r.total)}</span>
			<span class="kpi-lab">Reportes</span>
		</div>
		<div class="kpi">
			<span class="kpi-val">{num(t.total_semana)}</span>
			<span class="kpi-lab">Tickets</span>
		</div>
		<div class="kpi">
			<span class="kpi-val">{num(fotos.length)}</span>
			<span class="kpi-lab">Fotos</span>
		</div>
		<div class="kpi">
			<span class="kpi-val">{num(kmSemana)}</span>
			<span class="kpi-lab">Km semana</span>
		</div>
		<div class="kpi">
			<span class="kpi-val">{pct(tasaFirma)}</span>
			<span class="kpi-lab">Tasa firma</span>
		</div>
	</div>

	<!-- Contenido principal en grid -->
	<div class="grid-principal">
		<!-- Reportes -->
		<div class="seccion">
			<div class="seccion-titulo">🔧 Reportes recientes</div>
			{#if reportes.length}
				<div class="lista-compacta">
					{#each reportes.slice(0, 4) as rp}
						<div class="item">
							<span class="item-folio" style="color: {estatusColor(rp.Estatus)}">{rp.Folio}</span>
							<span class="item-desc">{recortar(rp.Cliente, 20)}</span>
							<span class="item-meta">{rp.ingeniero} · {rp.fecha}</span>
						</div>
					{/each}
				</div>
			{:else}
				<div class="vacio-mini">Sin reportes</div>
			{/if}
		</div>

		<!-- Tickets -->
		<div class="seccion">
			<div class="seccion-titulo">🎫 Tickets OxxoGas</div>
			{#if tickets.length}
				<div class="lista-compacta">
					{#each tickets.slice(0, 4) as tk}
						<div class="item">
							<span class="item-folio ticket">{tk.folio}</span>
							<span class="item-desc">{recortar(tk.cliente, 18)}</span>
							<span class="item-meta">{tk.vehiculo} · {tk.usuario}</span>
						</div>
					{/each}
				</div>
			{:else}
				<div class="vacio-mini">Sin tickets</div>
			{/if}
		</div>

		<!-- Métricas -->
		<div class="seccion">
			<div class="seccion-titulo">📈 Métricas</div>
			<div class="metricas-list">
				{#if topCliente}
					<div class="metrica">
						<span class="metrica-label">Top cliente</span>
						<span class="metrica-val">{recortar(topCliente.Cliente, 18)}</span>
						<span class="metrica-sub">{num(topCliente.total)} reportes</span>
					</div>
				{/if}
				{#if topIng}
					<div class="metrica">
						<span class="metrica-label">Top ingeniero</span>
						<span class="metrica-val">{recortar(topIng.nombre, 18)}</span>
						<span class="metrica-sub">{num(topIng.reportes)} reportes · {num(topIng.horas_totales)}h</span>
					</div>
				{/if}
				<div class="metrica">
					<span class="metrica-label">Reportes hoy</span>
					<span class="metrica-val">{num(r.hoy)}</span>
				</div>
				<div class="metrica">
					<span class="metrica-label">Firmados esta semana</span>
					<span class="metrica-val">{num(r.firmados)}</span>
					<span class="metrica-sub">de {num(r.total)}</span>
				</div>
			</div>
		</div>

		<!-- Kilómetros -->
		<div class="seccion">
			<div class="seccion-titulo">🚗 Kilómetros</div>
			<div class="km-list">
				{#each (k.por_vehiculo ?? []).slice(0, 4) as v}
					<div class="km-item">
						<span class="km-vehiculo">{recortar(v.MarcaModelo || v.vehiculo, 16)}</span>
						<span class="km-val">{num(v.km_esta_semana ?? v.total_tickets ?? 0)} km</span>
					</div>
				{/each}
				{#if !(k.por_vehiculo ?? []).length}
					<div class="vacio-mini">Sin datos</div>
				{/if}
			</div>
		</div>
	</div>
</div>

<style>
	.screen { height: 100%; display: flex; flex-direction: column; gap: 0.5rem; }
	.screen-titulo { font-size: 1.5rem; font-weight: 800; color: var(--color-text); flex-shrink: 0; }

	.kpis {
		display: flex; gap: 0.75rem; flex-shrink: 0; flex-wrap: wrap;
	}
	.kpi {
		flex: 1; min-width: 80px; text-align: center;
		padding: 0.5rem 0.75rem; border-radius: 10px;
		background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08);
	}
	.kpi-val { display: block; font-size: 1.6rem; font-weight: 800; color: var(--color-primary-light); line-height: 1; }
	.kpi-lab { display: block; font-size: 0.7rem; color: var(--color-text-muted); margin-top: 2px; text-transform: uppercase; }

	.grid-principal {
		flex: 1; min-height: 0; display: grid;
		grid-template-columns: repeat(2, 1fr);
		grid-template-rows: repeat(2, 1fr);
		gap: 0.75rem; overflow: hidden;
	}
	.seccion {
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(255, 255, 255, 0.06);
		border-radius: 12px; padding: 0.75rem;
		overflow: hidden; display: flex; flex-direction: column;
	}
	.seccion-titulo { font-size: 0.9rem; font-weight: 700; color: var(--color-primary-light); margin-bottom: 0.5rem; flex-shrink: 0; }

	.lista-compacta { display: flex; flex-direction: column; gap: 0.35rem; overflow: hidden; }
	.item {
		display: flex; align-items: center; gap: 0.5rem;
		padding: 0.35rem 0.5rem; border-radius: 6px;
		background: rgba(255, 255, 255, 0.03);
		font-size: 0.8rem;
	}
	.item-folio { font-weight: 800; font-size: 0.85rem; min-width: 60px; }
	.item-folio.ticket { color: #F59E0B; }
	.item-desc { flex: 1; color: #e2e8f0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.item-meta { font-size: 0.7rem; color: var(--color-text-muted); white-space: nowrap; }

	.metricas-list { display: flex; flex-direction: column; gap: 0.4rem; }
	.metrica { display: flex; align-items: center; gap: 0.5rem; }
	.metrica-label { font-size: 0.75rem; color: var(--color-text-muted); min-width: 90px; }
	.metrica-val { font-size: 0.9rem; font-weight: 700; color: var(--color-text); }
	.metrica-sub { font-size: 0.7rem; color: var(--color-text-muted); }

	.km-list { display: flex; flex-direction: column; gap: 0.3rem; }
	.km-item { display: flex; justify-content: space-between; align-items: center; padding: 0.25rem 0; }
	.km-vehiculo { font-size: 0.8rem; color: #e2e8f0; }
	.km-val { font-size: 0.8rem; font-weight: 700; color: #4ade80; }

	.vacio-mini { color: var(--color-text-muted); font-size: 0.8rem; text-align: center; padding: 1rem; }
</style>
