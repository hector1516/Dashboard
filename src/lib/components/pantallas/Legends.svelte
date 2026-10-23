<!--
	🏆 ECCSA Legends — competencia semanal + temporada, racha y logros.

	La TV se mira de lejos y de reojo: tipografía grande, contraste alto y una
	sola jerarquía. Se quitaron los rayos, el latido y las partículas del diseño
	anterior; el movimiento queda en la entrada estándar de las pantallas.

	El ganador de la semana ocupa la tarjeta izquierda. A la derecha va la tabla
	completa: puntos de la semana, nivel de la temporada, racha y logros. Los
	puntos salen de HUB_ScoreLog (el snapshotter los trae cada 2 min) y el
	backend calcula el nivel con el trimestre, igual que Field y Admon.
-->
<script lang="ts">
	import { avatarSrc } from '$lib/kiosk/api';
	import { medalla, hhmmDiff, num } from '$lib/kiosk/format';
	import type { Snapshot } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const ranking = $derived(datos.legends.ranking ?? []);
	const visibles = $derived(ranking.slice(0, 10));
	const lider = $derived(ranking[0]);
	const campeon = $derived(datos.legends.ganador_semana);
	const participantes = $derived(datos.legends.participantes ?? ranking.length);
	const restantes = $derived(Math.max(0, ranking.length - visibles.length));
	const semana = $derived(datos.legends.semana);
	const temporada = $derived(datos.legends.temporada);

	function iniciales(nombre: string | null | undefined) {
		const partes = (nombre || '?').trim().split(/\s+/).filter(Boolean);
		if (!partes.length) return '?';
		if (partes.length === 1) return partes[0].slice(0, 2).toUpperCase();
		return (partes[0][0] + partes[1][0]).toUpperCase();
	}

	function fecha(iso: string | null | undefined) {
		if (!iso) return '';
		const d = new Date(String(iso).length <= 10 ? String(iso) + 'T00:00:00' : String(iso));
		if (Number.isNaN(d.getTime())) return String(iso).slice(0, 10);
		return d.toLocaleDateString('es-MX', { day: 'numeric', month: 'short' });
	}

	function flecha(pos: number | undefined, antes: number | null | undefined) {
		if (!antes || !pos || antes === pos) return '';
		return antes > pos ? '▲' : '▼';
	}

	function claseFlecha(pos: number | undefined, antes: number | null | undefined) {
		if (!antes || !pos || antes === pos) return '';
		return antes > pos ? 'subio' : 'bajo';
	}
</script>

