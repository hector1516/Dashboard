export const dinero = (n: number | null) =>
	n == null ? '—' : '$' + Number(n).toLocaleString('es-MX');

export const dias = (n: number) => (n === 1 ? '1 día' : `${n} días`);

export const colorEdad = (d: number): 'rojo' | 'ambar' | 'gris' =>
	d >= 7 ? 'rojo' : d >= 3 ? 'ambar' : 'gris';
