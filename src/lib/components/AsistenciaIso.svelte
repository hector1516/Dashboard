<!-- AsistenciaIso.svelte - Checador de asistencia isométrico -->
<script lang="ts">
	import { iso, slab, TONES } from '$lib/iso/iso';
	import type { Snapshot } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const asist = $derived(datos.asistencia);
	const dentro = $derived(asist.dentro);
	const total = $derived(asist.total);
	const personas = $derived(asist.personas);

	// Projection
	const proj = { origin: [300, 200] as [number, number], scale: 3, azimuth: 45, elevation: 30 };

	// Generate the SVG
	const svgContent = $derived.by(() => {
		let svg = '';

		// Base plate
		svg += slab(0, 0, 60, 40, 3, proj, 'mid');

		// Card reader post
		svg += slab(25, 15, 6, 6, 25, proj, 'hi');

		// Card slot (on the post)
		const slotTL = iso([27, 15, 18], proj);
		const slotTR = iso([29, 15, 18], proj);
		const slotBL = iso([27, 15, 14], proj);
		const slotBR = iso([29, 15, 14], proj);
		svg += `<polygon points="${slotTL[0]},${slotTL[1]} ${slotTR[0]},${slotTR[1]} ${slotBR[0]},${slotBR[1]} ${slotBL[0]},${slotBL[1]}" fill="#ff6b00" />`;

		// Turnstile (rotating bar)
		svg += slab(10, 10, 4, 4, 15, proj, 'lo');
		// Turnstile arms
		const arm1 = iso([12, 12, 15], proj);
		const arm2 = iso([12, 8, 15], proj);
		svg += `<line x1="${arm1[0]}" y1="${arm1[1]}" x2="${arm2[0]}" y2="${arm2[1]}" stroke="#4caf50" stroke-width="3" stroke-linecap="round" />`;

		// Counter display
		svg += slab(40, 10, 15, 8, 8, proj, 'lit');

		// LED indicators
		for (let i = 0; i < 3; i++) {
			const led = iso([42 + i * 4, 12, 8], proj);
			svg += `<circle cx="${led[0]}" cy="${led[1]}" r="2" fill="${i < dentro ? '#4caf50' : '#f44336'}" />`;
		}

		// Small person figures (simplified)
		for (let i = 0; i < Math.min(personas.length, 5); i++) {
			const p = personas[i];
			const px = 5 + (i % 3) * 8;
			const py = 25 + Math.floor(i / 3) * 8;
			// Body (slab)
			svg += slab(px, py, 3, 3, 8, proj, p.en_sitio ? 'lit' : 'lo');
			// Head (sphere approximated as small cylinder)
			const head = iso([px + 1.5, py + 1.5, 10], proj);
			svg += `<circle cx="${head[0]}" cy="${head[1]}" r="2.5" fill="${p.en_sitio ? '#4caf50' : '#9e9e9e'}" />`;
		}

		return svg;
	});
</script>

<div class="iso-figure asistencia">
	<div class="figure-card">
		<div class="card-header">
			<span class="fig-num">Fig 1</span>
			<span class="fig-title">Checador de Asistencia</span>
		</div>
		<svg viewBox="0 0 600 400" class="iso-svg">
			{@html svgContent}
		</svg>
		<div class="card-footer">
			<span class="hint">Interacción: hover para ver detalles</span>
			<span class="readout">
				{dentro} en sitio · {total} total
			</span>
		</div>
	</div>
	<div class="legend">
		<div class="legend-item"><span class="dot green"></span> En sitio</div>
		<div class="legend-item"><span class="dot red"></span> Salió</div>
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
	.readout { color: #4caf50; font-weight: 700; }
	.legend { display: flex; gap: 16px; margin-top: 8px; font-size: 12px; color: #aaa; }
	.legend-item { display: flex; align-items: center; gap: 4px; }
	.dot { width: 8px; height: 8px; border-radius: 50%; }
	.dot.green { background: #4caf50; }
	.dot.red { background: #f44336; }
</style>
