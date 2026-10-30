// iso.ts - Shared isometric projection utilities for Svelte
// Based on anatomy skill's iso-kit

const RADIANS = Math.PI / 180;
const UNIT = Math.sqrt(1.6);

export interface Projection {
	origin: [number, number];
	scale: number;
	azimuth?: number;
	elevation?: number;
}

export function cameraOf(proj: Projection) {
	const a = (proj.azimuth ?? 45) * RADIANS;
	const e = (proj.elevation ?? 30) * RADIANS;
	return {
		sinA: Math.sin(a),
		cosA: Math.cos(a),
		sinE: Math.sin(e),
		cosE: Math.cos(e),
		k: proj.scale * UNIT
	};
}

export function iso(p: [number, number, number], proj: Projection): [number, number] {
	const cam = cameraOf(proj);
	const [x, y, z] = p;
	return [
		proj.origin[0] + (x * cam.sinA - y * cam.cosA) * cam.k,
		proj.origin[1] + ((x * cam.cosA + y * cam.sinA) * cam.sinE - z * cam.cosE) * cam.k
	];
}

export function depthOf(p: [number, number, number], proj: Projection): number {
	const cam = cameraOf(proj);
	const [x, y, z] = p;
	return (x * cam.cosA + y * cam.sinA) * cam.cosE + z * cam.sinE;
}

export function pathOf(points: [number, number][], closed = false): string {
	if (!points.length) return '';
	return points.map(([x, y], at) => `${at ? 'L' : 'M'}${x.toFixed(1)} ${y.toFixed(1)}`).join('') + (closed ? 'Z' : '');
}

// Tone palette for anatomy style
export const TONES = {
	dark: { lo: '#1a1a2e', mid: '#2d2d44', hi: '#4a4a6a', lit: '#ffffff', faint: '#0f0f1a', bg: '#0a0a14' },
	light: { lo: '#d0d0d8', mid: '#b8b8c4', hi: '#9898a8', lit: '#1a1a2e', faint: '#e8e8f0', bg: '#f5f5fa' }
};

export function slab(
	x: number, y: number, w: number, d: number, h: number,
	proj: Projection, tone: 'lo' | 'mid' | 'hi' | 'lit' = 'mid',
	palette = TONES.dark
): string {
	// Top face
	const tl = iso([x, y, h], proj);
	const tr = iso([x + w, y, h], proj);
	const br = iso([x + w, y + d, h], proj);
	const bl = iso([x, y + d, h], proj);
	// Front face (y+d side)
	const fl = iso([x, y + d, 0], proj);
	const fr = iso([x + w, y + d, 0], proj);
	const ftl = iso([x, y + d, h], proj);
	const ftr = iso([x + w, y + d, h], proj);
	// Side face (x+w side)
	const sl = iso([x + w, y, 0], proj);
	const sr = iso([x + w, y + d, 0], proj);
	const stl = iso([x + w, y, h], proj);
	const str = iso([x + w, y + d, h], proj);

	const color = palette[tone];
	const sideColor = palette.lo;
	const frontColor = palette.mid;

	return `
		<polygon points="${tl[0]},${tl[1]} ${tr[0]},${tr[1]} ${br[0]},${br[1]} ${bl[0]},${bl[1]}" fill="${color}" />
		<polygon points="${ftl[0]},${ftl[1]} ${ftr[0]},${ftr[1]} ${fr[0]},${fr[1]} ${fl[0]},${fl[1]}" fill="${frontColor}" />
		<polygon points="${stl[0]},${stl[1]} ${str[0]},${str[1]} ${sr[0]},${sr[1]} ${sl[0]},${sl[1]}" fill="${sideColor}" />
	`;
}

export function cylinder(
	cx: number, cy: number, r: number, h: number,
	proj: Projection, tone: 'lo' | 'mid' | 'hi' | 'lit' = 'mid',
	palette = TONES.dark, segments = 12
): string {
	// Generate top ellipse and bottom ellipse
	const topPoints: [number, number][] = [];
	const botPoints: [number, number][] = [];
	for (let i = 0; i <= segments; i++) {
		const angle = (i / segments) * Math.PI * 2;
		const x = cx + r * Math.cos(angle);
		const y = cy + r * Math.sin(angle);
		topPoints.push(iso([x, y, h], proj));
		botPoints.push(iso([x, y, 0], proj));
	}
	const topPath = pathOf(topPoints, true);
	const botPath = pathOf(botPoints, true);

	// Side faces
	let sides = '';
	for (let i = 0; i < segments; i++) {
		const angle1 = (i / segments) * Math.PI * 2;
		const angle2 = ((i + 1) / segments) * Math.PI * 2;
		const x1 = cx + r * Math.cos(angle1);
		const y1 = cy + r * Math.sin(angle1);
		const x2 = cx + r * Math.cos(angle2);
		const y2 = cy + r * Math.sin(angle2);
		const tl = iso([x1, y1, h], proj);
		const tr = iso([x2, y2, h], proj);
		const bl = iso([x1, y1, 0], proj);
		const br = iso([x2, y2, 0], proj);
		sides += `<polygon points="${tl[0]},${tl[1]} ${tr[0]},${tr[1]} ${br[0]},${br[1]} ${bl[0]},${bl[1]}" fill="${palette.lo}" opacity="0.8" />`;
	}

	return `${sides}<path d="${botPath}" fill="${palette.lo}" /><path d="${topPath}" fill="${palette[tone]}" />`;
}

export function sphere(cx: number, cy: number, cz: number, r: number, proj: Projection, tone: 'lo' | 'mid' | 'hi' | 'lit' = 'lit', palette = TONES.dark, segments = 8): string {
	return cylinder(cx, cy, r, 0, proj, tone, palette, segments).replace(/z.*?0/g, (m) => m);
	// Simplified: just a circle in iso
}