<div class="screen legends">
	<div class="screen-titulo">
		<span class="ic">🏆</span> ECCSA Legends
		<span class="sep">·</span>
		Carrera semanal
		{#if datos.legends.reset_en_segundos > 0}
			<span class="reset">cierra en {hhmmDiff(datos.legends.reset_en_segundos)}</span>
		{/if}
	</div>

	{#if !lider}
		<div class="vacio">
			Sin ranking esta semana
			<span class="vacio-sub">
				Aquí aparece quien tenga nickname y passkey registrados en Field o Admon
			</span>
		</div>
	{:else}
		<div class="contenido">
			<section class="lider-card">
				<p class="kicker">LÍDER DE LA SEMANA</p>

				<div class="lider-top">
					<div class="avatar-lider" style={`--nivel-color:${lider.color_nivel || '#FFD700'}`}>
						{#if lider.avatar}
							<img src={avatarSrc(lider.avatar)} alt="" />
						{:else}
							{iniciales(lider.nickname || lider.nombre)}
						{/if}
					</div>
					<div class="lider-info">
						<h1>{lider.nickname || lider.nombre}</h1>
						{#if lider.nickname && lider.nombre && lider.nickname !== lider.nombre}
							<p class="nombre-real">{lider.nombre}</p>
						{/if}
						<div class="puntos-lider">{num(lider.puntos_semana)}<span>pts</span></div>
						<div class="nivel-lider" style={`--nivel-color:${lider.color_nivel || '#FFD700'}`}>
							{lider.icono_nivel} {lider.nivel}
							{#if flecha(lider.posicion, lider.puesto_anterior)}
								<span class={claseFlecha(lider.posicion, lider.puesto_anterior)}>
									{flecha(lider.posicion, lider.puesto_anterior)}
								</span>
							{/if}
						</div>
					</div>
				</div>

				<div class="mini-kpis">
					<div>
						<b>{num(lider.puntos_temporada)}</b>
						<span>puntos de temporada</span>
					</div>
					<div>
						<b>🔥 {num(lider.racha_dias)}</b>
						<span>días de racha</span>
					</div>
					<div>
						<b>🎖️ {num(lider.logros_desbloqueados)}</b>
						<span>logros</span>
					</div>
				</div>

				<div class="temporada">
					<div class="temporada-head">
						<span>{temporada?.nombre || 'Temporada'}</span>
						<span>{temporada?.dias_restantes ?? 0} días</span>
					</div>
					<p>
						El nivel se gana con los puntos del trimestre, no con el historial.
						La semana reinicia el domingo a las 00:00.
					</p>
				</div>

				<div class="regla">
					<span class="regla-ic">💡</span>
					<p>
						Si le haces <b>ganar dinero</b> a ECCSA, ganas puntos. Si le haces
						<b>perder dinero</b>, pierdes puntos. Una cotización pagada vale de
						<b>+15 a +75</b> según el monto.
					</p>
				</div>
			</section>

			<section class="tabla-card">
				<header class="tabla-head">
					<div>
						<h2>Tabla de la semana</h2>
						<p>{participantes} participante{participantes === 1 ? '' : 's'}</p>
					</div>
					{#if semana?.inicio}
						<div class="semana">{fecha(semana.inicio)} → {fecha(semana.fin)}</div>
					{/if}
				</header>

				{#if campeon}
					<div class="campeon">
						<span>🏆</span>
						<span>Semana pasada: <b>{campeon.nickname || campeon.nombre}</b></span>
						<span class="campeon-pts">{num(campeon.puntos)} pts</span>
					</div>
				{/if}

				<div class="filas">
					{#each visibles as r, i (r.id_usuario ?? i)}
						<article
							class="fila"
							class:oro={r.posicion === 1}
							class:plata={r.posicion === 2}
							class:bronce={r.posicion === 3}
						>
							<span class="pos">{medalla(r.posicion ?? i + 1)}</span>

							<div class="avatar-med" style={`--nivel-color:${r.color_nivel || '#FFD700'}`}>
								{#if r.avatar}
									<img src={avatarSrc(r.avatar)} alt="" />
								{:else}
									{iniciales(r.nickname || r.nombre)}
								{/if}
							</div>

							<div class="quien">
								<strong>{r.nickname || r.nombre}</strong>
								<span>
									{r.icono_nivel} {r.nivel}
									{#if r.racha_dias > 0}· 🔥 {r.racha_dias} días{/if}
									{#if r.logros_desbloqueados > 0}· 🎖️ {r.logros_desbloqueados} logros{/if}
								</span>
							</div>

							<div class="pts">
								<b>{num(r.puntos_semana)}</b>
								<span>esta semana</span>
							</div>

							<div class="temporada-pts">
								<b>{num(r.puntos_temporada)}</b>
								<span>temporada</span>
							</div>

							<span class="delta {claseFlecha(r.posicion, r.puesto_anterior)}">
								{flecha(r.posicion, r.puesto_anterior)}
							</span>
						</article>
					{/each}
				</div>

				{#if restantes > 0}
					<p class="mas">+ {restantes} participante{restantes === 1 ? '' : 's'} más en la tabla</p>
				{/if}

				<footer class="pie">
					Los puntos se recalculan cada 5 minutos · el nivel es de la temporada
				</footer>
			</section>
		</div>
	{/if}
</div>

<style>
	.legends { gap: 10px; }
	.sep { color: #475569; font-weight: 700; }
	.reset { font-size: 17px; font-weight: 700; color: var(--color-text-muted); letter-spacing: 0; }

	.contenido {
		flex: 1 1 auto;
		min-height: 0;
		display: grid;
		grid-template-columns: 540px minmax(0, 1fr);
		gap: 18px;
	}

	/* ── Tarjeta del líder ─────────────────────────────────────── */
	.lider-card {
		min-height: 0;
		display: flex;
		flex-direction: column;
		padding: 20px 24px;
		border-radius: 22px;
		background:
			linear-gradient(155deg, rgba(255, 174, 0, 0.13), rgba(255, 255, 255, 0.035) 48%, rgba(255, 255, 255, 0.02));
		border: 1px solid rgba(255, 174, 0, 0.24);
		overflow: hidden;
	}
	.kicker {
		margin: 0 0 14px;
		font-size: 15px;
		font-weight: 900;
		letter-spacing: 0.14em;
		color: #FFAE00;
	}
	.lider-top { display: flex; align-items: center; gap: 22px; }
	.avatar-lider {
		width: 164px;
		height: 164px;
		flex-shrink: 0;
		border-radius: 50%;
		border: 5px solid var(--nivel-color, #FFD700);
		background: rgba(255, 255, 255, 0.06);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 54px;
		font-weight: 900;
		color: #0F172A;
		overflow: hidden;
		box-shadow: 0 0 0 8px rgba(255, 174, 0, 0.06);
	}
	.avatar-lider img { width: 100%; height: 100%; object-fit: cover; }
	.lider-info { min-width: 0; }
	.lider-info h1 {
		margin: 0;
		font-size: 43px;
		line-height: 1.04;
		font-weight: 900;
		color: #FFD700;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.nombre-real {
		margin: 4px 0 0;
		font-size: 18px;
		font-weight: 600;
		color: var(--color-text-muted);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.puntos-lider {
		margin-top: 6px;
		font-size: 76px;
		line-height: 0.95;
		font-weight: 900;
		color: var(--color-primary-light);
		font-variant-numeric: tabular-nums;
	}
	.puntos-lider span {
		margin-left: 8px;
		font-size: 23px;
		font-weight: 700;
		color: var(--color-text-muted);
	}
	.nivel-lider {
		display: inline-flex;
		align-items: center;
		gap: 7px;
		margin-top: 8px;
		padding: 5px 12px;
		border-radius: 999px;
		border: 1px solid var(--nivel-color, #FFD700);
		color: var(--nivel-color, #FFD700);
		font-size: 21px;
		font-weight: 800;
	}

	.mini-kpis {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 10px;
		margin-top: 22px;
	}
	.mini-kpis > div {
		padding: 12px 14px;
		border-radius: 14px;
		background: rgba(255, 255, 255, 0.045);
		border: 1px solid rgba(255, 255, 255, 0.08);
		min-width: 0;
	}
	.mini-kpis b {
		display: block;
		font-size: 32px;
		line-height: 1.05;
		font-weight: 900;
		color: #E2E8F0;
		font-variant-numeric: tabular-nums;
	}
	.mini-kpis span {
		display: block;
		margin-top: 4px;
		font-size: 13px;
		font-weight: 600;
		color: var(--color-text-muted);
	}

	.temporada { margin-top: auto; padding-top: 22px; }
	.temporada-head {
		display: flex;
		justify-content: space-between;
		gap: 12px;
		font-size: 16px;
		font-weight: 800;
		color: var(--color-text);
	}
	.temporada p {
		margin: 8px 0 0;
		font-size: 15px;
		line-height: 1.35;
		font-weight: 600;
		color: var(--color-text-muted);
	}

	.regla {
		display: flex;
		gap: 12px;
		margin-top: 16px;
		padding: 14px 16px;
		border-radius: 14px;
		background: rgba(255, 107, 0, 0.09);
		border: 1px solid rgba(255, 107, 0, 0.24);
	}
	.regla-ic { font-size: 24px; line-height: 1.2; }
	.regla p {
		margin: 0;
		font-size: 17px;
		line-height: 1.35;
		color: #FED7AA;
	}
	.regla b { color: #fff; }

	/* ── Tabla ─────────────────────────────────────────────────── */
	.tabla-card {
		min-height: 0;
		display: flex;
		flex-direction: column;
		padding: 16px 18px 12px;
		border-radius: 22px;
		background: rgba(255, 255, 255, 0.035);
		border: 1px solid rgba(255, 255, 255, 0.085);
		overflow: hidden;
	}
	.tabla-head {
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
		gap: 16px;
		padding: 0 6px 12px;
	}
	.tabla-head h2 {
		margin: 0;
		font-size: 28px;
		font-weight: 900;
		color: #F8FAFC;
	}
	.tabla-head p {
		margin: 2px 0 0;
		font-size: 14px;
		font-weight: 600;
		color: var(--color-text-muted);
	}
	.semana {
		font-size: 16px;
		font-weight: 700;
		color: var(--color-text-muted);
		white-space: nowrap;
	}

	.campeon {
		display: flex;
		align-items: center;
		gap: 10px;
		margin-bottom: 10px;
		padding: 9px 14px;
		border-radius: 12px;
		background: rgba(255, 215, 0, 0.08);
		border: 1px solid rgba(255, 215, 0, 0.22);
		font-size: 17px;
		color: #FDE68A;
	}
	.campeon b { color: #fff; }
	.campeon-pts { margin-left: auto; font-weight: 900; color: #FFD700; white-space: nowrap; }

	.filas {
		flex: 1 1 auto;
		min-height: 0;
		display: grid;
		grid-auto-rows: 1fr;
		gap: 6px;
	}
	.fila {
		display: grid;
		grid-template-columns: 50px 54px minmax(0, 1fr) 110px 96px 24px;
		align-items: center;
		gap: 12px;
		min-height: 0;
		padding: 0 12px;
		border-radius: 12px;
		background: rgba(255, 255, 255, 0.035);
		border: 1px solid transparent;
	}
	.fila.oro {
		background: linear-gradient(90deg, rgba(255, 215, 0, 0.14), rgba(255, 215, 0, 0.035));
		border-color: rgba(255, 215, 0, 0.26);
	}
	.fila.plata { background: rgba(203, 213, 225, 0.095); border-color: rgba(203, 213, 225, 0.2); }
	.fila.bronce { background: rgba(217, 119, 6, 0.1); border-color: rgba(217, 119, 6, 0.2); }

	.pos {
		font-size: 26px;
		font-weight: 900;
		text-align: center;
		color: #CBD5E1;
		font-variant-numeric: tabular-nums;
	}
	.avatar-med {
		width: 54px;
		height: 54px;
		border-radius: 50%;
		overflow: hidden;
		border: 3px solid var(--nivel-color, #FFD700);
		background: rgba(255, 255, 255, 0.06);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 20px;
		font-weight: 900;
		color: #0F172A;
	}
	.avatar-med img { width: 100%; height: 100%; object-fit: cover; }

	.quien { min-width: 0; display: flex; flex-direction: column; gap: 2px; }
	.quien strong {
		font-size: 25px;
		font-weight: 800;
		color: #F1F5F9;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.quien span {
		font-size: 14px;
		font-weight: 600;
		color: var(--color-text-muted);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.pts, .temporada-pts { text-align: right; font-variant-numeric: tabular-nums; }
	.pts b {
		display: block;
		font-size: 30px;
		line-height: 1;
		font-weight: 900;
		color: #FFAE00;
	}
	.temporada-pts b {
		display: block;
		font-size: 23px;
		line-height: 1;
		font-weight: 800;
		color: #CBD5E1;
	}
	.pts span, .temporada-pts span {
		display: block;
		margin-top: 3px;
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: #64748B;
	}
	.delta { font-size: 18px; font-weight: 900; text-align: center; color: #64748B; }
	.delta.subio { color: #4ADE80; }
	.delta.bajo { color: #F87171; }

	.mas {
		margin: 8px 0 0;
		font-size: 14px;
		font-weight: 700;
		text-align: center;
		color: #64748B;
	}
	.pie {
		flex-shrink: 0;
		padding-top: 9px;
		font-size: 12px;
		font-weight: 600;
		text-align: center;
		color: #475569;
	}
</style>
