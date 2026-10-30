<!-- PanelControlIso.svelte - Panel de control industrial isométrico -->
<script lang="ts">
	import { iso, slab, TONES } from '$lib/iso/iso';
	import type { Snapshot } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const reportes = $derived(datos.reportes);
	const kilometros = $derived(datos.kilometros);
	const metricas = $derived(datos.metricas);

	const proj = { origin: [300, 180] as [number, number], scale: 3, azimuth: 45, elevation: 30 };

	const svgContent = $derived.by(() => {
		let svg = '';

		// Base plate
		svg += slab(0, 0, 80, 55, 5, proj, 'mid');

		// Main panel body
		svg += slab(5, 5, 70, 45, 20, proj, 'hi');

		// Gauges (round dials) - 4 gauges
		const gauges = [
			{ x: 12, y: 12, label: 'Rpts', value: reportes.total, max: 100, color: '#ff6b00' },
			{ x: 30, y: 12, label: 'Km', value: kilometros.total_semana, max: 1000, color: '#4caf50' },
			{ x: 48, y: 12, label: 'Tickets', value: datos.tickets.total_semana, max: 50, color: '#2196f3' },
			{ x: 66, y: 12, label: 'Firma', value: metricas.tasa_firma, max: 100, color: '#9c27b0' },
		];

		for (const g of gauges) {
			// Gauge housing
			svg += slab(g.x, g.y, 14, 14, 6, proj, 'lo');
			// Dial face
			const dialCenter = iso([g.x + 7, g.y + 7, 6], proj);
			svg += `<circle cx="${dialCenter[0]}" cy="${dialCenter[1]}" r="5" fill="#1a1a2e" stroke="${g.color}" stroke-width="1.5" />`;
			// Needle
			const pct = Math.min(1, g.value / g.max);
			const angle = -Math.PI * 0.75 + pct * Math.PI * 1.5;
			const needleEnd = iso([g.x + 7 + 4 * Math.cos(angle), g.y + 7 + 4 * Math.sin(angle), 6], proj);
			svg += `<line x1="${dialCenter[0]}" y1="${dialCenter[1]}" x2="${needleEnd[0]}" y2="${needleEnd[1]}" stroke="${g.color}" stroke-width="1.5" stroke-linecap="round" />`;
			// Label
			const labelPos = iso([g.x + 7, g.y + 16, 6], proj);
			svg += `<text x="${labelPos[0]}" y="${labelPos[1]}" font-size="5" fill="#aaa" text-anchor="middle">${g.label}</text>`;
		}

		// Switches (bottom row)
		for (let i = 0; i < 4; i++) {
			const sx = 10 + i * 15;
			svg += slab(sx, 40, 8, 6, 4, proj, 'mid');
			const switchPos = iso([sx + 4, 43, 4], proj);
			svg += `<rect x="${switchPos[0] - 2}" y="${switchPos[1] - 3}" width="4" height="6" fill="${i < 2 ? '#4caf50' : '#f44336'}" rx="1" />`;
		}

		// LED indicators (top)
		for (let i = 0; i < 6; i++) {
			const led = iso([8 + i * 10, 8, 20], proj);
			svg += `<circle cx="${led[0]}" cy="${led[1]}" r="2" fill="${i < 3 ? '#4caf50' : '#ff9800'}" />`;
		}

		// Screen/display (center bottom)
		svg += slab(25, 30, 30, 12, 8, proj, 'lit');
		const screenPos = iso([27, 32, 8], proj);
		svg += `<text x="${screenPos[0]}" y="${screenPos[1]}" font-size="6" fill="#4caf50" font-weight="bold">ECCSA</text>`;
		const screenPos2 = iso([27, 36, 8], proj);
		svg += `<text x="${screenPos2[0]}" y="${screenPos2[1]}" font-size="5" fill="#aaa">Control Panel</text>`;

		// Small PLC unit (side)
		svg += slab(70, 20, 8, 15, 12, proj, 'lo');
		for (let i = 0; i < 3; i++) {
			const plcLed = iso([72, 22 + i * 4, 12], proj);
			svg += `<circle cx="${plcLed[0]}" cy="${plcLed[1]}" r="1.5" fill="${i === 0 ? '#4caf50' : '#ff9800'}" />`;
		}

		// Corner screws
		const corners = [[6, 6], [74, 6], [6, 54], [74, 54]];
		for (const [cx, cy] of corners) {
			const screw = iso([cx, cy, 5], proj);
			svg += `<circle cx="${screw[0]}" cy="${screw[1]}" r="1.5" fill="#888" stroke="#555" stroke-width="0.5" />`;
		}

		return svg;
	});
</script>

<div class="iso-figure panel-control">
	<div class="figure-card">
		<div class="card-header">
			<span class="fig-num">Fig 3</span>
			<span class="fig-title">Panel de Control Industrial</span>
		</div>
		<svg viewBox="0 0 600 400" class="iso-svg">
			{@html svgContent}
		</svg>
		<div class="card-footer">
			<span class="hint">Reportes: {reportes.total} · Km: {kilometros.total_semana}</span>
			<span class="readout">
				Tickets: {datos.tickets.total_semana} · Firma: {metricas.tasa_firma}%
			</span>
		</div>
	</div>
	<div class="legend">
		<div class="legend-item"><span class="dot green"></span> Activo</div>
		<div class="legend-item"><span class="dot orange"></span> En espera</div>
		<div class="legend-item"><span class="dot red"></span> Inactivo</div>
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
	.dot.green { background: #4caf50; }
	.dot.orange { background: #ff9800; }
	.dot.red { background: #f44336; }
</style>
