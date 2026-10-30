<!-- LegendsIso.svelte - Máquina de puntos Legends isométrica -->
<script lang="ts">
	import { iso, slab, TONES } from '$lib/iso/iso';
	import type { Snapshot } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const legends = $derived(datos.legends);
	const ranking = $derived(legends.ranking ?? []);
	const ganador = $derived(legends.ganador_semana);
	const totalPuntos = $derived(legends.total_puntos ?? 0);

	const proj = { origin: [300, 180] as [number, number], scale: 3, azimuth: 45, elevation: 30 };

	const svgContent = $derived.by(() => {
		let svg = '';

		// Base plate
		svg += slab(0, 0, 70, 50, 4, proj, 'mid');

		// Main gear (center) - represents points
		const gearCx = 35, gearCy = 25;
		for (let i = 0; i < 8; i++) {
			const angle = (i / 8) * Math.PI * 2;
			const x = gearCx + 12 * Math.cos(angle);
			const y = gearCy + 12 * Math.sin(angle);
			svg += slab(x - 2, y - 2, 4, 4, 6, proj, 'lo');
		}
		// Gear center
		svg += slab(gearCx - 4, gearCy - 4, 8, 8, 8, proj, 'hi');

		// Dial gauge (top of gear)
		const dialCx = 35, dialCy = 25;
		const dialTop = iso([dialCx, dialCy, 12], proj);
		svg += `<circle cx="${dialTop[0]}" cy="${dialTop[1]}" r="12" fill="#1a1a2e" stroke="#ff6b00" stroke-width="2" />`;
		// Needle
		const needleAngle = (totalPuntos % 100) / 100 * Math.PI * 1.5 - Math.PI * 0.75;
		const needleEnd = iso([dialCx + 8 * Math.cos(needleAngle), dialCy + 8 * Math.sin(needleAngle), 12], proj);
		svg += `<line x1="${dialTop[0]}" y1="${dialTop[1]}" x2="${needleEnd[0]}" y2="${needleEnd[1]}" stroke="#ff6b00" stroke-width="2" stroke-linecap="round" />`;

		// Level indicators (small slabs on the side)
		const levels = ['Bronce', 'Plata', 'Oro', 'Diamante', 'Leyenda'];
		const colors = ['#cd7f32', '#c0c0c0', '#ffd700', '#b9f2ff', '#ff6b00'];
		for (let i = 0; i < levels.length; i++) {
			const ly = 5 + i * 8;
			svg += slab(55, ly, 12, 6, 4, proj, 'mid');
			const label = iso([57, ly + 3, 4], proj);
			svg += `<text x="${label[0]}" y="${label[1]}" font-size="6" fill="${colors[i]}" font-weight="bold">${levels[i].slice(0, 3)}</text>`;
		}

		// Streak counter (small display)
		svg += slab(5, 5, 15, 8, 6, proj, 'lit');
		const streakPos = iso([7, 7, 6], proj);
		svg += `<text x="${streakPos[0]}" y="${streakPos[1]}" font-size="8" fill="#ff6b00" font-weight="bold">${ranking[0]?.racha_dias ?? 0}🔥</text>`;

		// Trophy (top center)
		svg += slab(30, 20, 10, 10, 15, proj, 'lit');
		const trophyTop = iso([35, 25, 15], proj);
		svg += `<text x="${trophyTop[0]}" y="${trophyTop[1]}" font-size="12" text-anchor="middle">🏆</text>`;

		// Small person figures for top 3
		for (let i = 0; i < Math.min(ranking.length, 3); i++) {
			const r = ranking[i];
			const px = 10 + i * 15;
			const py = 40;
			svg += slab(px, py, 4, 4, 6, proj, i === 0 ? 'lit' : 'mid');
			const head = iso([px + 2, py + 2, 8], proj);
			svg += `<circle cx="${head[0]}" cy="${head[1]}" r="2" fill="${i === 0 ? '#ffd700' : '#c0c0c0'}" />`;
		}

		return svg;
	});
</script>

<div class="iso-figure legends">
	<div class="figure-card">
		<div class="card-header">
			<span class="fig-num">Fig 2</span>
			<span class="fig-title">Máquina de Legends</span>
		</div>
		<svg viewBox="0 0 600 400" class="iso-svg">
			{@html svgContent}
		</svg>
		<div class="card-footer">
			<span class="hint">Puntos totales: {totalPuntos}</span>
			<span class="readout">
				{ranking[0]?.nombre ?? '—'} · {ranking[0]?.puntos_semana ?? 0} pts
			</span>
		</div>
	</div>
	<div class="legend">
		<div class="legend-item"><span class="dot gold"></span> 1° lugar</div>
		<div class="legend-item"><span class="dot silver"></span> 2° lugar</div>
		<div class="legend-item"><span class="dot bronze"></span> 3° lugar</div>
	</div>
</div>

<style>
	.iso-figure { width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; }
	.figure-card {
		width: 100%; max-width: 600px;
		background: rgba(20, 20, 30, 0.6);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px; padding: 12px;
	}
	.card-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
	.fig-num { font-size: 12px; color: #888; font-weight: 600; }
	.fig-title { font-size: 14px; color: #fff; font-weight: 700; }
	.iso-svg { width: 100%; height: auto; }
	.card-footer { display: flex; justify-content: space-between; margin-top: 8px; font-size: 12px; color: #aaa; }
	.readout { color: #ff6b00; font-weight: 700; }
	.legend { display: flex; gap: 16px; margin-top: 8px; font-size: 12px; color: #aaa; }
	.legend-item { display: flex; align-items: center; gap: 4px; }
	.dot { width: 8px; height: 8px; border-radius: 50%; }
	.dot.gold { background: #ffd700; }
	.dot.silver { background: #c0c0c0; }
	.dot.bronze { background: #cd7f32; }
</style>
