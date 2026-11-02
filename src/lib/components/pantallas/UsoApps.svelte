<!-- UsoApps.svelte - Estadísticas de uso de las apps Admon y Field -->
<script lang="ts">
	let datos = $state<any>(null);
	let cargando = $state(true);

	async function cargar() {
		try {
			const r = await fetch('/api/uso/resumen');
			if (r.ok) datos = await r.json();
		} catch { /* sin datos */ }
		cargando = false;
	}

	$effect(() => { cargar(); const t = setInterval(cargar, 60000); return () => clearInterval(t); });

	const activos = $derived(datos?.activos_7d ?? 0);
	const total = $derived(datos?.total_7d ?? 0);
	const porApp = $derived(datos?.por_app ?? {});
	const porDia = $derived(datos?.por_dia ?? []);
	const porHora = $derived(datos?.por_hora ?? []);
	const porDiaSemana = $derived(datos?.por_dia_semana ?? []);
	const topEndpoints = $derived(datos?.top_endpoints ?? []);
	const topUsuarios = $derived(datos?.top_usuarios ?? []);
	const inactivos = $derived(datos?.inactivos ?? []);

	const maxHora = $derived(Math.max(1, ...porHora.map((x: any) => x.llamadas)));
	const maxDia = $derived(Math.max(1, ...porDia.map((x: any) => x.llamadas)));
	const maxDiaSemana = $derived(Math.max(1, ...porDiaSemana.map((x: any) => x.llamadas)));

	function nombreCorto(ep: string): string {
		return ep.replace('/api/', '').replace('/{', '/:').slice(0, 28);
	}
</script>

