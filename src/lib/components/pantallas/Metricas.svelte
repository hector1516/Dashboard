<!--
	📈 Resumen de la semana.

	Lo nuevo: el HEATMAP hora×día (de 0 a 23h, domingo a sábado). Responde la
	pregunta que el resto de las pantallas no responde — ¿a qué hora trabaja
	esta oficina? — y de paso se ve de un vistazo si hubo un día raro.
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
		if (t <= 0) return 'rgba(255,255,255,0.045)';
		if (t < 0.25) return `rgba(59,130,246,${0.18 + t})`;
		if (t < 0.5) return `rgba(245,158,11,${0.2 + t * 0.8})`;
		return `rgba(255,107,0,${0.3 + t * 0.7})`;
	}
	function celda(dia: number, hora: number): number {
		return pulso.find((p) => p.dia === dia && p.hora === hora)?.valor ?? 0;
	}
</script>

<div class="screen">
	<div class="screen-titulo"><span class="ic">📈</span> Resumen de la Semana en ECCSA</div>

	<div class="kpis" style="grid-template-columns:repeat(5,1fr)">
		<div class="kpi blue" style="animation-delay:0s">
			<span class="kpi-ic">📊</span><span class="kpi-val">{num(datos.reportes.esta_semana)}</span>
			<span class="kpi-lab">Reportes esta semana</span>
		</div>
		<div class="kpi green" style="animation-delay:0.08s">
			<span class="kpi-ic">✍️</span><span class="kpi-val">{num(datos.reportes.firmados)}</span>
			<span class="kpi-lab">Firmados</span><span class="kpi-sub">{num(datos.reportes.pendientes)} pendientes</span>
		</div>
		<div class="kpi orange" style="animation-delay:0.16s">
			<span class="kpi-ic">⛽</span><span class="kpi-val">{num(datos.kilometros.total_semana)}</span>
			<span class="kpi-lab">Km esta semana</span><span class="kpi-sub">{num(datos.kilometros.hoy)} km hoy</span>
		</div>
		<div class="kpi purple" style="animation-delay:0.24s">
			<span class="kpi-ic">🎫</span><span class="kpi-val">{num(datos.tickets.total_semana)}</span>
			<span class="kpi-lab">Tickets esta semana</span>
		</div>
		<div class="kpi gold" style="animation-delay:0.32s">
			<span class="kpi-ic">⚡</span><span class="kpi-val">{num(m.actividad_hora)}</span>
			<span class="kpi-lab">Movimiento última hora</span>
		</div>
	</div>

	<div class="cuerpo">
		<!-- Heatmap -->
		<div class="card heat">
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
			<!-- Eje de horas ABAJO: en vertical (que es como estaba) se leía como
			     una lista suelta al lado de los días y no como un eje. -->
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

		<!-- Tops -->
		<div class="col-tops">
			{#if !m.top_cliente && !m.top_ingeniero && !m.ultimo_evento && !m.top_del_dia}
				<div class="card top sin-datos">
					<span class="top-ic">🌙</span>
					<div>
						<div class="top-lab">Sin actividad en la semana</div>
						<div class="top-val txt">Todavía no hay registros</div>
						<div class="top-cnt">La pantalla se llena sola en cuanto empiece el turno</div>
					</div>
				</div>
			{/if}
			{#if m.top_cliente}
				<div class="card top" style="animation-delay:0.4s">
					<span class="top-ic">🏭</span>
					<div>
						<div class="top-lab">Cliente con más reportes — semana</div>
						<div class="top-val">{m.top_cliente.Cliente}</div>
						<div class="top-cnt">{m.top_cliente.total} reportes</div>
					</div>
				</div>
			{/if}
			{#if m.top_ingeniero}
				<div class="card top" style="animation-delay:0.5s">
					<span class="top-ic">👷</span>
					<div>
						<div class="top-lab">Ingeniero con más horas — semana</div>
						<div class="top-val">{m.top_ingeniero.nombre}</div>
						<div class="top-cnt">{m.top_ingeniero.horas_totales} horas · {m.top_ingeniero.reportes} reportes</div>
					</div>
				</div>
			{/if}
			{#if m.ultimo_evento}
				<div class="card top" style="animation-delay:0.6s">
					<span class="top-ic">🕒</span>
					<div>
						<div class="top-lab">Último movimiento</div>
						<div class="top-val txt">{m.ultimo_evento.texto}</div>
						<div class="top-cnt">{m.ultimo_evento.meta}</div>
					</div>
				</div>
			{/if}
			{#if m.top_del_dia}
				<div class="card top" style="animation-delay:0.7s">
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
	.cuerpo { flex: 1; min-height: 0; display: grid; grid-template-columns: 1.45fr 1fr; gap: 16px; }
	.seccion-lab { font-size: 14px; font-weight: 800; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.05em; }

	.heat { padding: 14px 18px; display: flex; flex-direction: column; gap: 10px; min-height: 0; }
	.rejilla-heat { display: flex; flex: 1; min-height: 0; }
	.heat-celdas { flex: 1; display: flex; flex-direction: column; gap: 5px; }
	.eje-hora {
		display: grid; grid-template-columns: 40px repeat(24, 1fr); gap: 3px;
		font-size: 11px; color: #64748B; flex-shrink: 0;
	}
	.eje-hora span { grid-row: 1; }
	.eje-hora .hueco { display: none; }
	/* Cada etiqueta se alinea al inicio de su columna (hora 0, 4, 8...). */
	.eje-hora span:not(.hueco) { justify-self: start; }
	.fila-heat { display: grid; grid-template-columns: 40px repeat(24, 1fr); gap: 3px; align-items: center; flex: 1; }
	.dia { font-size: 12px; color: #64748B; font-weight: 700; }
	.celda { display: block; width: 100%; height: 100%; min-height: 14px; border-radius: 3px; transition: background 0.3s; }
	.leyenda { display: flex; align-items: center; gap: 5px; font-size: 11px; color: #64748B; }
	.leyenda .celda { width: 18px; height: 12px; }

	.col-tops { display: flex; flex-direction: column; gap: 10px; }
	.col-tops .top { flex: 1 1 auto; }
	.sin-datos { border-color: rgba(255,255,255,0.1); }
	.top { display: flex; align-items: center; gap: 16px; padding: 14px 18px; animation: entrarStagger 0.5s cubic-bezier(0.16, 1, 0.3, 1) both; }
	.top-ic { font-size: 34px; }
	.top-lab { font-size: 14px; color: var(--color-text-muted); font-weight: 600; }
	.top-val { font-size: 26px; font-weight: 900; color: var(--color-primary-light); line-height: 1.15; }
	.top-val.txt { font-size: 19px; }
	.top-cnt { font-size: 14px; color: #CBD5E1; }
</style>
