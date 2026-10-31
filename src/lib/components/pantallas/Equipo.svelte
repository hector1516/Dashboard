<!-- Equipo.svelte - Pantalla unificada: Legends + Celebraciones + Notas -->
<script lang="ts">
	import { recortar, num } from '$lib/kiosk/format';
	import type { Snapshot, LegendRow, Cumpleanero, Aniversariero, Nota } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const lg = $derived(datos.legends);
	const ranking = $derived(lg.ranking ?? []);
	const ganador = $derived(lg.ganador_semana);
	const totalPuntos = $derived(lg.total_puntos ?? 0);

	const cumpleanos = $derived(datos.cumpleanos);
	const aniversarios = $derived(datos.aniversarios);
	const notas = $derived(datos.notas ?? []);

	const hoyCumple = $derived(cumpleanos.hoy ?? []);
	const mesCumple = $derived(cumpleanos.del_mes ?? []);
	const hoyAniv = $derived(aniversarios.hoy ?? []);
	const mesAniv = $derived(aniversarios.del_mes ?? []);

	function medalla(pos: number): string {
		return pos === 1 ? '🥇' : pos === 2 ? '🥈' : pos === 3 ? '🥉' : `#${pos}`;
	}

	function nivelColor(nivel: string): string {
		const colors: Record<string, string> = {
			'Leyenda': '#ff6b00',
			'Diamante': '#b9f2ff',
			'Oro': '#ffd700',
			'Plata': '#c0c0c0',
			'Bronce': '#cd7f32'
		};
		return colors[nivel] || '#94a3b8';
	}
</script>

