import { writable } from 'svelte/store';

// Estado de la mascota Volt en el kiosco
export const mascotState = writable<string>('idle');

// Helper para cambiar el estado
export function setMascotState(state: string) {
	mascotState.set(state);
}

// Estados disponibles: idle, thinking, listening, speaking, sleeping,
// working, error, surprised, celebrating, sad, happy