import { writable } from 'svelte/store';

/**
 * Buzón corto de Volt. Cualquier módulo puede dejar aquí una frase para que el
 * globo la diga; el globo es un extra de una línea, no un aviso de pantalla.
 */
export const voltAviso = writable<{ texto: string; reaccion?: string } | null>(null);

export function decirVolt(texto: string, reaccion = '💬') {
	voltAviso.set({ texto, reaccion });
}
