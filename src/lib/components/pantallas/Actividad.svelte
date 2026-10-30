<!-- Actividad.svelte - Pantalla unificada rediseñada: Reportes + Tickets + Métricas + Km -->
<script lang="ts">
	import { recortar, num, money, pct } from '$lib/kiosk/format';
	import type { Snapshot, Reporte, Ticket } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const r = $derived(datos.reportes);
	const t = $derived(datos.tickets);
	const m = $derived(datos.metricas);
	const k = $derived(datos.kilometros);

	const reportes = $derived(r.ultimos ?? []);
	const tickets = $derived(t.ultimos ?? []);
	const topCliente = $derived(m.top_cliente);
	const topIng = $derived(m.top_ingeniero);
	const tasaFirma = $derived(m.tasa_firma ?? 0);
	const kmSemana = $derived(k.total_semana ?? 0);
	const vehiculos = $derived(k.por_vehiculo ?? []);
	const maxKm = $derived(Math.max(1, ...vehiculos.map((x: any) => x.km_esta_semana ?? x.total_tickets ?? 0)));

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

	<!-- KPIs superiores - barra horizontal -->
	<div class="kpis-bar">
		<div class="kpi">
			<span class="kpi-val">{num(r.total)}</span>
			<span class="kpi-lab">Reportes</span>
		</div>
		<div class="kpi">
			<span class="kpi-val">{num(t.total_semana)}</span>
			<span class="kpi-lab">Tickets</span>
		</div>
		<div class="kpi">
			<span class="kpi-val">{num(kmSemana)}</span>
			<span class="kpi-lab">Km semana</span>
		</div>
		<div class="kpi">
			<span class="kpi-val">{pct(tasaFirma)}</span>
			<span class="kpi-lab">Tasa firma</span>
		</div>
		<div class="kpi">
			<span class="kpi-val">{num(r.firmados)}</span>
			<span class="kpi-lab">Firmados</span>
		</div>
		<div class="kpi">
			<span class="kpi-val">{num(r.pendientes)}</span>
			<span class="kpi-lab">Pendientes</span>
		</div>
	</div>

	<!-- Contenido principal: 2 columnas grandes -->
	<div class="contenido">
		<!-- Columna izquierda: Reportes + Tickets -->
		<div class="col-izq">
			<!-- Reportes -->
			<div class="bloque">
				<div class="bloque-titulo">🔧 Reportes recientes</div>
				{#if reportes.length}
					<div class="lista">
						{#each reportes.slice(0, 5) as rp, i}
							<div class="fila" style="animation-delay: {i * 0.05}s">
								<span class="folio" style="color: {estatusColor(rp.Estatus)}">{rp.Folio}</span>
								<span class="desc">{recortar(rp.Cliente, 24)}</span>
								<span class="meta">{rp.ingeniero}</span>
								<span class="fecha">{rp.fecha}</span>
							</div>
						{/each}
					</div>
				{:else}
					<div class="vacio">Sin reportes</div>
				{/if}
			</div>

			<!-- Tickets -->
			<div class="bloque">
				<div class="bloque-titulo">🎫 Tickets OxxoGas</div>
				{#if tickets.length}
					<div class="lista">
						{#each tickets.slice(0, 5) as tk, i}
							<div class="fila" style="animation-delay: {i * 0.05}s">
								<span class="folio ticket">{tk.folio}</span>
								<span class="desc">{recortar(tk.cliente, 20)}</span>
								<span class="meta">{tk.vehiculo} · {tk.usuario}</span>
								<span class="fecha">{tk.fecha?.replace('T', ' ')}</span>
							</div>
						{/each}
					</div>
				{:else}
					<div class="vacio">Sin tickets</div>
				{/if}
			</div>
		</div>

		<!-- Columna derecha: Métricas + Km -->
		<div class="col-der">
			<!-- Métricas -->
			<div class="bloque">
				<div class="bloque-titulo">📈 Métricas</div>
				<div class="metricas">
					{#if topCliente}
						<div class="metrica-row">
							<span class="m-label">Top cliente</span>
							<span class="m-val">{recortar(topCliente.Cliente, 20)}</span>
							<span class="m-sub">{num(topCliente.total)} reportes</span>
						</div>
					{/if}
					{#if topIng}
						<div class="metrica-row">
							<span class="m-label">Top ingeniero</span>
							<span class="m-val">{recortar(topIng.nombre, 20)}</span>
							<span class="m-sub">{num(topIng.reportes)} reportes · {num(topIng.horas_totales)}h</span>
						</div>
					{/if}
					<div class="metrica-row">
						<span class="m-label">Reportes hoy</span>
						<span class="m-val">{num(r.hoy)}</span>
					</div>
					<div class="metrica-row">
						<span class="m-label">Esta semana</span>
						<span class="m-val">{num(r.esta_semana)}</span>
					</div>
				</div>
			</div>

			<!-- Kilómetros -->
			<div class="bloque">
				<div class="bloque-titulo">🚗 Kilómetros</div>
				<div class="km-list">
					{#each vehiculos.slice(0, 5) as v, i}
						<div class="km-row">
							<span class="km-vehiculo">{recortar(v.MarcaModelo || v.vehiculo, 18)}</span>
							<div class="km-barra">
								<div class="km-relleno" style="width: {Math.max(4, Math.round((v.km_esta_semana || v.total_tickets || 0) / maxKm * 100))}%"></div>
							</div>
							<span class="km-val">{num(v.km_esta_semana ?? v.total_tickets ?? 0)}</span>
						</div>
					{/each}
					{#if !vehiculos.length}
						<div class="vacio">Sin datos de km</div>
					{/if}
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.screen { height: 100%; display: flex; flex-direction: column; gap: 0.75rem; }
	.screen-titulo { font-size: 1.8rem; font-weight: 800; color: var(--color-text); flex-shrink: 0; }

	.kpis-bar {
		display: flex; gap: 0.75rem; flex-shrink: 0; flex-wrap: wrap;
	}
	.kpi {
		flex: 1; min-width: 90px; text-align: center;
		padding: 0.6rem 0.75rem; border-radius: 10px;
		background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08);
	}
	.kpi-val { display: block; font-size: 1.8rem; font-weight: 800; color: var(--color-primary-light); line-height: 1; }
	.kpi-lab { display: block; font-size: 0.75rem; color: var(--color-text-muted); margin-top: 3px; text-transform: uppercase; letter-spacing: 0.05em; }

	.contenido {
		flex: 1; min-height: 0; display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.75rem; overflow: hidden;
	}
	.col-izq, .col-der { display: flex; flex-direction: column; gap: 0.75rem; min-height: 0; }

	.bloque {
		flex: 1; min-height: 0;
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(255, 255, 255, 0.06);
		border-radius: 12px; padding: 0.75rem;
		overflow: hidden; display: flex; flex-direction: column;
	}
	.bloque-titulo { font-size: 1rem; font-weight: 700; color: var(--color-primary-light); margin-bottom: 0.5rem; flex-shrink: 0; }

	.lista { display: flex; flex-direction: column; gap: 0.35rem; overflow: hidden; }
	.fila {
		display: flex; align-items: center; gap: 0.75rem;
		padding: 0.4rem 0.6rem; border-radius: 6px;
		background: rgba(255, 255, 255, 0.03);
		animation: entrarStagger 0.4s ease both;
	}
	.folio { font-weight: 800; font-size: 0.95rem; min-width: 70px; }
	.folio.ticket { color: #F59E0B; }
	.desc { flex: 1; font-size: 0.85rem; color: #e2e8f0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.meta { font-size: 0.75rem; color: var(--color-text-muted); white-space: nowrap; }
	.fecha { font-size: 0.7rem; color: #64748b; white-space: nowrap; }

	.metricas { display: flex; flex-direction: column; gap: 0.4rem; }
	.metrica-row { display: flex; align-items: center; gap: 0.5rem; padding: 0.3rem 0; }
	.m-label { font-size: 0.8rem; color: var(--color-text-muted); min-width: 100px; }
	.m-val { font-size: 0.95rem; font-weight: 700; color: var(--color-text); }
	.m-sub { font-size: 0.7rem; color: var(--color-text-muted); margin-left: auto; }

	.km-list { display: flex; flex-direction: column; gap: 0.35rem; }
	.km-row { display: flex; align-items: center; gap: 0.5rem; }
	.km-vehiculo { font-size: 0.8rem; color: #e2e8f0; min-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.km-barra { flex: 1; height: 6px; background: rgba(255,255,255,0.08); border-radius: 3px; overflow: hidden; }
	.km-relleno { height: 100%; background: #4ade80; border-radius: 3px; transition: width 0.5s; }
	.km-val { font-size: 0.8rem; font-weight: 700; color: #4ade80; min-width: 60px; text-align: right; }

	.vacio { color: var(--color-text-muted); font-size: 0.85rem; text-align: center; padding: 1.5rem; }

	@keyframes entrarStagger {
		from { opacity: 0; transform: translateY(8px); }
		to { opacity: 1; transform: none; }
	}
</style>