<div class="screen uso-apps">
	<div class="screen-titulo"><span class="ic">📱</span> Uso de Apps</div>

	{#if cargando}
		<div class="cargando">Cargando estadísticas...</div>
	{:else if !datos}
		<div class="cargando">Sin datos de uso</div>
	{:else}
		<!-- KPIs superiores -->
		<div class="kpis-bar">
			<div class="kpi">
				<span class="kpi-val">{total}</span>
				<span class="kpi-lab">Llamadas 7d</span>
			</div>
			<div class="kpi">
				<span class="kpi-val">{activos}</span>
				<span class="kpi-lab">Usuarios activos</span>
			</div>
			<div class="kpi">
				<span class="kpi-val">{porApp.admon ?? 0}</span>
				<span class="kpi-lab">Admon</span>
			</div>
			<div class="kpi">
				<span class="kpi-val">{porApp.field ?? 0}</span>
				<span class="kpi-lab">Field</span>
			</div>
			<div class="kpi">
				<span class="kpi-val">{inactivos.length}</span>
				<span class="kpi-lab">Inactivos</span>
			</div>
		</div>

		<div class="contenido">
			<!-- Columna izquierda: Horas pico + Días de la semana -->
			<div class="col-izq">
				<!-- Horas pico -->
				<div class="bloque">
					<div class="bloque-titulo">🕐 Horas pico de uso</div>
					<div class="barras-hora">
						{#each porHora as h}
							<div class="barra-hora">
								<span class="hora-label">{String(h.hora).padStart(2, '0')}:00</span>
								<div class="hora-track">
									<div class="hora-fill" style="width: {Math.max(2, Math.round(h.llamadas / maxHora * 100))}%"></div>
								</div>
								<span class="hora-val">{h.llamadas}</span>
							</div>
						{/each}
					</div>
				</div>

				<!-- Días de la semana -->
				<div class="bloque">
					<div class="bloque-titulo">📅 Uso por día de la semana</div>
					<div class="barras-dia">
						{#each porDiaSemana as d}
							<div class="barra-dia">
								<span class="dia-label">{d.dia?.slice(0, 3) ?? ''}</span>
								<div class="dia-track">
									<div class="dia-fill" style="width: {Math.max(2, Math.round(d.llamadas / maxDiaSemana * 100))}%"></div>
								</div>
								<span class="dia-val">{d.llamadas}</span>
							</div>
						{/each}
					</div>
				</div>
			</div>

			<!-- Columna derecha: Top usuarios + Top endpoints -->
			<div class="col-der">
				<!-- Top usuarios -->
				<div class="bloque">
					<div class="bloque-titulo">👤 Top usuarios (7 días)</div>
					<div class="lista">
						{#each topUsuarios as u, i}
							<div class="fila" style="animation-delay: {i * 0.05}s">
								<span class="rank">{i + 1}</span>
								<span class="nombre">{u.usuario}</span>
								<span class="val">{u.llamadas}</span>
							</div>
						{/each}
						{#if !topUsuarios.length}
							<div class="vacio">Sin datos</div>
						{/if}
					</div>
				</div>

				<!-- Top endpoints -->
				<div class="bloque">
					<div class="bloque-titulo">🔗 Funciones más usadas</div>
					<div class="lista">
						{#each topEndpoints as e, i}
							<div class="fila" style="animation-delay: {i * 0.05}s">
								<span class="endpoint">{nombreCorto(e.endpoint)}</span>
								<span class="val">{e.usos}</span>
							</div>
						{/each}
						{#if !topEndpoints.length}
							<div class="vacio">Sin datos</div>
						{/if}
					</div>
				</div>

				<!-- Inactivos -->
				{#if inactivos.length}
					<div class="bloque inactivos">
						<div class="bloque-titulo">😴 Sin actividad (7 días)</div>
						<div class="inactivos-list">
							{#each inactivos as nombre}
								<span class="inactivo-chip">{nombre}</span>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.screen { height: 100%; display: flex; flex-direction: column; gap: 0.75rem; }
	.screen-titulo { font-size: 1.8rem; font-weight: 800; color: var(--color-text); flex-shrink: 0; }
	.cargando { display: flex; align-items: center; justify-content: center; height: 100%; color: var(--color-text-muted); font-size: 1.2rem; }

	.kpis-bar { display: flex; gap: 0.75rem; flex-shrink: 0; flex-wrap: wrap; }
	.kpi { flex: 1; min-width: 90px; text-align: center; padding: 0.6rem 0.75rem; border-radius: 10px; background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); }
	.kpi-val { display: block; font-size: 1.8rem; font-weight: 800; color: var(--color-primary-light); line-height: 1; }
	.kpi-lab { display: block; font-size: 0.75rem; color: var(--color-text-muted); margin-top: 3px; text-transform: uppercase; letter-spacing: 0.05em; }

	.contenido { flex: 1; min-height: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; overflow: hidden; }
	.col-izq, .col-der { display: flex; flex-direction: column; gap: 0.75rem; min-height: 0; }

	.bloque { flex: 1; min-height: 0; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 0.75rem; overflow: hidden; display: flex; flex-direction: column; }
	.bloque-titulo { font-size: 1rem; font-weight: 700; color: var(--color-primary-light); margin-bottom: 0.5rem; flex-shrink: 0; }
	.bloque.inactivos { flex: 0 0 auto; }

	/* Barras de hora */
	.barras-hora { display: flex; flex-direction: column; gap: 0.15rem; overflow: hidden; flex: 1; }
	.barra-hora { display: flex; align-items: center; gap: 0.4rem; }
	.hora-label { font-size: 0.7rem; color: var(--color-text-muted); min-width: 38px; font-family: monospace; }
	.hora-track { flex: 1; height: 8px; background: rgba(255, 255, 255, 0.06); border-radius: 4px; overflow: hidden; }
	.hora-fill { height: 100%; background: linear-gradient(90deg, #3B82F6, #60A5FA); border-radius: 4px; transition: width 0.5s; }
	.hora-val { font-size: 0.7rem; font-weight: 700; color: #60A5FA; min-width: 30px; text-align: right; }

	/* Barras de día */
	.barras-dia { display: flex; flex-direction: column; gap: 0.3rem; }
	.barra-dia { display: flex; align-items: center; gap: 0.4rem; }
	.dia-label { font-size: 0.8rem; color: var(--color-text-muted); min-width: 32px; text-transform: capitalize; }
	.dia-track { flex: 1; height: 10px; background: rgba(255, 255, 255, 0.06); border-radius: 5px; overflow: hidden; }
	.dia-fill { height: 100%; background: linear-gradient(90deg, #8B5CF6, #A78BFA); border-radius: 5px; transition: width 0.5s; }
	.dia-val { font-size: 0.75rem; font-weight: 700; color: #A78BFA; min-width: 35px; text-align: right; }

	/* Lista */
	.lista { display: flex; flex-direction: column; gap: 0.25rem; overflow: hidden; flex: 1; }
	.fila { display: flex; align-items: center; gap: 0.5rem; padding: 0.3rem 0.5rem; border-radius: 6px; background: rgba(255, 255, 255, 0.03); animation: entrarStagger 0.4s ease both; }
	.rank { font-size: 0.75rem; font-weight: 800; color: var(--color-primary-light); min-width: 18px; }
	.nombre { flex: 1; font-size: 0.85rem; color: #e2e8f0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.endpoint { flex: 1; font-size: 0.75rem; color: #94a3b8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: monospace; }
	.val { font-size: 0.85rem; font-weight: 800; color: var(--color-primary-light); min-width: 40px; text-align: right; }

	.inactivos-list { display: flex; flex-wrap: wrap; gap: 0.3rem; }
	.inactivo-chip { font-size: 0.7rem; padding: 0.2rem 0.5rem; border-radius: 999px; background: rgba(239, 68, 68, 0.1); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.2); }

	.vacio { color: var(--color-text-muted); font-size: 0.85rem; text-align: center; padding: 1rem; }

	@keyframes entrarStagger {
		from { opacity: 0; transform: translateY(8px); }
		to { opacity: 1; transform: none; }
	}
</style>