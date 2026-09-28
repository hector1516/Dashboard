<!--
	⛽ Combustible — consumo de la semana por vehículo.

	Lo que aporta frente al dashboard de Field:
	  · odómetro animado en los KPIs (el número cuenta, no aparece de golpe),
	  · sparkline de 7 días (¿es normal lo de hoy?),
	  · radar de flota con semáforo por "último registro" (no solo por si hay km
	    esta semana): un vehículo con km de hace 5 días no está en ruta aunque
	    esta semana tenga un registro.
-->
<script lang="ts">
	import { num, haceCuanto } from '$lib/kiosk/format';
	import type { Snapshot, VehiculoKm } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const km = $derived(datos.kilometros);
	const vehiculos = $derived(km.por_vehiculo);
	// La ventana MÓVIL de 7 días es la que se dibuja: la semana de ECCSA arranca
	// en domingo, así que con la semanal los domingos la pantalla quedaría vacía.
	const maxKm = $derived(Math.max(1, ...vehiculos.map((v) => Math.abs(v.consumo_7d || 0))));
	const maxTickets = $derived(Math.max(1, ...datos.tickets.por_vehiculo.map((t) => t.total_tickets || 0)));
	const totalConsumo = $derived(vehiculos.reduce((s, v) => s + Math.abs(v.consumo_7d || 0), 0));
	const enRuta = $derived(vehiculos.filter((v) => v.consumo_7d > 0).length);

	/** Semáforo de un vehículo según cuándo fue su último registro. */
	function estado(v: VehiculoKm): { cls: string; txt: string } {
		if (!v.ultimo_registro) return { cls: 'off', txt: 'sin registro' };
		const h = (Date.now() - Date.parse(v.ultimo_registro.replace(' ', 'T'))) / 3600000;
		if (h <= 24) return { cls: 'ruta', txt: haceCuanto(v.ultimo_registro) };
		if (h <= 72) return { cls: 'medio', txt: haceCuanto(v.ultimo_registro) };
		return { cls: 'off', txt: haceCuanto(v.ultimo_registro) };
	}

	// Serie de 7 días → puntos del sparkline (SVG viewBox fijo 320×70).
	const serie = $derived(km.serie_7dias ?? []);
	const puntos = $derived.by(() => {
		if (serie.length < 2) return '';
		const max = Math.max(1, ...serie.map((d) => d.km || 0));
		return serie
			.map((d, i) => {
				const x = (i / (serie.length - 1)) * 320;
				const y = 66 - ((d.km || 0) / max) * 60;
				return `${x.toFixed(1)},${y.toFixed(1)}`;
			})
			.join(' ');
	});
	const area = $derived(puntos ? `0,70 ${puntos} 320,70` : '');
</script>

