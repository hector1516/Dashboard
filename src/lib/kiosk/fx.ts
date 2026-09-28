/**
 * Confeti y partículas en canvas.
 *
 * Una sola capa de canvas para toda la pantalla (no un canvas por tarjeta):
 * a 1920×1080 y 24/7 en una TV, dibujar 6 canvases distintos es lo que hace
 * que estas máquinas se encasqueten. Todo en `transform`/`globalAlpha` y con un
 * tope duro de partículas; si el frame rate cae, el orquestador llama
 * `degradar(true)` y esto dibuja menos.
 */
export interface Particula {
	x: number;
	y: number;
	vx: number;
	vy: number;
	tam: number;
	color: string;
	rot: number;
	vrot: number;
	vida: number;
	forma: 'rect' | 'circulo' | 'cinta';
}

let canvas: HTMLCanvasElement | null = null;
let ctx: CanvasRenderingContext2D | null = null;
let raf = 0;
let particulas: Particula[] = [];
let modoLigero = false;
let ultima = 0;
let fps = 60;

/** Tope duro: 120 es suficiente para que se vea festivo sin comerse la CPU. */
const TOPE_PARTICULAS = 120;
const TOPE_LIGERO = 30;

const COLORES = ['#FF6B00', '#FFAE00', '#22C55E', '#3B82F6', '#EC4899', '#A855F7', '#F8FAFC'];

export function montarConfeti(el: HTMLCanvasElement) {
	canvas = el;
	ctx = el.getContext('2d');
	redimensionar();
	ultima = performance.now();
	if (!raf) bucle(ultima);
}

export function redimensionar() {
	if (!canvas) return;
	const dpr = Math.min(1.5, window.devicePixelRatio || 1); // tope: en TV 4K no
	canvas.width = Math.floor(canvas.clientWidth * dpr);
	canvas.height = Math.floor(canvas.clientHeight * dpr);
	if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

/** Modo ligero cuando la pantalla no da: menos partículas, misma festividad. */
export function degradar(v: boolean) {
	modoLigero = v;
}

export function fpsActual(): number {
	return Math.round(fps);
}

export function cuantasParticulas(): number {
	return particulas.length;
}

function bucle(t: number) {
	raf = requestAnimationFrame(bucle);
	if (!ctx || !canvas) return;
	const dt = Math.min(64, t - ultima) / 16.667; // en frames de 60fps
	ultima = t;
	if (dt > 0) fps = fps * 0.9 + (1000 / (dt * 16.667)) * 0.1;

	ctx.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight);
	const sigue: Particula[] = [];
	for (const p of particulas) {
		p.x += p.vx * dt;
		p.y += p.vy * dt;
		p.vy += 0.32 * dt; // gravedad
		p.vx *= 0.995;
		p.rot += p.vrot * dt;
		p.vida -= 0.006 * dt;
		if (p.vida <= 0 || p.y > canvas.clientHeight + 60) continue;

		ctx.save();
		ctx.globalAlpha = Math.max(0, Math.min(1, p.vida));
		ctx.translate(p.x, p.y);
		ctx.rotate(p.rot);
		ctx.fillStyle = p.color;
		if (p.forma === 'rect') ctx.fillRect(-p.tam / 2, -p.tam / 4, p.tam, p.tam / 2);
		else if (p.forma === 'circulo') {
			ctx.beginPath();
			ctx.arc(0, 0, p.tam / 2.4, 0, Math.PI * 2);
			ctx.fill();
		} else {
			ctx.fillRect(-p.tam / 2, -1.5, p.tam, 3); // cinta
		}
		ctx.restore();
		sigue.push(p);
	}
	particulas = sigue;
}

/** Ráfaga de confeti desde el centro-arriba. `cantidad` 0 = tope. */
export function lanzarConfeti(cantidad = 90) {
	if (!canvas) return;
	const tope = modoLigero ? TOPE_LIGERO : TOPE_PARTICULAS;
	const w = canvas.clientWidth;
	const n = Math.min(cantidad, tope);
	for (let i = 0; i < n; i++) {
		const desde = Math.random() * w * 0.7 + w * 0.15;
		particulas.push({
			x: desde,
			y: -20 - Math.random() * 120,
			vx: (Math.random() - 0.5) * 9,
			vy: 3 + Math.random() * 8,
			tam: modoLigero ? 9 : 8 + Math.random() * 10,
			color: COLORES[(Math.random() * COLORES.length) | 0],
			rot: Math.random() * Math.PI,
			vrot: (Math.random() - 0.5) * 0.35,
			vida: 1,
			forma: (['rect', 'circulo', 'cinta'] as const)[(Math.random() * 3) | 0]
		});
	}
	if (particulas.length > tope) particulas = particulas.slice(-tope);
}

/** Lluvia de dorados, para la corona del ganador de Legends. */
export function lanzarOro(cantidad = 70) {
	if (!canvas) return;
	lanzarConfeti(0);
	const tope = modoLigero ? TOPE_LIGERO : TOPE_PARTICULAS;
	for (let i = 0; i < Math.min(cantidad, tope); i++) {
		particulas.push({
			x: Math.random() * canvas.clientWidth,
			y: -20 - Math.random() * 200,
			vx: (Math.random() - 0.5) * 3,
			vy: 2 + Math.random() * 5,
			tam: 8 + Math.random() * 12,
			color: Math.random() > 0.4 ? '#FFD700' : '#FFAE00',
			rot: Math.random() * Math.PI,
			vrot: (Math.random() - 0.5) * 0.25,
			vida: 1,
			forma: Math.random() > 0.5 ? 'cinta' : 'circulo'
		});
	}
}

export function limpiarConfeti() {
	particulas = [];
}

export function pararConfeti() {
	if (raf) cancelAnimationFrame(raf);
	raf = 0;
	particulas = [];
	canvas = null;
	ctx = null;
}
