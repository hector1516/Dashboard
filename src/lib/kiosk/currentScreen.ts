import { writable } from 'svelte/store';

// Pantalla actual del kiosco (id de la pantalla que se esta mostrando)
export const currentScreen = writable<string>('portada');

// Etiquetas legibles para cada pantalla
export const SCREEN_LABELS: Record<string, string> = {
	clima: 'Clima',
	asistencia: 'Asistencia',
	actividad: 'Actividad',
	equipo: 'Equipo',
	portada: 'Portada',
	uso_apps: 'Uso de Apps',
	sabias_que: 'Sabias Que',
	combustible: 'Combustible',
	legends: 'Legends',
	reportes: 'Reportes',
	tickets: 'Tickets',
	notas: 'Notas',
	celebraciones: 'Celebraciones',
	fotos: 'Fotos',
	metricas: 'Metricas',
	pulso: 'Pulso',
	ingenieria_campo: 'Ingenieria de Campo',
};