<div class="screen">
	<div class="screen-titulo"><span class="ic">⛽</span> Consumo de Combustible — Últimos 7 días</div>

	{#if vehiculos.length}
		<div class="kpis" style="grid-template-columns:repeat(4,1fr)">
			<div class="kpi blue" style="animation-delay:0s">
				<span class="kpi-ic">🛣️</span>
				<span class="kpi-val">{num(km.total_semana)}</span>
				<span class="kpi-lab">km registrados · semana</span>
			</div>
			<div class="kpi green" style="animation-delay:0.08s">
				<span class="kpi-ic">🟢</span>
				<span class="kpi-val">{enRuta}/{vehiculos.length}</span>
				<span class="kpi-lab">vehículos con consumo</span>
			</div>
			<div class="kpi gold" style="animation-delay:0.16s">
				<span class="kpi-ic">Σ</span>
				<span class="kpi-val">{num(totalConsumo)}</span>
				<span class="kpi-lab">km recorridos · 7 días</span>
			</div>
			<div class="kpi orange" style="animation-delay:0.24s">
				<span class="kpi-ic">🎫</span>
				<span class="kpi-val">{num(datos.tickets.total_semana)}</span>
				<span class="kpi-lab">tickets OxxoGas · semana</span>
			</div>
		</div>

		<div class="cuerpo">
			<!-- Izquierda: estado de la flota + serie semanal -->
			<div class="col-izq">
				<div class="seccion-lab">Flota · último registro</div>
				<div class="flota">
					{#each vehiculos as v, i}
						{@const e = estado(v)}
						<div class="veh" class:con-km={v.consumo_7d > 0} style="animation-delay:{i * 0.05}s">
							<span class="luz {e.cls}" title={e.txt}></span>
							<div class="veh-cuerpo">
								<div class="veh-nombre">{v.MarcaModelo}</div>
								<div class="veh-meta">{v.Placas} · {e.txt}</div>
							</div>
							<div class="veh-km">
								{#if v.sin_referencia}
									<span class="sin-ref" title="No hay lectura anterior para comparar">1ª lectura</span>
								{:else if v.consumo_7d > 0}
									+{num(v.consumo_7d)}
								{:else}
									—
								{/if}
							</div>
						</div>
					{/each}
				</div>

				{#if serie.length > 1}
					<div class="spark-box card">
						<div class="seccion-lab">Kilómetros por día (7 días)</div>
						<svg class="spark" viewBox="0 0 320 78" preserveAspectRatio="none" aria-hidden="true">
							<defs>
								<linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
									<stop offset="0%" stop-color="#FFAE00" stop-opacity="0.55" />
									<stop offset="100%" stop-color="#FFAE00" stop-opacity="0" />
								</linearGradient>
							</defs>
							<polygon class="spark-area" points={area} />
							<polyline class="spark-line" points={puntos} />
							{#each serie as d, i}
								{@const max = Math.max(1, ...serie.map((x) => x.km || 0))}
								<circle
									class="spark-pt"
									cx={(i / (serie.length - 1)) * 320}
									cy={66 - ((d.km || 0) / max) * 60}
									r="3"
								/>
							{/each}
						</svg>
						<div class="spark-ejes">
							<span>{serie[0]?.fecha?.slice(5) ?? ''}</span>
							<span>{serie[serie.length - 1]?.fecha?.slice(5) ?? ''}</span>
						</div>
					</div>
				{/if}
			</div>

			<!-- Derecha: barras de km y de tickets -->
			<div class="col-der">
				<div class="seccion-lab">Kilómetros por vehículo (vs. el mayor de los últimos 7 días)</div>
				<div class="barras">
					{#each vehiculos.slice(0, 9) as v, i}
						{@const p = Math.round((Math.abs(v.consumo_7d || 0) / maxKm) * 100)}
						<div class="bar-fila" style="animation-delay:{i * 0.06}s">
							<span class="bar-lab">{v.MarcaModelo}</span>
							<div class="bar-pista">
								<div class="bar-relleno km" style="width:{Math.max(p, 2)}%"></div>
							</div>
							<span class="bar-val km">+{num(v.consumo_7d)}</span>
							<span class="bar-pct">{p}%</span>
						</div>
					{/each}
				</div>

				{#if datos.tickets.por_vehiculo.length}
					<div class="seccion-lab t-tickets">🎫 Tickets OxxoGas por vehículo (semana)</div>
					<div class="barras">
						{#each datos.tickets.por_vehiculo as t, i}
							{@const p = Math.round(((t.total_tickets || 0) / maxTickets) * 100)}
							<div class="bar-fila" style="animation-delay:{0.25 + i * 0.06}s">
								<span class="bar-lab">{t.vehiculo}</span>
								<div class="bar-pista">
									<div class="bar-relleno ticket" style="width:{Math.max(p, 4)}%"></div>
								</div>
								<span class="bar-val ticket">{t.total_tickets} tkt</span>
								<span class="bar-pct">{p}%</span>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>
	{:else}
		<div class="vacio">
			Sin consumo calculable esta semana
			<span class="vacio-sub">Se muestra cuando hay registro esta semana y el anterior</span>
		</div>
	{/if}
</div>

<style>
	.cuerpo { flex: 1; min-height: 0; display: grid; grid-template-columns: minmax(360px, 0.85fr) 1.35fr; gap: 18px; }
	.col-izq, .col-der { display: flex; flex-direction: column; gap: 10px; min-height: 0; }
	.seccion-lab { font-size: 14px; font-weight: 800; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.05em; flex-shrink: 0; }
	.seccion-lab.t-tickets { margin-top: 4px; color: #FBBF24; }

	/* La lista de flota NO crece (son pocas filas): el espacio que sobra lo toma
	   la sparkline, que de otro modo quedaba aplastada contra el piso. */
	.flota { display: flex; flex-direction: column; gap: 7px; overflow: hidden; flex: 0 1 auto; }
	.veh {
		display: flex; align-items: center; gap: 12px; padding: 9px 14px; border-radius: 11px;
		background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07);
		animation: entrarStagger 0.45s cubic-bezier(0.16, 1, 0.3, 1) both;
	}
	.veh.con-km { background: linear-gradient(90deg, rgba(34,197,94,0.13), rgba(34,197,94,0.03)); border-color: rgba(34,197,94,0.3); }
	.luz { width: 11px; height: 11px; border-radius: 50%; flex-shrink: 0; }
	.luz.ruta  { background: #22C55E; box-shadow: 0 0 10px rgba(34,197,94,0.7); animation: latir 2.4s ease-in-out infinite; }
	.luz.medio { background: #F59E0B; box-shadow: 0 0 8px rgba(245,158,11,0.5); }
	.luz.off   { background: #475569; }
	.veh-cuerpo { flex: 1; min-width: 0; }
	.veh-nombre { font-weight: 700; font-size: 16px; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.veh-meta { font-size: 13px; color: var(--color-text-muted); }
	.veh-km { font-size: 15px; font-weight: 800; color: #4ADE80; font-variant-numeric: tabular-nums; }
	.sin-ref { font-size: 12px; font-weight: 700; color: #FBBF24; }

	.barras { display: flex; flex-direction: column; gap: 8px; overflow: hidden; flex: 1; }
	.barras .bar-fila { grid-template-columns: 190px 1fr 110px 46px; }

	.spark-box { padding: 14px 18px 10px; flex: 1 1 auto; display: flex; flex-direction: column; justify-content: center; gap: 6px; min-height: 150px; }
	.spark { height: 100%; min-height: 110px; }
	.spark-ejes { display: flex; justify-content: space-between; font-size: 12px; color: #64748B; }

	@keyframes latir { 0%,100% { opacity: 1; } 50% { opacity: 0.55; } }
</style>
