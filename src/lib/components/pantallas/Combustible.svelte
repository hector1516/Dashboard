<!--
	⛽ Combustible — tablero completo de vales y costos.

	Diseño: la pared de una máquina expendedora japonesa. Cada indicador es una
	"ranura" con su franja de color, borde duro y sombra desplazada; los números
	son el producto. Volt vive en la cabecera, en el flujo (nunca encima de los
	datos), y la rejilla reserva su espacio.

	Los datos llegan del snapshot (`datos.combustible`), que arma el snapshotter
	desde SQL. El kiosco es de solo lectura.
-->
<script lang="ts">
	interface Props { datos: any }
	let { datos }: Props = $props();

	const c = $derived(datos?.combustible ?? null);
	const r = $derived(c?.resumen ?? {});
	const semanas = $derived(c?.semanas ?? []);
	const autos = $derived((c?.por_auto ?? []).slice(0, 6));
	const usuarios = $derived((c?.por_usuario ?? []).slice(0, 5));
	const estaciones = $derived(c?.estaciones ?? []);
	const clientes = $derived(c?.clientes ?? []);
	const horas = $derived(c?.horas ?? Array(24).fill(0));
	const tiempos = $derived(c?.tiempos ?? {});
	const calidad = $derived(c?.calidad ?? {});

	const precioL = $derived(c?.precio_l ?? null);
	const litrosC = $derived(c?.litros ?? null);
	const maxSemana = $derived(Math.max(1, ...semanas.map((s: any) => s.monto || 0)));
	const maxAuto = $derived(Math.max(1, ...autos.map((a: any) => a.monto || 0)));
	const maxUsuario = $derived(Math.max(1, ...usuarios.map((u: any) => u.vales || 0)));
	const maxHora = $derived(Math.max(1, ...horas));
	const maxCliente = $derived(Math.max(1, ...clientes.map((x: any) => x.tickets || 0)));

	const meses = ['enero','febrero','marzo','abril','mayo','junio','julio',
		'agosto','septiembre','octubre','noviembre','diciembre'];
	const hoy = new Date();
	const mesTxt = `${meses[hoy.getMonth()]} ${hoy.getFullYear()}`;

	const dinero = (n: any) =>
		n == null ? '—' : Number(n).toLocaleString('es-MX', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
	const decimal = (n: any, d = 1) =>
		n == null ? '—' : Number(n).toLocaleString('es-MX', { minimumFractionDigits: d, maximumFractionDigits: d });

	/** Imagen del auto: mismo nombre que usan Field/Admon (slug del modelo). */
	function slugAuto(marca: string): string {
		return String(marca || '').toLowerCase().trim()
			.replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
	}
	function sinFoto(e: Event) {
		(e.currentTarget as HTMLElement).style.display = 'none';
	}
</script>

<div class="maquina">
	<!-- Cabecera: marca, mes y Volt. Volt va EN EL FLUJO: reserva su espacio y
	     nunca puede taparse con un dato. -->
	<header class="cab">
		<div class="cab-izq">
			<span class="cab-logo">⛽</span>
			<div>
				<div class="cab-tit">Combustible</div>
				<div class="cab-sub">Vales · costos · consumo — {mesTxt}</div>
			</div>
		</div>
		<div class="cab-der">
			<div class="saldo">
				<span class="saldo-l">Saldo Go Vale</span>
				<span class="saldo-n">${dinero(r.saldo)}</span>
				<span class="saldo-s">{r.alcanza_vales != null ? `alcanza ${r.alcanza_vales} vales` : 'sin dato'}</span>
			</div>
			<div class="volt" title="Volt, el asistente de ECCSA">
				<svg viewBox="0 0 24 24" width="34" height="34" aria-hidden="true">
					<path d="M13 2 4 14h6l-1 8 9-12h-6l1-8z" fill="currentColor" />
				</svg>
				<span>Volt</span>
			</div>
		</div>
	</header>

	<!-- Franja de tiempos y cobertura: una línea, sin robar altura a las ranuras. -->
	<div class="tira">
		<span>Pedir → generar: <b>{decimal(tiempos.pedir_generar_min)} min</b></span>
		<span>Peor caso: <b>{tiempos.pedir_generar_peor_min ?? '—'} min</b></span>
		<span>Tickets con factura: <b>{calidad.tickets ? Math.round((calidad.tickets_con_vale / calidad.tickets) * 100) : 0} %</b></span>
		<span>Con foto: <b>{calidad.tickets ? Math.round((calidad.tickets_con_foto / calidad.tickets) * 100) : 0} %</b></span>
	<span class="tira-push">Sin comprobante: <b>{dinero(r.sin_comprobante_monto)}</b></span>
	</div>

	<main class="rejilla">
		<!-- Gasto del mes -->
		<section class="slot ancho-4 alto-2 rojo" style="--i:0">
			<div class="slot-hd">Gasto del mes</div>
			<div class="slot-bd">
				<div class="num gigante">${dinero(r.gasto_mes)}</div>
				<div class="comp">
					{#if r.variacion_pct != null}
						<span class:mas={r.variacion_pct > 0} class:menos={r.variacion_pct <= 0}>
							{r.variacion_pct > 0 ? '▲' : '▼'} {Math.abs(r.variacion_pct)} %
						</span>
						<span class="comp-l">vs mes anterior (${dinero(r.gasto_mes_anterior)})</span>
					{:else}
						<span class="comp-l">sin mes anterior para comparar</span>
					{/if}
				</div>
			</div>
		</section>

		<!-- Vales y promedio -->
		<section class="slot ancho-2 cobalt" style="--i:1">
			<div class="slot-hd">Vales</div>
			<div class="slot-bd">
				<div class="num">{dinero(r.vales_mes)}</div>
				<div class="pie">en el mes</div>
			</div>
		</section>

		<section class="slot ancho-2 amarillo" style="--i:2">
			<div class="slot-hd">Promedio</div>
			<div class="slot-bd">
				<div class="num">${dinero(r.promedio)}</div>
				<div class="pie">por vale <span class="mini">(tope $500)</span></div>
			</div>
		</section>

		<!-- Sin comprobante -->
		<section class="slot ancho-4 alto-2 tinta" style="--i:3">
			<div class="slot-hd alerta">Dinero sin comprobante</div>
			<div class="slot-bd">
				<div class="num gigante">${dinero(r.sin_comprobante_monto)}</div>
				<div class="pie">{r.sin_comprobante_n ?? 0} vale(s) emitidos sin foto del ticket</div>
				<div class="nota">Se cierra solo cuando el usuario sube la foto.</div>
			</div>
		</section>

		<!-- Semanas -->
		<section class="slot ancho-4 alto-2 verde" style="--i:4">
			<div class="slot-hd">Gasto por semana</div>
			<div class="slot-bd barras">
				{#each semanas as s (s.semana)}
					<div class="barra-col">
						<span class="barra-top">${dinero(s.monto)}</span>
						<div class="barra" style={`height:${Math.max(6, (s.monto / maxSemana) * 130)}px`}></div>
						<span class="barra-l">sem {s.semana}</span>
					</div>
				{/each}
				{#if !semanas.length}<div class="vacio">Sin vales en 4 semanas</div>{/if}
			</div>
		</section>

		<!-- Estaciones y precio del litro -->
		<section class="slot ancho-4 alto-2 menta" style="--i:5">
			<div class="slot-hd">Gasolineras y precio del litro</div>
			<div class="slot-bd">
				<div class="precio-global">
					<span class="pg-n">${decimal(precioL, 2)}</span>
					<span class="pg-l">por litro<br />{litrosC != null ? `${dinero(litrosC)} L en 4 semanas` : ''}</span>
				</div>
				<div class="sub-h" style="margin-top:6px">Dónde cargan más</div>
				{#each estaciones as e, i (e.estacion)}
					<div class="fila-precio">
						<span class="puesto">{i + 1}</span>
						<span class="est">{e.estacion}</span>
						<span class="cuenta">{e.tickets}</span>
					</div>
				{/each}
				{#if !estaciones.length}<div class="vacio">Sin tickets</div>{/if}
			</div>
		</section>

		<!-- Autos -->
		<section class="slot ancho-4 alto-2 amarillo" style="--i:6">
			<div class="slot-hd">Autos que más piden</div>
			<div class="slot-bd lista-autos">
				{#each autos as a (a.id)}
					<div class="auto">
						<div class="auto-foto">
							<img src={`/autos/${slugAuto(a.marca)}.webp`} alt={a.marca || ''} loading="lazy" onerror={sinFoto} />
							<span class="auto-ini">{(a.marca || '?').slice(0, 2)}</span>
						</div>
						<div class="auto-info">
							<div class="auto-nom">{a.marca || 'Sin modelo'}<span class="auto-pl">{[a.placas].filter(Boolean)}</span></div>
							<div class="auto-barra"><i style={`width:${Math.max(4, (a.monto / maxAuto) * 100)}%`}></i></div>
						</div>
						<div class="auto-cifras">
							<b>${dinero(a.monto)}</b>
							<span>{a.vales} vale(s){a.km ? ` · ${dinero(a.km)} km` : ''}{a.costo_km ? ` · $${decimal(a.costo_km, 2)}/km` : ''}</span>
						</div>
					</div>
				{/each}
				{#if !autos.length}<div class="vacio">Sin vales en 4 semanas</div>{/if}
			</div>
		</section>

		<!-- Usuarios -->
		<section class="slot ancho-3 cobalt" style="--i:7">
			<div class="slot-hd">Quién más pide</div>
			<div class="slot-bd">
				{#each usuarios as u, i (u.nombre)}
					<div class="fila">
						<span class="puesto">{i + 1}</span>
						<span class="quien">{u.nombre || '—'}</span>
						<span class="cuenta">{u.vales}</span>
					</div>
					<div class="mini-barra"><i style={`width:${(u.vales / maxUsuario) * 100}%`}></i></div>
				{/each}
				{#if !usuarios.length}<div class="vacio">Sin datos</div>{/if}
			</div>
		</section>

		<!-- Horas -->
		<section class="slot ancho-3 rojo" style="--i:8">
			<div class="slot-hd">A qué hora cargan</div>
			<div class="slot-bd">
				<div class="horas">
					{#each horas as n, h}
						<div class="hora" style={`height:${Math.max(4, (n / maxHora) * 96)}px`} title={`${h}:00`}></div>
					{/each}
				</div>
				<div class="pie">00 h ··· 23 h</div>
			</div>
		</section>

		<!-- Clientes -->
		<section class="slot ancho-3 menta" style="--i:9">
			<div class="slot-hd">Clientes más visitados</div>
			<div class="slot-bd">
				{#each clientes as cl (cl.cliente)}
					<div class="fila">
						<span class="quien">{cl.cliente || '—'}</span>
						<span class="cuenta">{cl.tickets}</span>
					</div>
					<div class="mini-barra"><i style={`width:${(cl.tickets / maxCliente) * 100}%`}></i></div>
				{/each}
				{#if !clientes.length}<div class="vacio">Sin tickets</div>{/if}
			</div>
		</section>

		<!-- Calidad -->
		<section class="slot ancho-3 tinta" style="--i:10">
			<div class="slot-hd">Calidad del registro</div>
			<div class="slot-bd calidad">
				<div class="cal-fila"><span>Sin código</span><b class:malo={calidad.sin_codigo > 0}>{calidad.sin_codigo ?? 0}</b></div>
				<div class="cal-fila"><span>Sin monto emitido</span><b class:malo={calidad.sin_monto > 0}>{calidad.sin_monto ?? 0}</b></div>
				<div class="cal-fila"><span>Monto distinto a $500</span><b class:malo={calidad.monto_raro > 0}>{calidad.monto_raro ?? 0}</b></div>
				<div class="cal-fila"><span>Tickets del periodo</span><b>{calidad.tickets ?? 0}</b></div>
			</div>
		</section>
	</main>
</div>

<style>
	.maquina {
		position: absolute; inset: 0;
		display: flex; flex-direction: column;
		padding: 26px 28px 24px;
		gap: 12px;
		background:
			radial-gradient(circle at 18% 12%, #faf5ec 0%, #f1e9db 55%, #ece2d1 100%);
		color: #141414;
		font-family: Outfit, system-ui, sans-serif;
		overflow: hidden;
	}

	/* ── Cabecera ─────────────────────────────────────────────────── */
	.cab {
		flex: 0 0 92px;
		display: flex; align-items: center; justify-content: space-between;
		padding: 0 22px;
		background: #e4002b; color: #fff;
		border: 2px solid #141414; border-radius: 18px;
		box-shadow: 6px 6px 0 #141414;
	}
	.cab-izq { display: flex; align-items: center; gap: 16px; }
	.cab-logo { font-size: 42px; line-height: 1; filter: grayscale(1) brightness(3); }
	.cab-tit { font-size: 40px; font-weight: 900; letter-spacing: -0.5px; line-height: 1; }
	.cab-sub { font-size: 15px; font-weight: 600; opacity: 0.9; margin-top: 4px; }
	.cab-der { display: flex; align-items: center; gap: 18px; }

	.saldo {
		display: flex; flex-direction: column; align-items: flex-end;
		background: #fffdf8; color: #141414;
		border: 2px solid #141414; border-radius: 12px;
		padding: 6px 14px; min-width: 190px;
	}
	.saldo-l { font-size: 11px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; opacity: 0.6; }
	.saldo-n { font-size: 26px; font-weight: 900; line-height: 1.05; font-variant-numeric: tabular-nums; }
	.saldo-s { font-size: 11px; font-weight: 600; opacity: 0.65; }

	/* Volt: en el flujo, con su propio espacio. Nunca se superpone. */
	.volt {
		display: flex; flex-direction: column; align-items: center; justify-content: center;
		width: 78px; height: 78px; flex: 0 0 78px;
		background: #ffc400; color: #141414;
		border: 2px solid #141414; border-radius: 50%;
		box-shadow: 4px 4px 0 #141414;
	}
	.volt span { font-size: 11px; font-weight: 800; letter-spacing: 0.5px; margin-top: -2px; }

	/* ── Tira de tiempos ──────────────────────────────────────────── */
	.tira {
		flex: 0 0 36px;
		display: flex; align-items: center; gap: 26px;
		padding: 0 16px;
		font-size: 14px; font-weight: 600;
		background: #fffdf8; border: 2px solid #141414; border-radius: 12px;
	}
	.tira b { font-weight: 900; }
	.tira-push { margin-left: auto; color: #b00020; }

	/* ── Rejilla de ranuras ───────────────────────────────────────── */
	.rejilla {
		flex: 1; min-height: 0;
		display: grid;
		grid-template-columns: repeat(12, 1fr);
		grid-auto-rows: 1fr;
		gap: 14px;
	}
	.ancho-2 { grid-column: span 2; }
	.ancho-3 { grid-column: span 3; }
	.ancho-4 { grid-column: span 4; }
	.alto-2 { grid-row: span 2; }

	.slot {
		display: flex; flex-direction: column;
		background: #fffdf8;
		border: 2px solid #141414; border-radius: 16px;
		box-shadow: 5px 5px 0 #141414;
		overflow: hidden;
		animation: caer 0.5s cubic-bezier(.2,.9,.3,1.2) both;
		animation-delay: calc(var(--i) * 40ms);
	}
	@keyframes caer {
		from { opacity: 0; transform: translateY(-16px) scale(.97); }
		to   { opacity: 1; transform: none; }
	}
	@media (prefers-reduced-motion: reduce) {
		.slot { animation: none; }
	}

	.slot-hd {
		flex: 0 0 34px;
		display: flex; align-items: center;
		padding: 0 14px;
		font-size: 12.5px; font-weight: 800;
		letter-spacing: 1.4px; text-transform: uppercase;
		color: #fff; background: #141414;
	}
	.rojo .slot-hd { background: #e4002b; }
	.cobalt .slot-hd { background: #1b3fa0; }
	.amarillo .slot-hd { background: #ffc400; color: #141414; }
	.verde .slot-hd { background: #007a4d; }
	.menta .slot-hd { background: #00a88e; }
	.tinta .slot-hd { background: #141414; }
	.slot-hd.alerta { background: #b00020; }

	.slot-bd {
		flex: 1; min-height: 0;
		padding: 10px 14px 12px;
		display: flex; flex-direction: column; justify-content: center;
		gap: 4px;
	}

	.num { font-size: 46px; font-weight: 900; line-height: 1; font-variant-numeric: tabular-nums; letter-spacing: -1px; }
	.num.gigante { font-size: 74px; }
	.pie { font-size: 13px; font-weight: 600; color: #555; }
	.mini { font-weight: 500; opacity: .7; }
	.nota { font-size: 11.5px; color: #777; margin-top: 2px; }
	.comp { display: flex; align-items: baseline; gap: 8px; font-size: 15px; font-weight: 800; }
	.comp .mas { color: #b00020; }
	.comp .menos { color: #007a4d; }
	.comp-l { font-size: 12.5px; font-weight: 600; color: #666; }
	.vacio { font-size: 13px; color: #888; font-weight: 600; }

	/* Barras por semana */
	.barras { flex-direction: row; align-items: flex-end; justify-content: space-around; gap: 10px; }
	.barra-col { display: flex; flex-direction: column; align-items: center; gap: 4px; }
	.barra-top { font-size: 12px; font-weight: 800; }
	.barra { width: 44px; background: #007a4d; border: 2px solid #141414; border-radius: 6px 6px 0 0; }
	.barra-l { font-size: 11px; font-weight: 700; color: #666; }

	/* Precio global del litro */
	.precio-global { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
	.pg-n { font-size: 40px; font-weight: 900; color: #00a88e; line-height: 1; font-variant-numeric: tabular-nums; }
	.pg-l { font-size: 11.5px; font-weight: 700; color: #555; line-height: 1.25; }

	/* Precios */
	.dos-col { flex-direction: row; gap: 16px; }
	.dos-col > div { flex: 1; min-width: 0; }
	.sub-h { font-size: 11px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; color: #666; margin-bottom: 4px; }
	.fila-precio { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; padding: 2.5px 0; border-bottom: 1px dashed #ddd; }
	.est { font-size: 12px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.precio { font-size: 14px; font-weight: 900; font-variant-numeric: tabular-nums; }
	.bien { color: #007a4d; }
	.mal { color: #b00020; }

	/* Autos */
	.lista-autos { gap: 6px; }
	.auto { display: flex; align-items: center; gap: 10px; }
	.auto-foto {
		position: relative; width: 62px; height: 40px; flex: 0 0 62px;
		background: #f1e9db; border: 2px solid #141414; border-radius: 8px; overflow: hidden;
	}
	.auto-foto img { width: 100%; height: 100%; object-fit: cover; }
	.auto-ini {
		position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
		font-size: 14px; font-weight: 900; color: #b9ab93; text-transform: uppercase;
	}
	.auto-foto img:not([style*="none"]) + .auto-ini { display: none; }
	.auto-info { flex: 1; min-width: 0; }
	.auto-nom { font-size: 12.5px; font-weight: 800; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.auto-pl { font-weight: 600; color: #777; margin-left: 6px; }
	.auto-barra { height: 9px; background: #efe6d6; border: 1.5px solid #141414; border-radius: 5px; overflow: hidden; margin-top: 3px; }
	.auto-barra i { display: block; height: 100%; background: #ffc400; }
	.auto-cifras { text-align: right; flex: 0 0 auto; }
	.auto-cifras b { display: block; font-size: 14px; font-weight: 900; font-variant-numeric: tabular-nums; }
	.auto-cifras span { font-size: 10.5px; font-weight: 600; color: #666; white-space: nowrap; }

	/* Listas (usuarios y clientes) */
	.fila { display: flex; align-items: baseline; gap: 8px; font-size: 13px; }
	.puesto { font-size: 10px; font-weight: 900; color: #999; width: 14px; }
	.quien { flex: 1; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.cuenta { font-weight: 900; font-variant-numeric: tabular-nums; }
	.mini-barra { height: 6px; background: #efe6d6; border-radius: 4px; overflow: hidden; margin: 0 0 6px 22px; }
	.cobalt .mini-barra i { background: #1b3fa0; }
	.menta .mini-barra i { background: #00a88e; }
	.mini-barra i { display: block; height: 100%; }

	/* Horas */
	.horas { display: flex; align-items: flex-end; gap: 3px; height: 96px; }
	.hora { flex: 1; background: #e4002b; border-radius: 2px 2px 0 0; min-width: 0; }

	/* Calidad */
	.calidad { gap: 8px; }
	.cal-fila { display: flex; justify-content: space-between; align-items: baseline; font-size: 13px; border-bottom: 1px dashed #ddd; padding-bottom: 5px; }
	.cal-fila b { font-size: 18px; font-weight: 900; }
	.cal-fila .malo { color: #b00020; }
</style>
