import { writable } from 'svelte/store';
import { mascotState } from './mascot';

// Estado de posición de Volt en pantalla
export const voltPosition = writable({ x: 0, y: 0 });

// Configuración del caminar
const CONFIG = {
	padX: 120,       // margen horizontal desde bordes
	padY: 120,       // margen vertical desde bordes
	topSafe: 90,     // evitar header
	bottomSafe: 100, // evitar footer
	speed: 120,      // px/s velocidad de caminata
	pauseMin: 4000,  // ms pausa mínima en destino
	pauseMax: 9000,  // ms pausa máxima en destino
	moveMin: 2000,   // ms duración mínima del trayecto
	moveMax: 4000,   // ms duración máxima del trayecto
};

let rafId: number | null = null;
let paused = false;
let currentPos = { x: 0, y: 0 };
let targetPos = { x: 0, y: 0 };
let moveStartTime = 0;
let moveDuration = 0;
let isMoving = false;
let pauseTimer: ReturnType<typeof setTimeout> | null = null;

function getBounds() {
	const w = window.innerWidth;
	const h = window.innerHeight;
	return {
		minX: CONFIG.padX,
		maxX: w - CONFIG.padX - 180,
		minY: CONFIG.topSafe,
		maxY: h - CONFIG.bottomSafe - 180,
	};
}

function pickTarget() {
	const b = getBounds();
	return {
		x: b.minX + Math.random() * (b.maxX - b.minX),
		y: b.minY + Math.random() * (b.maxY - b.minY),
	};
}

function easeInOut(t: number): number {
	return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
}

function startMove() {
	if (paused) return;
	targetPos = pickTarget();
	const dx = targetPos.x - currentPos.x;
	const dy = targetPos.y - currentPos.y;
	const dist = Math.sqrt(dx * dx + dy * dy);
	moveDuration = Math.max(CONFIG.moveMin, Math.min(CONFIG.moveMax, (dist / CONFIG.speed) * 1000));
	moveStartTime = performance.now();
	isMoving = true;
	mascotState.set('working');
}

function finishMove() {
	isMoving = false;
	currentPos = { ...targetPos };
	voltPosition.set(currentPos);
	mascotState.set('idle');
	// Pausa antes del siguiente movimiento
	const pause = CONFIG.pauseMin + Math.random() * (CONFIG.pauseMax - CONFIG.pauseMin);
	pauseTimer = setTimeout(() => {
		if (!paused) startMove();
	}, pause);
}

function tick(now: number) {
	if (paused) {
		rafId = requestAnimationFrame(tick);
		return;
	}
	if (isMoving) {
		const elapsed = now - moveStartTime;
		const t = Math.min(1, elapsed / moveDuration);
		const eased = easeInOut(t);
		currentPos.x = currentPos.x + (targetPos.x - currentPos.x) * eased * 0.15 + (targetPos.x - currentPos.x) * 0;
		// Recalcular posición interpolada correctamente
		const startX = currentPos.x - (targetPos.x - currentPos.x) * (1 - eased) / (1 - (eased - 0.15 * eased));
		// Simplificar: usar lerp directo
		const progress = eased;
		// Recalcular desde el inicio del movimiento
		// Necesitamos guardar la posición inicial
		// ...
		voltPosition.set({ x: currentPos.x, y: currentPos.y });
		if (t >= 1) {
			finishMove();
		}
	}
	rafId = requestAnimationFrame(tick);
}

// Guardar posición inicial del movimiento
let moveStartPos = { x: 0, y: 0 };

function startMoveV2() {
	if (paused) return;
	targetPos = pickTarget();
	moveStartPos = { ...currentPos };
	const dx = targetPos.x - currentPos.x;
	const dy = targetPos.y - currentPos.y;
	const dist = Math.sqrt(dx * dx + dy * dy);
	moveDuration = Math.max(CONFIG.moveMin, Math.min(CONFIG.moveMax, (dist / CONFIG.speed) * 1000));
	moveStartTime = performance.now();
	isMoving = true;
	mascotState.set('working');
}

function tickV2(now: number) {
	if (paused) {
		rafId = requestAnimationFrame(tickV2);
		return;
	}
	if (isMoving) {
		const elapsed = now - moveStartTime;
		const t = Math.min(1, elapsed / moveDuration);
		const eased = easeInOut(t);
		currentPos.x = moveStartPos.x + (targetPos.x - moveStartPos.x) * eased;
		currentPos.y = moveStartPos.y + (targetPos.y - moveStartPos.y) * eased;
		voltPosition.set({ x: currentPos.x, y: currentPos.y });
		if (t >= 1) {
			isMoving = false;
			currentPos = { ...targetPos };
			voltPosition.set(currentPos);
			mascotState.set('idle');
			const pause = CONFIG.pauseMin + Math.random() * (CONFIG.pauseMax - CONFIG.pauseMin);
			pauseTimer = setTimeout(() => {
				if (!paused) startMoveV2();
			}, pause);
		}
	}
	rafId = requestAnimationFrame(tickV2);
}

export function startWalking() {
	if (rafId !== null) return; // ya está corriendo
	paused = false;
	// Posición inicial: esquina inferior derecha
	const b = getBounds();
	currentPos = { x: b.maxX, y: b.maxY };
	voltPosition.set(currentPos);
	// Primer movimiento tras pausa inicial
	pauseTimer = setTimeout(() => {
		if (!paused) startMoveV2();
	}, 3000);
	rafId = requestAnimationFrame(tickV2);
}

export function stopWalking() {
	paused = true;
	if (pauseTimer) {
		clearTimeout(pauseTimer);
		pauseTimer = null;
	}
	if (rafId !== null) {
		cancelAnimationFrame(rafId);
		rafId = null;
	}
	mascotState.set('idle');
}

export function pauseWalking() {
	paused = true;
	if (pauseTimer) {
		clearTimeout(pauseTimer);
		pauseTimer = null;
	}
}

export function resumeWalking() {
	if (!paused) return;
	paused = false;
	if (rafId === null) {
		rafId = requestAnimationFrame(tickV2);
	}
	// Reanudar con nuevo movimiento tras pausa corta
	pauseTimer = setTimeout(() => {
		if (!paused && !isMoving) startMoveV2();
	}, 1000);
}

// Verificar preferencia de movimiento reducido
export function prefersReducedMotion(): boolean {
	return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}