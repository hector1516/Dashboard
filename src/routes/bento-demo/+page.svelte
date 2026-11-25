<script lang="ts">
	// Banco de pruebas del sistema bento. NO es una pantalla de producción:
	// sirve para ver las pantallas montadas sobre el escenario exacto del
	// kiosco, con datos de ejemplo tomados de la maqueta aprobada.
	//
	//   /bento-demo                     → Combustible (maqueta aprobada)
	//   /bento-demo?p=combustible       → lo mismo, explícito
	//   /bento-demo?sincombustible=1    → snapshot viejo: sin bloque `combustible`
	//   /bento-demo?grande=1            → cifras de seis dígitos y nombres largos
	//   /bento-demo?p=comprobantes      → Comprobantes con los datos del snapshot
	//   /bento-demo?vacio=1             → Comprobantes sin pendientes ni vales
	//   /bento-demo?edades=1            → Comprobantes con los tres colores de edad
	//   /bento-demo?fotos=1             → Comprobantes con foto real y con foto rota
	//   /bento-demo?sinbloque=1         → snapshot viejo, sin bloque `pendientes`
	//   &volt=1                         → muestra la placa y el globo reales de Volt
	//                                     (por defecto se ocultan para capturar limpio)
	import { onMount } from 'svelte';
	import '$lib/rediseno/tokens.css';
	import Comprobantes from '$lib/components/pantallas/bento/Comprobantes.svelte';
	import Combustible from '$lib/components/pantallas/bento/Combustible.svelte';

	// ── Combustible: los números de la maqueta (2026-11-25) ──────────
	// Misma forma que `datos.combustible` en el snapshot: `resumen`,
	// `semanas`, `por_auto`, `estaciones`, `horas`, `precio_l` y `litros`.
	// `variacion_pct` negativa = se gastó menos que el mes anterior.
	const COMBUSTIBLE = {
		combustible: {
			resumen: {
				gasto_mes: 2000,
				gasto_mes_anterior: 2273,
				variacion_pct: -12,
				vales_mes: 23,
				promedio: 500,
				vales_sin_monto: 3,
				sin_comprobante_n: 6,
				sin_comprobante_monto: 1000,
				sin_comprobante_desde: '2026-11-23',
				saldo: 4209,
				alcanza_vales: 8
			},
			semanas: [
				{ anio: 2026, semana: 45, vales: 6, monto: 0 },
				{ anio: 2026, semana: 46, vales: 7, monto: 0 },
				{ anio: 2026, semana: 47, vales: 8, monto: 0 },
				{ anio: 2026, semana: 48, vales: 2, monto: 2000 }
			],
			por_auto: [
				{
					id: 3,
					marca: 'Honda City',
					placas: 'RWS675B',
					vales: 8,
					monto: 1000,
					km: 2112,
					costo_km: 0.47,
					litros: null
				},
				{
					id: 7,
					marca: 'Nissan Versa',
					placas: 'RYL615A',
					vales: 6,
					monto: 0,
					km: 1840,
					costo_km: 0,
					litros: null
				}
			],
			estaciones: [
				{ estacion: 'Aeropuerto Ramos SLW', tickets: 6 },
				{ estacion: 'Apasco SLW', tickets: 2 },
				{ estacion: 'Acapulco MTY', tickets: 2 },
				{ estacion: 'Libramiento 2 MTY', tickets: 1 },
				{ estacion: 'Las Quintas MTC', tickets: 1 }
			],
			horas: [0, 0, 0, 0, 0, 0, 1, 3, 9, 7, 5, 4, 6, 8, 5, 3, 2, 1, 0, 0, 0, 0, 0, 0],
			precio_l: 21.29,
			litros: 874
		}
	};

	// ── Combustible: números grandes (para probar que nada se recorta) ──
	// Seis dígitos en el ancla, un modelo con nombre largo y más tickets por
	// estación: la cifra se encoge sola y los nombres se cortan con puntos.
	const GRANDE = {
		combustible: {
			...COMBUSTIBLE.combustible,
			resumen: {
				...COMBUSTIBLE.combustible.resumen,
				gasto_mes: 124500,
				gasto_mes_anterior: 98230,
				variacion_pct: 26.7,
				vales_mes: 249,
				promedio: 500,
				sin_comprobante_n: 12,
				sin_comprobante_monto: 6000,
				saldo: 84209,
				alcanza_vales: 168
			},
			por_auto: [
				{
					id: 9,
					marca: 'Nissan NP-300 Doble Cabina 2021',
					placas: 'TDX-777-B',
					vales: 148,
					monto: 74000,
					km: 21840,
					costo_km: 3.39
				}
			],
			estaciones: [
				{ estacion: 'Aeropuerto Internacional Ramos Arizpe SLW', tickets: 146 },
				{ estacion: 'Apasco SLW', tickets: 82 },
				{ estacion: 'Acapulco MTY', tickets: 42 },
				{ estacion: 'Libramiento 2 MTY', tickets: 21 },
				{ estacion: 'Las Quintas MTC', tickets: 11 }
			]
		}
	};

	// ── Comprobantes ────────────────────────────────────────────────
	// Datos reales del snapshot del 2026-11-25 (los mismos de la maqueta).
	// `monto: null` es un vale sin monto emitido: se pinta «sin monto», no $0.
	const REAL = {
		pendientes: {
			vales: 2,
			monto: 1000,
			desde: '2026-11-23',
			ultimos: [
				{ nombre: 'Alfredo Rendón', placa: 'RWS675B', monto: 500, dias: 0, cerrado: false },
				{ nombre: 'José Salazar', placa: 'RYL615A', monto: 500, dias: 1, cerrado: false },
				{ nombre: 'Ricardo Barajas', placa: 'SNE979', monto: 500, dias: 1, cerrado: true },
				{ nombre: 'José Salazar', placa: 'RYL615A', monto: 500, dias: 2, cerrado: true },
				{ nombre: 'Héctor Peña', placa: 'TDX-777-B', monto: null, dias: 3, cerrado: true },
				{ nombre: 'Ricardo Barajas', placa: 'SNE979', monto: null, dias: 5, cerrado: true }
			]
		}
	};

	// Caso «todo al día»: temporada recién arrancada, sin vales todavía.
	const VACIO = {
		pendientes: { vales: 0, monto: 0, desde: '2026-11-23', ultimos: [] as never[] }
	};

	// Caso de edades: 0-2 gris · 3-6 ámbar · 7+ rojo (el semáforo de la lista).
	const EDADES = {
		pendientes: {
			vales: 3,
			monto: 1000,
			desde: '2026-11-16',
			ultimos: [
				{ nombre: 'Alfredo Rendón', placa: 'RWS675B', monto: 500, dias: 9, cerrado: false },
				{ nombre: 'José Salazar', placa: 'RYL615A', monto: 500, dias: 4, cerrado: false },
				{ nombre: 'Ricardo Barajas', placa: 'SNE979', monto: null, dias: 0, cerrado: false },
				{ nombre: 'Héctor Peña', placa: 'TDX-777-B', monto: 500, dias: 2, cerrado: true }
			]
		}
	};

	// Fotos de persona: el snapshot las deja resueltas en `/media/usuarios/u<Id>.jpg`.
	// En el banco no hay `/media`, así que una fila lleva una imagen local que sí
	// existe y otra una ruta rota a propósito: se ven los dos caminos (foto e
	// iniciales de respaldo).
	const FOTOS = {
		pendientes: {
			...REAL.pendientes,
			ultimos: REAL.pendientes.ultimos.map((v, i) => ({
				...v,
				foto:
					i === 0
						? '/images/oficina-eccsa.webp'
						: i === 1
							? '/media/usuarios/no-existe.jpg'
							: null
			}))
		}
	};

	let pantalla = $state<'combustible' | 'comprobantes'>('combustible');
	let vacio = $state(false);
	let sinBloque = $state(false);
	let sinCombustible = $state(false);
	let grande = $state(false);
	let edades = $state(false);
	let fotos = $state(false);
	let conVolt = $state(false);

	onMount(() => {
		const q = new URLSearchParams(location.search);
		vacio = q.get('vacio') === '1';
		edades = q.get('edades') === '1';
		fotos = q.get('fotos') === '1';
		grande = q.get('grande') === '1';
		// Snapshots viejos: aún no traen `pendientes` ni `combustible`. No deben
		// reventar ni fingir un cero.
		sinBloque = q.get('sinbloque') === '1';
		sinCombustible = q.get('sincombustible') === '1';
		pantalla =
			vacio || edades || fotos || sinBloque || q.get('p') === 'comprobantes'
				? 'comprobantes'
				: 'combustible';
		// La placa y el globo de Volt viven en el layout: aquí solo se decide
		// si se ven. Con `?volt=1` se revisa que el rincón reservado no tape
		// ninguna celda.
		conVolt = q.get('volt') === '1';
		document.documentElement.classList.toggle('bento-con-volt', conVolt);
		return () => document.documentElement.classList.remove('bento-con-volt');
	});
