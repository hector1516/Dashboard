<!-- 📊 Últimos reportes de servicio: quién trabaja dónde, y qué falta firmar. -->
<script lang="ts">
	import { num, haceCuanto } from '$lib/kiosk/format';
	import type { Snapshot } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const r = $derived(datos.reportes);
	const lista = $derived(r.ultimos ?? []);
	const firmadosPct = $derived(r.total > 0 ? (r.firmados / r.total) * 100 : 0);

	// Arco de la dona firmado/pendiente (SVG, 2 arcos de 180px de diámetro).
	const C = 2 * Math.PI * 70;
	const arcoOk = $derived((firmadosPct / 100) * C);
</script>

<div class="screen">
	<div class="screen-titulo"><span class="ic">📊</span> Últimos Reportes de Servicio</div>

	<div class="cuerpo">
		<div class="col-izq stagger">
			{#each lista as rep, i}
				<div class="reporte" class:firmado={rep.Estatus === 'Firmado'} style="animation-delay:{i * 0.07}s">
					<div class="estado" class:firmado={rep.Estatus === 'Firmado'}>{rep.Estatus === 'Firmado' ? '✍️' : '📝'}</div>
					<div class="rep-cuerpo">
						<div class="folio">{rep.Folio}</div>
						<div class="cliente">{rep.Cliente || '—'}</div>
						<div class="meta">{rep.ingeniero} · {rep.fecha}</div>
					</div>
					<div class="pill" class:ok={rep.Estatus === 'Firmado'} class:warn={rep.Estatus !== 'Firmado'}>
						{rep.Estatus}
					</div>
				</div>
			{/each}
			{#if !lista.length}
				<div class="vacio">Sin reportes registrados</div>
			{/if}
		</div>

		<div class="col-der">
			<div class="card dona">
				<svg viewBox="0 0 160 160" class="dona" aria-hidden="true">
					<circle cx="80" cy="80" r="70" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="16" />
					<circle
						cx="80" cy="80" r="70" fill="none" stroke="#22C55E" stroke-width="16" stroke-linecap="round"
						stroke-dasharray="{arcoOk} {C - arcoOk}" transform="rotate(-90 80 80)"
					/>
					<text x="80" y="76" class="dona-val">{Math.round(firmadosPct)}%</text>
					<text x="80" y="98" class="dona-lab">firmados</text>
				</svg>
			</div>

			<div class="kpis" style="grid-template-columns:repeat(2,1fr)">
				<div class="kpi blue">
					<span class="kpi-val">{num(r.esta_semana)}</span>
					<span class="kpi-lab">reportes · semana</span>
				</div>
				<div class="kpi green">
					<span class="kpi-val">{num(r.firmados)}</span>
					<span class="kpi-lab">firmados</span>
					<span class="kpi-sub">{num(r.pendientes)} pendientes</span>
				</div>
				<div class="kpi orange">
					<span class="kpi-val">{num(r.hoy)}</span>
					<span class="kpi-lab">hoy</span>
				</div>
				<div class="kpi gold">
					<span class="kpi-val">{num(r.total)}</span>
					<span class="kpi-lab">histórico</span>
				</div>
			</div>

			{#if r.por_ingeniero.length}
				<div class="seccion-lab">Reportes por ingeniero</div>
				<div class="barras">
					{#each r.por_ingeniero.slice(0, 6) as g, i}
						{@const max = Math.max(1, ...r.por_ingeniero.map((x) => x.total))}
						<div class="bar-fila" style="animation-delay:{i * 0.06}s">
							<span class="bar-lab">{g.nombre}</span>
							<div class="bar-pista">
								<div class="bar-relleno" style="width:{Math.max(Math.round((g.total / max) * 100), 3)}%"></div>
							</div>
							<span class="bar-val">{g.total}</span>
							<span class="bar-pct">{Math.round((g.firmados / Math.max(1, g.total)) * 100)}% firm.</span>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	.cuerpo { flex: 1; min-height: 0; display: grid; grid-template-columns: 1.25fr 0.9fr; gap: 18px; }
	.col-izq { display: flex; flex-direction: column; gap: 10px; min-height: 0; overflow: hidden; }
	.col-der { display: flex; flex-direction: column; gap: 12px; min-height: 0; }
	.seccion-lab { font-size: 14px; font-weight: 800; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.05em; }

	.reporte {
		display: flex; align-items: center; gap: 16px; padding: 14px 18px; border-radius: 14px;
		background: rgba(255,255,255,0.045); border: 1px solid rgba(255,255,255,0.07);
		position: relative; overflow: hidden; flex-shrink: 0;
	}
	/* Brillo que recorre la tarjeta al entrar: da movimiento sin gastar nada. */
	.reporte::after {
		content: ''; position: absolute; inset: 0;
		background: linear-gradient(105deg, transparent 30%, rgba(255,255,255,0.09) 48%, transparent 62%);
		transform: translateX(-100%); animation: brillar 1.1s ease both;
		animation-delay: inherit;
	}
	.reporte.firmado { border-color: rgba(34,197,94,0.25); }
	.estado { font-size: 30px; }
	.rep-cuerpo { flex: 1; min-width: 0; }
	.folio { font-weight: 800; color: var(--color-primary-light); font-size: 19px; }
	.cliente { font-weight: 700; color: var(--color-text); font-size: 20px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.meta { font-size: 15px; color: var(--color-text-muted); margin-top: 2px; }

	.dona { padding: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
	.dona { width: 100%; max-width: 190px; }
	.dona-val { fill: #fff; font-size: 30px; font-weight: 900; text-anchor: middle; }
	.dona-lab { fill: #94A3B8; font-size: 13px; font-weight: 600; text-anchor: middle; }

	.barras { display: flex; flex-direction: column; gap: 7px; overflow: hidden; }
	.barras .bar-fila { grid-template-columns: 150px 1fr 40px 76px; }

	@keyframes brillar { from { transform: translateX(-100%); } to { transform: translateX(100%); } }
</style>
