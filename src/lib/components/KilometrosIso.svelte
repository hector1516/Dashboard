<!-- KilometrosIso.svelte - Odómetro mecánico isométrico -->
<script lang="ts">
	import { iso, slab, TONES } from '$lib/iso/iso';
	import type { Snapshot } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const km = $derived(datos.kilometros);
	const totalSemana = $derived(km.total_semana);
	const hoy = $derived(km.hoy);
	const vehiculos = $derived(km.por_vehiculo ?? []);

	const proj = { origin: [300, 180] as [number, number], scale: 3, azimuth: 45, elevation: 30 };

	// Format km as digits
	const kmStr = $derived(String(Math.round(totalSemana)).padStart(6, '0'));

	const svgContent = $derived.by(() => {
		let svg = '';

		// Base plate
		svg += slab(0, 0, 70, 50, 4, proj, 'mid');

		// Odometer housing
		svg += slab(10, 10, 50, 25, 15, proj, 'hi');

		// Odometer window (glass)
		svg += slab(12, 12, 46, 21, 12, proj, 'lit');

		// Digit wheels (6 digits)
		for (let i = 0; i < 6; i++) {
			const dx = 14 + i * 7.5;
			svg += slab(dx, 14, 6, 17, 10, proj, 'lo');
			// Digit display (white on black)
			const digitPos = iso([dx + 3, 16, 10], proj);
			svg += `<text x="${digitPos[0]}" y="${digitPos[1]}" font-size="8" fill="#4caf50" font-weight="bold" text-anchor="middle" font-family="monospace">${kmStr[i]}</text>`;
		}

		// "KM" label
		const kmLabel = iso([35, 30, 12], proj);
		svg += `<text x="${kmLabel[0]}" y="${kmLabel[1]}" font-size="6" fill="#aaa" text-anchor="middle">KM SEMANA</text>`;

		// Small vehicle on track (side)
		svg += slab(60, 35, 8, 6, 4, proj, 'lit');
		// Wheels
		const w1 = iso([62, 37, 2], proj);
		const w2 = iso([66, 37, 2], proj);
		svg += `<circle cx="${w1[0]}" cy="${w1[1]}" r="2" fill="#333" />`;
		svg += `<circle cx="${w2[0]}" cy="${w2[1]}" r="2" fill="#333" />`;
		// Vehicle body
		svg += slab(61, 36, 6, 4, 3, proj, 'mid');

		// Track
		svg += slab(0, 38, 70, 4, 2, proj, 'lo');

		// Consumption gauge (small)
		svg += slab(5, 40, 12, 8, 6, proj, 'lo');
		const gaugeCenter = iso([11, 44, 6], proj);
		svg += `<circle cx="${gaugeCenter[0]}" cy="${gaugeCenter[1]}" r="4" fill="#1a1a2e" stroke="#2196f3" stroke-width="1" />`;
		const consPct = Math.min(1, hoy / Math.max(1, totalSemana));
		const consAngle = -Math.PI * 0.75 + consPct * Math.PI * 1.5;
		const consEnd = iso([11 + 3 * Math.cos(consAngle), 44 + 3 * Math.sin(consAngle), 6], proj);
		svg += `<line x1="${gaugeCenter[0]}" y1="${gaugeCenter[1]}" x2="${consEnd[0]}" y2="${consEnd[1]}" stroke="#2196f3" stroke-width="1.5" stroke-linecap="round" />`;
		const consLabel = iso([11, 50, 6], proj);
		svg += `<text x="${consLabel[0]}" y="${consLabel[1]}" font-size="4" fill="#aaa" text-anchor="middle">Hoy</text>`;

		// Corner screws
		const corners = [[2, 2], [68, 2], [2, 48], [68, 48]];
		for (const [cx, cy] of corners) {
			const screw = iso([cx, cy, 4], proj);
			svg += `<circle cx="${screw[0]}" cy="${screw[1]}" r="1" fill="#888" />`;
		}

		// Vehicle labels
		for (let i = 0; i < Math.min(vehiculos.length, 3); i++) {
			const v = vehiculos[i];
			const vx = 5 + i * 22;
			const vy = 5;
			svg += slab(vx, vy, 18, 4, 3, proj, 'mid');
			const vLabel = iso([vx + 2, vy + 2, 3], proj);
			svg += `<text x="${vLabel[0]}" y="${vLabel[1]}" font-size="4" fill="#fff">${(v.MarcaModelo || '').slice(0, 8)}</text>`;
		}

		return svg;
	});
</script>

<div class="iso-figure kilometros">
	<div class="figure-card">
		<div class="card-header">
			<span class="fig-num">Fig 4</span>
			<span class="fig-title">Odómetro Mecánico</span>
		</div>
		<svg viewBox="0 0 600 400" class="iso-svg">
			{@html svgContent}
		</svg>
		<div class="card-footer">
			<span class="hint">Hoy: {hoy} km · {vehiculos.length} vehículos</span>
			<span class="readout">
				{totalSemana} km esta semana
			</span>
		</div>
	</div>
	<div class="legend">
		<div class="legend-item"><span class="dot green"></span> En movimiento</div>
		<div class="legend-item"><span class="dot blue"></span> Consumo</div>
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
	.readout { color: #2196f3; font-weight: 700; }
	.legend { display: flex; gap: 16px; margin-top: 8px; font-size: 12px; color: #aaa; }
	.legend-item { display: flex; align-items: center; gap: 4px; }
	.dot { width: 8px; height: 8px; border-radius: 50%; }
	.dot.green { background: #4caf50; }
	.dot.blue { background: #2196f3; }
</style>
