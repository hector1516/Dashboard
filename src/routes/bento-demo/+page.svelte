<script lang="ts">
	// Banco de pruebas del sistema bento. NO es una pantalla de producción:
	// sirve para ver tokens, rejilla, celda y número sobre el escenario exacto
	// del kiosco.
	//
	//   /bento-demo                     → Combustible (maqueta aprobada)
	//   /bento-demo?p=comprobantes      → Comprobantes con los datos del snapshot
	//   /bento-demo?vacio=1             → Comprobantes sin pendientes ni vales
	//   /bento-demo?edades=1            → Comprobantes con los tres colores de edad
	//   /bento-demo?fotos=1             → Comprobantes con foto real y con foto rota
	//   /bento-demo?sinbloque=1         → snapshot viejo, sin bloque `pendientes`
	//   &volt=1                         → muestra la placa y el globo reales de Volt
	//                                     (por defecto se ocultan para capturar limpio)
	import { onMount } from 'svelte';
	import '$lib/rediseno/tokens.css';
	import Bento from '$lib/rediseno/Bento.svelte';
	import Celda from '$lib/rediseno/Celda.svelte';
	import Marco from '$lib/rediseno/Marco.svelte';
	import Numero from '$lib/rediseno/Numero.svelte';
	import Comprobantes from '$lib/components/pantallas/bento/Comprobantes.svelte';
	import { dinero } from '$lib/rediseno/formato';

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
	let edades = $state(false);
	let fotos = $state(false);
	let conVolt = $state(false);

	onMount(() => {
		const q = new URLSearchParams(location.search);
		vacio = q.get('vacio') === '1';
		edades = q.get('edades') === '1';
		fotos = q.get('fotos') === '1';
		// Snapshot viejo: aún no trae `pendientes`. No debe reventar ni fingir.
		sinBloque = q.get('sinbloque') === '1';
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

	// Valores de ejemplo tomados de la maqueta (datos del 2026-11-25).
	const semanas = [
		{ s: 45, v: 0 },
		{ s: 46, v: 0 },
		{ s: 47, v: 0 },
		{ s: 48, v: 2000 }
	];
	const estaciones: Array<[string, number]> = [
		['Aeropuerto Ramos SLW', 6],
		['Apasco SLW', 2],
		['Acapulco MTY', 2],
		['Libramiento 2 MTY', 1],
		['Las Quintas MTC', 1]
	];
	const horas = [0, 0, 0, 0, 0, 0, 1, 3, 9, 7, 5, 4, 6, 8, 5, 3, 2, 1, 0, 0, 0, 0, 0, 0];

	// El ancla lleva el signo de pesos aparte, más chico, como en la maqueta.
	const miles = (n: number) => Number(n).toLocaleString('es-MX');
	const conHora = (n: number) => `${n} h`;
</script>

<div class="stage">
	{#if pantalla === 'comprobantes'}
		<!-- La pantalla trae su propio marco: se monta con solo `datos`. -->
		<Comprobantes
			datos={sinBloque ? {} : edades ? EDADES : fotos ? FOTOS : vacio ? VACIO : REAL}
			reloj="12:29"
			fecha="miércoles 25 de noviembre"
			antiguedad="datos de hace 1 min"
			posicion="6/10"
		/>
	{:else}
		<Marco
			titulo="Prueba"
			reloj="12:29"
			fecha="miércoles 25 de noviembre"
			antiguedad="datos de hace 1 min"
			sinFoto={2}
			posicion="1/9"
			volt="El gasto va bien; lo que se acumula son los comprobantes."
		>
			<Bento>
				<Celda area="1/1/3/3" tono="dark" rotulo="Gasto del mes" i={0}>
					<div class="cuerpo centro">
						<div class="cifra ancla"><span class="cur">$</span><Numero valor={2000} formato={miles} /></div>
						<div class="sub oscuro"><b>23 vales</b> · promedio $500</div>
						<div class="delta down">▼ 12 % <span>vs mes anterior</span></div>
					</div>
				</Celda>

				<Celda area="1/3/2/4" rotulo="Sin comprobante" i={1}>
					<div class="cuerpo">
						<div class="cifra"><Numero valor={1000} formato={dinero} /></div>
						<div class="sub"><b>6 vales</b> · 3 sin monto</div>
					</div>
				</Celda>

				<Celda area="1/4/2/5" rotulo="Saldo Go Vale" i={2}>
					<div class="cuerpo">
						<div class="cifra"><Numero valor={4209} formato={dinero} /></div>
						<div class="sub">alcanza <b>8 vales</b></div>
					</div>
				</Celda>

				<Celda area="2/3/3/5" rotulo="Gasto por semana" i={3}>
					<div class="cuerpo">
						<div class="barras">
							{#each semanas as x}
								<div class="bcol">
									<div class="bval">{x.v ? dinero(x.v) : '$0'}</div>
									<div class="bbar" style="height:{x.v ? 120 : 6}px"></div>
									<div class="bpiso">sem {x.s}</div>
								</div>
							{/each}
						</div>
					</div>
				</Celda>

				<Celda area="3/1/4/3" rotulo="Precio del litro · dónde cargan" i={4}>
					<div class="cuerpo arriba">
						<div class="linea">
							<div class="cifra md verde">$21.29</div>
							<div class="sub">por litro · <b>874 L</b> en 4 semanas</div>
						</div>
						<div class="estaciones">
							{#each estaciones as [nombre, vales]}
								<div class="est-row">
									<b>{nombre}</b>
									<div class="est-pista"><i style="width:{(vales / 6) * 100}%"></i></div>
									<span>{vales}</span>
								</div>
							{/each}
						</div>
					</div>
				</Celda>

				<Celda area="3/3/4/4" rotulo="Auto que más pide" i={5}>
					<div class="cuerpo">
						<div class="auto">
							<img src="/autos/honda-city-blanco.webp" alt="Honda City" />
							<div class="datos"><b>Honda City</b><span>8 vales · $1,000</span></div>
						</div>
						<div class="sub">2,112 km · $0.47 / km</div>
					</div>
				</Celda>

				<Celda area="3/4/4/5" rotulo="A qué hora cargan" i={6}>
					<div class="cuerpo">
						<div class="cifra"><Numero valor={9} formato={conHora} /></div>
						<div class="mini24">
							{#each horas as v}
								<i style="height:{Math.max(4, (v / 9) * 58)}px"></i>
							{/each}
						</div>
						<div class="sub">pico entre 8 y 10</div>
					</div>
				</Celda>
			</Bento>
		</Marco>
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

	.cuerpo {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
		justify-content: flex-end;
		gap: 10px;
	}
	.cuerpo.centro { justify-content: center; }
	.cuerpo.arriba { justify-content: flex-start; }

	.cifra {
		font-size: var(--k-f-cifra);
		font-weight: 900;
		line-height: 0.92;
		letter-spacing: -4px;
		font-variant-numeric: tabular-nums;
		margin-bottom: 6px;
	}
	.cifra.ancla {
		font-size: var(--k-f-ancla);
		letter-spacing: -10px;
	}
	.cifra.md {
		font-size: 76px;
		letter-spacing: -2.5px;
		margin-bottom: 0;
	}
	.cur {
		font-size: 0.5em;
		vertical-align: 0.26em;
		margin-right: 6px;
		font-weight: 800;
		letter-spacing: 0;
	}
	.verde { color: var(--k-verde); }

	.sub {
		font-size: 21px;
		font-weight: 600;
		opacity: 0.62;
	}
	.sub b { font-weight: 800; opacity: 1; }
	.sub.oscuro { opacity: 0.8; }

	.delta {
		display: flex;
		align-items: center;
		gap: 10px;
		font-size: 20px;
		font-weight: 800;
	}
	.delta.down { color: #7fe3cf; }
	.delta span { font-weight: 600; opacity: 0.6; }

	/* serie de barras */
	.barras {
		display: flex;
		align-items: flex-end;
		gap: 28px;
		height: 100%;
	}
	.bcol {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: flex-end;
		gap: 8px;
		height: 100%;
	}
	.bval { font-size: 20px; font-weight: 800; }
	.bbar {
		width: 100%;
		max-width: 78px;
		border-radius: 8px 8px 0 0;
		background: var(--k-verde);
	}
	.bpiso { font-size: 20px; font-weight: 700; opacity: 0.45; }

	/* mini serie de 24 horas */
	.mini24 {
		display: flex;
		align-items: flex-end;
		gap: 3px;
		height: 58px;
	}
	.mini24 i {
		flex: 1;
		background: var(--k-rojo);
		border-radius: 2px 2px 0 0;
		opacity: 0.9;
	}

	/* lista de estaciones */
	.linea {
		display: flex;
		align-items: baseline;
		gap: 14px;
		margin-bottom: 6px;
	}
	.estaciones { display: flex; flex-direction: column; gap: 4px; }
	.est-row {
		display: flex;
		align-items: center;
		gap: 10px;
		font-size: 20px;
	}
	.est-row b {
		flex: 1;
		font-weight: 600;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.est-row span { font-weight: 900; font-variant-numeric: tabular-nums; }
	.est-pista {
		width: 90px;
		height: 6px;
		border-radius: 3px;
		background: rgba(18, 20, 26, 0.08);
		overflow: hidden;
	}
	.est-pista i { display: block; height: 100%; background: var(--k-verde); }

	/* auto */
	.auto { display: flex; align-items: center; gap: 16px; }
	.auto img {
		width: 132px;
		height: 84px;
		border-radius: 14px;
		object-fit: cover;
		background: #e6ddcd;
	}
	.auto .datos { display: flex; flex-direction: column; }
	.auto .datos b { font-size: 26px; font-weight: 800; letter-spacing: -0.4px; }
	.auto .datos span { font-size: 20px; font-weight: 600; opacity: 0.6; }
</style>