</script>

<div class="stage">
	{#if pantalla === 'comprobantes'}
		<!-- Cada pantalla trae su propio marco: se monta con solo `datos`. -->
		<Comprobantes
			datos={sinBloque ? {} : edades ? EDADES : fotos ? FOTOS : vacio ? VACIO : REAL}
			reloj="12:29"
			fecha="miércoles 25 de noviembre"
			antiguedad="datos de hace 1 min"
			posicion="6/10"
		/>
	{:else}
		<Combustible
			datos={sinCombustible ? {} : grande ? GRANDE : COMBUSTIBLE}
			reloj="12:29"
			fecha="miércoles 25 de noviembre"
			antiguedad="datos de hace 1 min"
			posicion="1/9"
		/>
	{/if}
</div>

<style>
	/* El escenario fijo del kiosco: el marco y el tablero se miden dentro de
	   esta caja de 1920×1080 y nunca empujan scroll. */
	.stage {
		width: 1920px;
		height: 1080px;
		position: relative;
		z-index: 1;
		overflow: hidden;
	}

	/* Solo para el banco de pruebas: el dock fijo de Volt y su globo taparían
	   la celda de abajo a la derecha y ensuciarían las capturas del sistema.
	   En producción el rincón se RESERVA, no se tapa: para comprobarlo,
	   `?volt=1` los deja visibles y se mide que no pisen ninguna celda. */
	:global(html:not(.bento-con-volt) .volt-dock),
	:global(html:not(.bento-con-volt) .volt-comentario) {
		display: none !important;
	}
</style>
