<!--
	📈 Resumen de la semana — versión glassmorphism.

	Estilo: tarjetas translúcidas con `backdrop-filter: blur()`, bordes con
	degradado, sombras suaves y animaciones de entrada escalonadas. Tema
	blanco-azul con acentos naranja ECCSA. Sin dinero: solo métricas medibles.
-->
<script lang="ts">
	import { num, haceCuanto } from '$lib/kiosk/format';
	import type { Snapshot } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const m = $derived(datos.metricas);
	const pulso = $derived(m.pulso ?? []);
	const maxPulso = $derived(Math.max(1, ...pulso.map((p) => p.valor)));
	const dias = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
	/** Colores por intensidad: de transparente a naranja ECCSA. */
	function colorCelda(v: number): string {
		const t = v / maxPulso;
		if (t <= 0) return 'rgba(255,255,255,0.06)';
		if (t < 0.25) return `rgba(59,130,246,${0.16 + t * 0.6})`;
		if (t < 0.5) return `rgba(245,158,11,${0.18 + t * 0.7})`;
		return `rgba(255,107,0,${0.22 + t * 0.75})`;
	}
	function celda(dia: number, hora: number): number {
		return pulso.find((p) => p.dia === dia && p.hora === hora)?.valor ?? 0;
	}
</script>