<div class="screen equipo">
	<div class="screen-titulo"><span class="ic">👥</span> Equipo</div>

	<div class="contenido">
		<!-- Columna izquierda: Legends -->
		<div class="col-izq">
			<div class="bloque legends-bloque">
				<div class="bloque-titulo">🏆 ECCSA Legends</div>
				{#if ranking.length}
					<div class="legends-list">
						{#each ranking.slice(0, 6) as r, i}
							<div class="legend-row" style="animation-delay: {i * 0.06}s">
								<span class="legend-pos">{medalla(i + 1)}</span>
								<span class="legend-nombre">{r.nombre}</span>
								<span class="legend-nivel" style="color: {nivelColor(r.nivel)}">{r.nivel}</span>
								<span class="legend-pts">{num(r.puntos_semana)}</span>
							</div>
						{/each}
					</div>
					<div class="legends-footer">
						<span>Total semana: {num(totalPuntos)} pts</span>
						{#if ganador}
							<span>🏆 Ganador: {ganador.nombre}</span>
						{/if}
					</div>
				{:else}
					<div class="vacio">Sin ranking</div>
				{/if}
			</div>
		</div>

		<!-- Columna derecha: Celebraciones + Notas -->
		<div class="col-der">
			<!-- Celebraciones -->
			<div class="bloque">
				<div class="bloque-titulo">🎂 Celebraciones</div>
				{#if hoyCumple.length || hoyAniv.length}
					<div class="celeb-list">
						{#each hoyCumple as c}
							<div class="celeb-item cumple">
								<span class="celeb-icon">🎂</span>
								<span class="celeb-nombre">{c.Nombre}</span>
								<span class="celeb-detalle">{c.edad ? c.edad + ' años' : 'Hoy'}</span>
							</div>
						{/each}
						{#each hoyAniv as a}
							<div class="celeb-item aniv">
								<span class="celeb-icon">⭐</span>
								<span class="celeb-nombre">{a.Nombre}</span>
								<span class="celeb-detalle">{a.anos ? a.anos + ' años' : 'Aniversario'}</span>
							</div>
						{/each}
					</div>
				{:else}
					<div class="celeb-empty">Sin celebraciones hoy</div>
				{/if}
				{#if mesCumple.length || mesAniv.length}
					<div class="mes-list">
						{#each mesCumple.slice(0, 4) as c}
							<div class="mes-item">
								<span>🎂 {c.Nombre}</span>
								<span class="mes-fecha">{c.dia}/{c.mes}</span>
							</div>
						{/each}
						{#each mesAniv.slice(0, 4) as a}
							<div class="mes-item">
								<span>⭐ {a.Nombre}</span>
								<span class="mes-fecha">{a.dia} · {a.anos}a</span>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Notas -->
			<div class="bloque">
				<div class="bloque-titulo">📝 Notas</div>
				{#if notas.length}
					<div class="notas-grid">
						{#each notas.slice(0, 4) as n}
							<div class="nota-card" style="border-left: 3px solid {n.Color || '#FF6B00'}">
								<div class="nota-titulo">{recortar(n.Titulo, 28)}</div>
								<div class="nota-contenido">{recortar(n.Contenido, 70)}</div>
								<div class="nota-meta">{n.Autor}</div>
							</div>
						{/each}
					</div>
				{:else}
					<div class="vacio">Sin notas</div>
				{/if}
			</div>
		</div>
	</div>
</div>

<style>
	.screen { height: 100%; display: flex; flex-direction: column; gap: 0.75rem; }
	.screen-titulo { font-size: 1.8rem; font-weight: 800; color: var(--color-text); flex-shrink: 0; }

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

	/* Legends */
	.legends-list { display: flex; flex-direction: column; gap: 0.3rem; }
	.legend-row {
		display: flex; align-items: center; gap: 0.5rem;
		padding: 0.4rem 0.5rem; border-radius: 6px;
		background: rgba(255, 255, 255, 0.03);
		animation: entrarStagger 0.4s ease both;
	}
	.legend-pos { font-size: 1.1rem; min-width: 28px; }
	.legend-nombre { flex: 1; font-size: 0.9rem; font-weight: 600; color: #e2e8f0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.legend-nivel { font-size: 0.75rem; font-weight: 600; }
	.legend-pts { font-size: 0.85rem; font-weight: 700; color: var(--color-primary-light); min-width: 60px; text-align: right; }
	.legends-footer { display: flex; justify-content: space-between; margin-top: 0.5rem; font-size: 0.75rem; color: var(--color-text-muted); }

	/* Celebraciones */
	.celeb-list { display: flex; flex-direction: column; gap: 0.3rem; }
	.celeb-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.5rem; border-radius: 6px; background: rgba(255, 255, 255, 0.03); }
	.celeb-icon { font-size: 1.2rem; }
	.celeb-nombre { flex: 1; font-size: 0.9rem; font-weight: 600; color: #e2e8f0; }
	.celeb-detalle { font-size: 0.75rem; color: var(--color-text-muted); }
	.celeb-empty { color: var(--color-text-muted); font-size: 0.85rem; text-align: center; padding: 0.75rem; }
	.mes-list { margin-top: 0.5rem; display: flex; flex-direction: column; gap: 0.2rem; }
	.mes-item { display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--color-text-muted); padding: 0.2rem 0; }
	.mes-fecha { color: var(--color-primary-light); font-weight: 600; }

	/* Notas */
	.notas-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.4rem; }
	.nota-card { padding: 0.5rem 0.6rem; border-radius: 6px; background: rgba(255, 255, 255, 0.03); }
	.nota-titulo { font-size: 0.85rem; font-weight: 700; color: #e2e8f0; margin-bottom: 0.15rem; }
	.nota-contenido { font-size: 0.75rem; color: var(--color-text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.nota-meta { font-size: 0.65rem; color: #64748b; margin-top: 0.15rem; }

	.vacio { color: var(--color-text-muted); font-size: 0.85rem; text-align: center; padding: 1.5rem; }

	@keyframes entrarStagger {
		from { opacity: 0; transform: translateY(8px); }
		to { opacity: 1; transform: none; }
	}
</style>
