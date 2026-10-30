<!-- LegendsIso.svelte - Máquina de puntos Legends isométrica ANIMADA -->
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

		// Gear system (animated rotation)
		const gearCx = 35, gearCy = 25;
		// Main gear
		svg += `<g class="gear-main">
			${Array.from({ length: 8 }, (_, i) => {
				const angle = (i / 8) * Math.PI * 2;
				const x = gearCx + 12 * Math.cos(angle);
				const y = gearCy + 12 * Math.sin(angle);
				return slab(x - 2, y - 2, 4, 4, 6, proj, 'lo');
			}).join('')}
			${slab(gearCx - 4, gearCy - 4, 8, 8, 8, proj, 'hi')}
			<animateTransform attributeName="transform" type="rotate" from="0 ${iso([gearCx, gearCy, 0], proj)[0]} ${iso([gearCx, gearCy, 0], proj)[1]}" to="360 ${iso([gearCx, gearCy, 0], proj)[0]} ${iso([gearCx, gearCy, 0], proj)[1]}" dur="8s" repeatCount="indefinite" />
		</g>`;

		// Secondary gear (counter-rotating)
		const gear2Cx = 52, gear2Cy = 20;
		svg += `<g class="gear-secondary">
			${Array.from({ length: 6 }, (_, i) => {
				const angle = (i / 6) * Math.PI * 2;
				const x = gear2Cx + 8 * Math.cos(angle);
				const y = gear2Cy + 8 * Math.sin(angle);
				return slab(x - 1.5, y - 1.5, 3, 3, 4, proj, 'lo');
			}).join('')}
			${slab(gear2Cx - 3, gear2Cy - 3, 6, 6, 5, proj, 'mid')}
			<animateTransform attributeName="transform" type="rotate" from="360 ${iso([gear2Cx, gear2Cy, 0], proj)[0]} ${iso([gear2Cx, gear2Cy, 0], proj)[1]}" to="0 ${iso([gear2Cx, gear2Cy, 0], proj)[0]} ${iso([gear2Cx, gear2Cy, 0], proj)[1]}" dur="6s" repeatCount="indefinite" />
		</g>`;

		// Dial gauge (top of gear)
		const dialCx = 35, dialCy = 25;
		const dialTop = iso([dialCx, dialCy, 12], proj);
		svg += `<circle cx="${dialTop[0]}" cy="${dialTop[1]}" r="12" fill="#1a1a2e" stroke="#ff6b00" stroke-width="2" />`;
		// Dial ticks
		for (let i = 0; i < 12; i++) {
			const angle = (i / 12) * Math.PI * 2 - Math.PI / 2;
			const inner = iso([dialCx + 9 * Math.cos(angle), dialCy + 9 * Math.sin(angle), 12], proj);
			const outer = iso([dialCx + 11 * Math.cos(angle), dialCy + 11 * Math.sin(angle), 12], proj);
			svg += `<line x1="${inner[0]}" y1="${inner[1]}" x2="${outer[0]}" y2="${outer[1]}" stroke="#ff6b00" stroke-width="1" />`;
		}
		// Needle (animated)
		const needleAngle = (totalPuntos % 100) / 100 * Math.PI * 1.5 - Math.PI * 0.75;
		const needleEnd = iso([dialCx + 8 * Math.cos(needleAngle), dialCy + 8 * Math.sin(needleAngle), 12], proj);
		svg += `<line x1="${dialTop[0]}" y1="${dialTop[1]}" x2="${needleEnd[0]}" y2="${needleEnd[1]}" stroke="#ff6b00" stroke-width="2.5" stroke-linecap="round">
			<animate attributeName="x2" values="${needleEnd[0]};${iso([dialCx + 8 * Math.cos(needleAngle + 0.3), dialCy + 8 * Math.sin(needleAngle + 0.3), 12], proj)[0]};${needleEnd[0]}" dur="3s" repeatCount="indefinite" />
			<animate attributeName="y2" values="${needleEnd[1]};${iso([dialCx + 8 * Math.cos(needleAngle + 0.3), dialCy + 8 * Math.sin(needleAngle + 0.3), 12], proj)[1]};${needleEnd[1]}" dur="3s" repeatCount="indefinite" />
		</line>`;
		// Center dot
		svg += `<circle cx="${dialTop[0]}" cy="${dialTop[1]}" r="3" fill="#ff6b00" />`;

		// Level indicators (lighting up sequentially)
		const levels = ['Bronce', 'Plata', 'Oro', 'Diamante', 'Leyenda'];
		const colors = ['#cd7f32', '#c0c0c0', '#ffd700', '#b9f2ff', '#ff6b00'];
		for (let i = 0; i < levels.length; i++) {
			const ly = 5 + i * 8;
			svg += slab(55, ly, 12, 6, 4, proj, 'mid');
			const label = iso([57, ly + 3, 4], proj);
			svg += `<text x="${label[0]}" y="${label[1]}" font-size="6" fill="${colors[i]}" font-weight="bold">
				${levels[i].slice(0, 3)}
				<animate attributeName="opacity" values="0.5;1;0.5" dur="${2 + i * 0.5}s" repeatCount="indefinite" begin="${i * 0.3}s" />
			</text>`;
			// LED indicator
			const ledPos = iso([54, ly + 3, 4], proj);
			svg += `<circle cx="${ledPos[0]}" cy="${ledPos[1]}" r="1.5" fill="${colors[i]}">
				<animate attributeName="opacity" values="0.3;1;0.3" dur="${1.5 + i * 0.3}s" repeatCount="indefinite" begin="${i * 0.2}s" />
			</circle>`;
		}

		// Streak counter (animated)
		svg += slab(5, 5, 15, 8, 6, proj, 'lit');
		const streakPos = iso([7, 7, 6], proj);
		svg += `<text x="${streakPos[0]}" y="${streakPos[1]}" font-size="8" fill="#ff6b00" font-weight="bold">
			${ranking[0]?.racha_dias ?? 0}🔥
			<animate attributeName="font-size" values="8;9;8" dur="2s" repeatCount="indefinite" />
		</text>`;

		// Trophy (pulsing)
		svg += slab(30, 20, 10, 10, 15, proj, 'lit');
		const trophyTop = iso([35, 25, 15], proj);
		svg += `<text x="${trophyTop[0]}" y="${trophyTop[1]}" font-size="12" text-anchor="middle">
			🏆
			<animate attributeName="font-size" values="12;14;12" dur="2.5s" repeatCount="indefinite" />
			<animate attributeName="opacity" values="1;0.8;1" dur="2.5s" repeatCount="indefinite" />
		</text>`;

		// Small person figures for top 3 (with bounce)
		for (let i = 0; i < Math.min(ranking.length, 3); i++) {
			const r = ranking[i];
			const px = 10 + i * 15;
			const py = 40;
			svg += slab(px, py, 4, 4, 6, proj, i === 0 ? 'lit' : 'mid');
			const head = iso([px + 2, py + 2, 8], proj);
			svg += `<circle cx="${head[0]}" cy="${head[1]}" r="2" fill="${i === 0 ? '#ffd700' : '#c0c0c0'}">
				<animate attributeName="cy" values="${head[1]};${head[1] - 3};${head[1]}" dur="${2 + i * 0.5}s" repeatCount="indefinite" />
			</circle>`;
		}

		// Sparkles around trophy
		for (let i = 0; i < 4; i++) {
			const sp = iso([35 + 6 * Math.cos(i * Math.PI / 2), 25 + 6 * Math.sin(i * Math.PI / 2), 18], proj);
			svg += `<circle cx="${sp[0]}" cy="${sp[1]}" r="1" fill="#ffd700" opacity="0.6">
				<animate attributeName="opacity" values="0.2;0.8;0.2" dur="${1.5 + i * 0.3}s" repeatCount="indefinite" begin="${i * 0.4}s" />
				<animate attributeName="r" values="0.5;1.5;0.5" dur="${1.5 + i * 0.3}s" repeatCount="indefinite" begin="${i * 0.4}s" />
			</circle>`;
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
	.gear-main, .gear-secondary { transform-box: fill-box; }
</style>