<div class="screen g-screen">
	<div class="screen-titulo g-titulo"><span class="ic">📈</span> Resumen de la Semana en ECCSA</div>

	<!-- KPIs con estilo glass -->
	<div class="kpis g-kpis">
		<div class="kpi g-kpi blue" style="animation-delay:0s">
			<span class="kpi-ic">📊</span><span class="kpi-val">{num(datos.reportes.esta_semana)}</span>
			<span class="kpi-lab">Reportes esta semana</span>
		</div>
		<div class="kpi g-kpi green" style="animation-delay:0.08s">
			<span class="kpi-ic">✍️</span><span class="kpi-val">{num(datos.reportes.firmados)}</span>
			<span class="kpi-lab">Firmados</span><span class="kpi-sub">{num(datos.reportes.pendientes)} pendientes · {m.tasa_firma}% firma</span>
		</div>
		<div class="kpi g-kpi orange" style="animation-delay:0.16s">
			<span class="kpi-ic">⛽</span><span class="kpi-val">{num(datos.kilometros.total_semana)}</span>
			<span class="kpi-lab">Km esta semana</span><span class="kpi-sub">{num(datos.kilometros.hoy)} km hoy</span>
		</div>
		<div class="kpi g-kpi purple" style="animation-delay:0.24s">
			<span class="kpi-ic">🎫</span><span class="kpi-val">{num(datos.tickets.total_semana)}</span>
			<span class="kpi-lab">Tickets esta semana</span>
		</div>
		<div class="kpi g-kpi gold" style="animation-delay:0.32s">
			<span class="kpi-ic">⚡</span><span class="kpi-val">{num(m.actividad_hora)}</span>
			<span class="kpi-lab">Movimiento última hora</span>
		</div>
	</div>

	<div class="cuerpo g-cuerpo">
		<!-- Heatmap -->
		<div class="card g-card heat">
			<div class="seccion-lab">Pulso de la semana · eventos por hora</div>
			<div class="rejilla-heat">
				<div class="heat-celdas">
					{#each dias as _d, dia}
						<div class="fila-heat">
							<span class="dia">{_d}</span>
							{#each Array(24) as _, hora}
								{@const v = celda(dia, hora)}
								<span
									class="celda"
									style="background:{colorCelda(v)}"
									title="{_d} {String(hora).padStart(2, '0')}:00 — {v} eventos"
								></span>
							{/each}
						</div>
					{/each}
				</div>
			</div>
			<div class="eje-hora">
				<span class="hueco"></span>
				{#each [0, 4, 8, 12, 16, 20, 23] as h}
					<span>{String(h).padStart(2, '0')}h</span>
				{/each}
			</div>
			<div class="leyenda">
				<span>menos</span>
				{#each [0.1, 0.35, 0.6, 0.85, 1] as t}
					<span class="celda" style="background:{colorCelda(t * maxPulso)}"></span>
				{/each}
				<span>más</span>
			</div>
		</div>

		<!-- Reportes por día de la semana -->
		<div class="card g-card top" style="animation-delay:0.35s;flex-direction:column;align-items:stretch;gap:8px">
			<div class="top-lab" style="text-align:center">Reportes por día — semana</div>
			<div class="barras-dia">
				{#each m.reportes_por_dia as v, i}
					{@const h = Math.max(4, Math.round((v / Math.max(1, ...m.reportes_por_dia)) * 60))}
					<div class="barra-col">
						<div class="barra" style="height:{h}px" title="{dias[i]}: {v} reportes"></div>
						<span class="barra-lab">{dias[i]}</span>
						<span class="barra-val">{v}</span>
					</div>
				{/each}
			</div>
		</div>
		<div class="col-tops g-col-tops">
			{#if !m.top_cliente && !m.top_ingeniero && !m.ultimo_evento && !m.top_del_dia}
				<div class="card g-card top sin-datos">
					<span class="top-ic">🌙</span>
					<div>
						<div class="top-lab">Sin actividad en la semana</div>
						<div class="top-val txt">Todavía no hay registros</div>
						<div class="top-cnt">La pantalla se llena sola en cuanto empiece el turno</div>
					</div>
				</div>
			{/if}
			{#if m.top_cliente}
				<div class="card g-card top" style="animation-delay:0.4s">
					<span class="top-ic">🏭</span>
					<div>
						<div class="top-lab">Cliente con más reportes — semana</div>
						<div class="top-val">{m.top_cliente.Cliente}</div>
						<div class="top-cnt">{m.top_cliente.total} reportes</div>
					</div>
				</div>
			{/if}
			{#if m.top_ingeniero}
				<div class="card g-card top" style="animation-delay:0.5s">
					<span class="top-ic">👷</span>
					<div>
						<div class="top-lab">Ingeniero con más horas — semana</div>
						<div class="top-val">{m.top_ingeniero.nombre}</div>
						<div class="top-cnt">{m.top_ingeniero.horas_totales} horas · {m.top_ingeniero.reportes} reportes</div>
					</div>
				</div>
			{/if}
			{#if m.ultimo_evento}
				<div class="card g-card top" style="animation-delay:0.6s">
					<span class="top-ic">🕒</span>
					<div>
						<div class="top-lab">Último movimiento</div>
						<div class="top-val txt">{m.ultimo_evento.texto}</div>
						<div class="top-cnt">{m.ultimo_evento.meta}</div>
					</div>
				</div>
			{/if}
			{#if m.top_del_dia}
				<div class="card g-card top" style="animation-delay:0.7s">
					<span class="top-ic">🔥</span>
					<div>
						<div class="top-lab">Más activo hoy</div>
						<div class="top-val txt">{m.top_del_dia.nombre}</div>
						<div class="top-cnt">{m.top_del_dia.valor} {m.top_del_dia.unidad}</div>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	/* ═════════════════════════════════════════════════════════════════════════
	   Glassmorphism base (sólo esta pantalla; el shell sigue intacto)
	   ═════════════════════════════════════════════════════════════════════════ */
	.g-screen { position: relative; z-index: 1; }
	.g-titulo { font-size: 20px; font-weight: 800; letter-spacing: 0.04em; margin-bottom: 16px; }
	.g-titulo .ic { margin-right: 8px; }

	/* KPIs */
	.g-kpis { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 20px; }
	.g-kpi {
		position: relative;
		overflow: hidden;
		background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));
		border: 1px solid rgba(255,255,255,0.08);
		-webkit-backdrop-filter: blur(14px) saturate(1.1);
		backdrop-filter: blur(14px) saturate(1.1);
		border-radius: 16px;
		padding: 12px 14px;
		display: flex; align-items: center; gap: 10px;
		animation: g-entrar 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
		transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
	}
	.g-kpi:hover { transform: translateY(-2px); border-color: rgba(255,255,255,0.25); }
	/* Brillo lateral por color */
	.g-kpi::before {
		content: ''; position: absolute; inset: 0; border-radius: 16px;
		padding: 1px; background: linear-gradient(135deg, rgba(255,255,255,0.15), transparent);
		-webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
		-webkit-mask-composite: destination-out; mask-composite: exclude;
		pointer-events: none;
	}
	.g-kpi.blue::after {
		content: ''; position: absolute; top: -40%; left: -40%; width: 60px; height: 140px;
		background: radial-gradient(circle, rgba(59,130,246,0.12), transparent 70%);
		pointer-events: none;
	}
	.g-kpi.green::after {
		content: ''; position: absolute; top: -40%; left: -40%; width: 60px; height: 140px;
		background: radial-gradient(circle, rgba(34,197,94,0.12), transparent 70%);
		pointer-events: none;
	}
	.g-kpi.orange::after {
		content: ''; position: absolute; top: -40%; left: -40%; width: 60px; height: 140px;
		background: radial-gradient(circle, rgba(255,107,0,0.12), transparent 70%);
		pointer-events: none;
	}
	.g-kpi.purple::after {
		content: ''; position: absolute; top: -40%; left: -40%; width: 60px; height: 140px;
		background: radial-gradient(circle, rgba(168,85,247,0.12), transparent 70%);
		pointer-events: none;
	}
	.g-kpi.gold::after {
		content: ''; position: absolute; top: -40%; left: -40%; width: 60px; height: 140px;
		background: radial-gradient(circle, rgba(255,174,0,0.12), transparent 70%);
		pointer-events: none;
	}
	.kpi-ic { font-size: 22px; flex-shrink: 0; }
	.kpi-val { font-size: 26px; font-weight: 900; color: var(--color-primary-light); line-height: 1.1; }
	.kpi-lab { font-size: 13px; color: var(--color-text-muted); font-weight: 600; margin-top: 2px; }
	.kpi-sub { font-size: 11px; color: #CBD5E1; margin-top: 2px; }

	@keyframes g-entrar {
		from { opacity: 0; transform: translateY(14px); }
		to   { opacity: 1; transform: translateY(0); }
	}

	/* Cuerpo: dos columnas */
	.g-cuerpo { flex: 1; min-height: 0; display: grid; grid-template-columns: 1.45fr 1fr; gap: 16px; }

	/* Cards glass */
	.g-card {
		position: relative;
		background: rgba(30, 41, 59, 0.35);
		border: 1px solid rgba(255,255,255,0.06);
		-webkit-backdrop-filter: blur(16px) saturate(1.2);
		backdrop-filter: blur(16px) saturate(1.2);
		border-radius: 20px;
		box-shadow: 0 8px 32px rgba(0,0,0,0.35);
		overflow: hidden;
		animation: g-entrar 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
	}
	.g-card.heat { padding: 0; display: flex; flex-direction: column; min-height: 0; }
	.g-card.top { padding: 14px 16px; min-height: 0; }

	/* Brillo superior de las cards (efecto vidrio real) */
	.g-card::before {
		content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1.5px;
		background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
		pointer-events: none;
	}

	.seccion-lab { font-size: 13px; font-weight: 800; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.06em; padding: 14px 18px 8px; margin: 0; }

	/* Heatmap */
	.rejilla-heat { display: flex; flex: 1; min-height: 0; padding: 0 18px 14px; }
	.heat-celdas { flex: 1; display: flex; flex-direction: column; gap: 4px; }
	.eje-hora {
		display: grid; grid-template-columns: 40px repeat(24, 1fr); gap: 3px;
		font-size: 11px; color: #64748B; flex-shrink: 0; padding: 0 18px 10px;
	}
	.eje-hora span { grid-row: 1; }
	.eje-hora .hueco { display: none; }
	.eje-hora span:not(.hueco) { justify-self: start; }
	.fila-heat { display: grid; grid-template-columns: 40px repeat(24, 1fr); gap: 4px; align-items: center; flex: 1; }
	.dia { font-size: 12px; color: #64748B; font-weight: 700; }
	.celda { display: block; width: 100%; height: 100%; min-height: 14px; border-radius: 3px; transition: background 0.3s, transform 0.1s; }
	.celda:hover { transform: scale(1.15); z-index: 2; box-shadow: 0 0 8px rgba(255,255,255,0.2); }
	.leyenda { display: flex; align-items: center; gap: 5px; font-size: 11px; color: #64748B; padding: 0 18px 14px; }
	.leyenda .celda { width: 18px; height: 12px; }

	/* Col de tops */
	.g-col-tops { display: flex; flex-direction: column; gap: 10px; }
	.sin-datos { border-color: rgba(255,255,255,0.08); }
	.top { display: flex; align-items: center; gap: 16px; padding: 12px 16px; animation: g-entrar 0.5s cubic-bezier(0.16, 1, 0.3, 1) both; }
	.top-ic { font-size: 30px; }
	.top-lab { font-size: 13px; color: var(--color-text-muted); font-weight: 600; }
	.top-val { font-size: 24px; font-weight: 900; color: var(--color-primary-light); line-height: 1.15; }
	.top-val.txt { font-size: 18px; }
	.top-cnt { font-size: 13px; color: #CBD5E1; }

	.barras-dia { display: flex; align-items: flex-end; justify-content: space-between; gap: 6px; height: 70px; padding: 0 4px; }
	.barra-col { display: flex; flex-direction: column; align-items: center; gap: 2px; flex: 1; }
	.barra { width: 100%; min-width: 8px; background: linear-gradient(180deg, #FF6B00, #FFAE00); border-radius: 3px 3px 0 0; transition: height 0.3s; }
	.barra-lab { font-size: 10px; color: #64748B; font-weight: 700; }
	.barra-val { font-size: 11px; color: #CBD5E1; font-weight: 600; }
</style>
