<script lang="ts">
	// Pantalla de combustible en la retícula bento.
	//
	// Siete celdas, una idea cada una. El ancla oscura 2×2 es el gasto del mes
	// (lo único que cuenta con `<Numero>`: spec §5.5) y a su lado se contestan
	// las seis preguntas del pasillo: cuánto falta por comprobar, cuánto saldo
	// queda, cómo va la semana, a qué hora cargan, a cuánto está el litro y
	// quién carga en cada gasolinera, y qué auto es el que más pide.
	//
	// RESERVA DE VOLT: la celda 3/4/4/5 (la esquina inferior derecha) NO se
	// usa. La maqueta ponía ahí «A qué hora cargan»; se movió a 2/4/3/5 y
	// «Gasto por semana» pasó a 2/3/3/4 para que ese hueco quede limpio. La
	// spec §3 lo pide explícito: el espacio de Volt se reserva en la retícula
	// (la última columna de la banda inferior), no se tapa con una celda.
	// Así las dos series quedan juntas en la fila de en medio, que además se
	// lee mejor que tenerlas separadas.
	//
	// Los datos salen del snapshot (`datos.combustible`), que el snapshotter
	// arma desde SQL cada 10 minutos. El bloque es OPCIONAL (snapshot viejo o
	// primer ciclo después de un deploy): todo se lee con `?.` y lo que no
	// viene se pinta «—» con su porqué, nunca un cero fingido.
	import Bento from '$lib/rediseno/Bento.svelte';
	import Celda from '$lib/rediseno/Celda.svelte';
	import Numero from '$lib/rediseno/Numero.svelte';
	import Marco from '$lib/rediseno/Marco.svelte';
	import '$lib/rediseno/tokens.css';
	import { dinero } from '$lib/rediseno/formato';
	import { relojKiosco } from '$lib/rediseno/relojKiosco.svelte';
	import { iniciales } from '$lib/kiosk/format';

	interface Semana {
		anio?: number;
		semana?: number;
		vales?: number;
		monto?: number;
	}
	interface Auto {
		id?: number;
		marca?: string;
		placas?: string;
		vales?: number;
		monto?: number;
		km?: number;
		costo_km?: number | null;
	}
	interface Estacion {
		estacion?: string;
		tickets?: number;
	}

	interface Props {
		/** Snapshot del kiosco. Solo se lee `combustible`. */
		datos?: any;
		/** Hora `HH:MM` ya formateada. Sin ella la toma del reloj. */
		reloj?: string;
		/** Fecha larga. Sin ella, la de hoy. */
		fecha?: string;
		/** «datos de hace 1 min». Sin ella, se calcula de `generado_en`. */
		antiguedad?: string;
		/** Posición en la rotación (`1/9`). Sin ella, un guion. */
		posicion?: string;
		/** Frase del pie. Sin ella, se arma del dato. */
		volt?: string;
	}
	let { datos, reloj, fecha, antiguedad, posicion, volt }: Props = $props();

	/** Un número del snapshot, o `null`. `0` es un dato; ausente no lo es. */
	function aNumero(v: any): number | null {
		if (v === null || v === undefined || v === '') return null;
		const n = Number(v);
		return Number.isFinite(n) ? n : null;
	}

	const c = $derived(datos?.combustible ?? null);
	// Sin bloque no se sabe nada: ni «todo al día» ni cero. Cada celda lo dice.
	const sinDatos = $derived(!c);
	const r = $derived(c?.resumen ?? null);

	// ── ancla: el mes ─────────────────────────────────────────────
	const gasto = $derived(aNumero(r?.gasto_mes));
	const variacion = $derived(aNumero(r?.variacion_pct));
	const valesMes = $derived(aNumero(r?.vales_mes));
	const promedio = $derived(aNumero(r?.promedio));

	// ── sin comprobante / saldo ───────────────────────────────────
	const sinCompMonto = $derived(aNumero(r?.sin_comprobante_monto));
	const sinCompN = $derived(aNumero(r?.sin_comprobante_n));
	/** `2026-11-23` → «23»: la ventana de «sin comprobante» es la temporada. */
	const desdeCorto = $derived.by(() => {
		const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(r?.sin_comprobante_desde ?? ''));
		return m ? String(Number(m[3])) : '';
	});
	const saldo = $derived(aNumero(r?.saldo));
	const alcanza = $derived(aNumero(r?.alcanza_vales));

	// ── series ────────────────────────────────────────────────────
	const semanas = $derived(
		(Array.isArray(c?.semanas) ? (c.semanas as Semana[]) : []).slice(-4)
	);
	const maxSemana = $derived(Math.max(1, ...semanas.map((s) => aNumero(s?.monto) ?? 0)));

	// Las 24 horas siempre son 24 barras: un hueco del snapshot es una barra
	// en cero, no una serie más corta.
	const horas = $derived(
		Array.from({ length: 24 }, (_, h) => {
			const v = Array.isArray(c?.horas) ? aNumero(c.horas[h]) : null;
			return v == null ? 0 : Math.max(0, v);
		})
	);
	const maxHora = $derived(Math.max(0, ...horas));
	const pico = $derived(maxHora > 0 ? horas.indexOf(maxHora) : null);

	// ── litro y gasolineras ───────────────────────────────────────
	const precioL = $derived(aNumero(c?.precio_l));
	const litros = $derived(aNumero(c?.litros));
	const estaciones = $derived(
		(Array.isArray(c?.estaciones) ? (c.estaciones as Estacion[]) : []).slice(0, 5)
	);
	const maxEst = $derived(
		Math.max(1, ...estaciones.map((e) => aNumero(e?.tickets) ?? 0))
	);

	// ── el auto top ───────────────────────────────────────────────
	// El rótulo manda: «el que más pide» es el que más VALES pide, no el que
	// más gasta. `datos.py` entrega `por_auto` ordenado por monto, y con la
	// mayoría de los vales sin monto emitido (19 de 23 el 2026-11-25) el que
	// más gasta puede no ser el que más pide. Se ordena aquí —desempate por
	// monto— sin tocar el backend ni el orden del snapshot, que otras
	// pantallas usan tal cual.
	const autos = $derived(Array.isArray(c?.por_auto) ? (c.por_auto as Auto[]) : []);
	const top = $derived(
		autos.length === 0
			? null
			: [...autos].sort(
					(a, b) =>
						(aNumero(b?.vales) ?? 0) - (aNumero(a?.vales) ?? 0) ||
						(aNumero(b?.monto) ?? 0) - (aNumero(a?.monto) ?? 0)
				)[0]
	);
	const foto = $derived(fotoAuto(top?.marca));

	/**
	 * Fotos locales de auto que sí existen en `static/autos` (mismo catálogo
	 * que `autoImageExists` de Admon). La pantalla vieja pedía
	 * `/autos/<slug>.webp` a secas: para «Honda City» ese archivo no está y el
	 * kiosco hacía un 404 en cada rotación. Aquí se pide solo un archivo que
	 * existe; si el modelo no tiene foto, quedan las iniciales (nunca un hueco
	 * blanco).
	 */
	const FOTOS_AUTO = [
		'honda-city-blanco',
		'honda-city-gris',
		'honda-civic',
		'honda-fit',
		'kia-rio-21',
		'lincoln-navigator-2003',
		'mg5',
		'nissan-np-300',
		'nissan-versa-acero',
		'nissan-versa-blanco',
		'nissan-versa-gris',
		'suzuki-swift'
	];
	function fotoAuto(marca: string | undefined): string | null {
		const slug = String(marca ?? '')
			.toLowerCase()
			.trim()
			.replace(/\s+/g, '-')
			.replace(/[^a-z0-9-]/g, '');
		if (!slug) return null;
		if (FOTOS_AUTO.includes(slug)) return `/autos/${slug}.webp`;
		// «Honda City» → «honda-city-blanco»: el archivo existe y es el mismo
		// modelo; no se inventa el dato, se elige la única foto disponible.
		const variante = FOTOS_AUTO.find((f) => f.startsWith(`${slug}-`));
		return variante ? `/autos/${variante}.webp` : null;
	}

	// ── texto ─────────────────────────────────────────────────────
	const miles = (n: number) => Math.round(n).toLocaleString('es-MX');
	const pesos = (n: number | null) => (n == null ? '—' : dinero(n));
	const precioTxt = (n: number | null) =>
		n == null
			? '—'
			: '$' + n.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
	const entero = (n: number) => Math.round(n).toLocaleString('es-MX');
	const conHora = (n: number) => `${Math.round(n)} h`;
	const variacionTxt = (n: number) => Math.abs(Number(n.toFixed(1))).toLocaleString('es-MX');

	/**
	 * La clase de tamaño de una cifra. En una celda de 446 px, «$124,209» a
	 * 96 px se sale de la tarjeta; sin esto el número se recorta en silencio.
	 */
	function escala(txt: string, comodo: number, largo: number): '' | 'md' | 'sm' {
		const n = txt.length;
		return n > largo ? 'sm' : n > comodo ? 'md' : '';
	}
	const escalaAncla = $derived(escala(miles(gasto ?? 0), 7, 8));
	const escalaSaldo = $derived(escala(pesos(saldo), 7, 9));
	const escalaSin = $derived(escala(pesos(sinCompMonto), 7, 9));

	/** `horas` son tickets por hora: el pico se dice como franja de dos horas. */
	const picoTxt = $derived(
		pico == null ? '' : pico >= 22 ? `pico a las ${pico} h` : `pico entre ${pico} y ${pico + 2}`
	);

	// ── reloj, fecha y antigüedad ─────────────────────────────────
	// El mismo módulo que usa Comprobantes: la prop manda y, si no viene, se
	// arma del navegador y de `datos.generado_en`.
	const k = relojKiosco(() => ({ reloj, fecha, antiguedad, generadoEn: datos?.generado_en }));

	const linea = $derived(volt ?? frase());
	function frase(): string {
		if (sinDatos) return 'El snapshot todavía no trae el tablero de combustible; no invento un cero.';
		if (sinCompN == null) return 'Sin el conteo de comprobantes no puedo decir cuánto falta por comprobar.';
		if (sinCompN > 0) return 'El gasto va bien; lo que se acumula son los comprobantes.';
		return `${pesos(gasto)} en ${entero(valesMes ?? 0)} vales y nada pendiente de comprobante.`;
	}
</script>

<Marco
	titulo="Combustible"
	reloj={k.hora}
	fecha={k.fecha}
	antiguedad={k.antiguedad}
	temperatura={datos?.clima?.actual?.temperatura}
	posicion={posicion ?? '—'}
	volt={linea}
	degradado={datos?.degradado ?? []}
>
	<Bento>
		<!-- Ancla 2×2: el gasto del mes con sus vales y el promedio. -->
		<Celda area="1/1/3/3" tono="dark" rotulo="Gasto del mes" i={0}>
			<div class="cuerpo centro">
				{#if gasto == null}
					<div class="cifra sin">—</div>
					<div class="sub">el snapshot no trae el gasto del mes</div>
				{:else}
					<div class="cifra ancla {escalaAncla}">
						<span class="cur">$</span><Numero valor={gasto} formato={miles} />
					</div>
					<div class="sub">
						{#if valesMes != null}
							<b>{entero(valesMes)} {valesMes === 1 ? 'vale' : 'vales'}</b>
							{#if promedio != null} · promedio <b>{pesos(promedio)}</b>{/if}
						{:else if promedio != null}
							promedio <b>{pesos(promedio)}</b>
						{:else}
							sin desglose de vales
						{/if}
					</div>
					{#if variacion != null}
						<div class="delta" class:sube={variacion > 0}>
							{variacion > 0 ? '▲' : '▼'} {variacionTxt(variacion)} % <span
								>vs mes anterior</span
							>
						</div>
					{:else}
						<div class="delta neutro"><span>sin mes anterior para comparar</span></div>
					{/if}
				{/if}
			</div>
		</Celda>

		<!-- Cifra 1×1: el dinero emitido que todavía no tiene foto de ticket. -->
		<Celda area="1/3/2/4" rotulo={desdeCorto ? `Sin comprobante · desde el ${desdeCorto}` : 'Sin comprobante'} i={1}>
			<div class="cuerpo">
				<div class="cifra {escalaSin}" class:sin={sinCompMonto == null}>
					{#if sinCompMonto == null}—{:else}{pesos(sinCompMonto)}{/if}
				</div>
				<div class="sub">
					<!-- Solo el conteo de la temporada. Los «sin monto» que traía
					     la maqueta son otra ventana (el mes) y otro concepto: juntos
					     se leían como si 19 cupieran en 6. -->
					{#if sinCompN == null}
						{sinDatos ? 'el snapshot no trae el bloque' : 'sin desglose del snapshot'}
					{:else}
						<b>{entero(sinCompN)} {sinCompN === 1 ? 'vale' : 'vales'}</b> sin comprobar
					{/if}
				</div>
			</div>
		</Celda>

		<!-- Cifra 1×1: el saldo de la tarjeta y para cuántos vales alcanza. -->
		<Celda area="1/4/2/5" rotulo="Saldo Go Vale" i={2}>
			<div class="cuerpo">
				<div class="cifra {escalaSaldo}" class:sin={saldo == null}>
					{#if saldo == null}—{:else}{pesos(saldo)}{/if}
				</div>
				<div class="sub">
					{#if saldo == null}
						{sinDatos ? 'el snapshot no trae el bloque' : 'sin saldo en el snapshot'}
					{:else if alcanza != null}
						alcanza <b>{entero(alcanza)} {alcanza === 1 ? 'vale' : 'vales'}</b>
					{:else}
						sin tope de vale
					{/if}
				</div>
			</div>
		</Celda>

		<!-- Serie 1×1: las cuatro semanas del periodo. -->
		<Celda area="2/3/3/4" rotulo="Gasto por semana" i={3}>
			<div class="cuerpo">
				{#if semanas.length === 0}
					<div class="sin-dato">
						<b>{sinDatos ? 'Sin datos todavía' : 'Sin vales'}</b>
						<span>
							{sinDatos ? 'El snapshot no trae el bloque.' : 'No hay vales en las últimas 4 semanas.'}
						</span>
					</div>
				{:else}
					<div class="barras">
						{#each semanas as s, k (k)}
							{@const monto = aNumero(s?.monto) ?? 0}
							<div class="bcol">
								<div class="bval">{pesos(monto)}</div>
								<div
									class="bbar"
									style="height:{monto > 0 ? Math.max(10, Math.round((monto / maxSemana) * 106)) : 6}px"
								></div>
								<div class="bpiso">sem {s?.semana ?? '—'}</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</Celda>

		<!-- Cifra 1×1 con su serie: cuántos cargan y a qué hora. -->
		<Celda area="2/4/3/5" rotulo="A qué hora cargan" i={4}>
			<div class="cuerpo">
				{#if pico == null}
					<div class="cifra sin">—</div>
					<div class="sub">
						{sinDatos ? 'el snapshot no trae el bloque' : 'sin tickets en 4 semanas'}
					</div>
				{:else}
					<div class="cifra">{conHora(maxHora)}</div>
					<div class="mini24" aria-hidden="true">
						{#each horas as v, h (h)}
							<i style="height:{Math.max(4, Math.round((v / maxHora) * 54))}px"></i>
						{/each}
					</div>
					<!-- `horas` son tickets por hora: la cifra es del pico, no una
					     duración. La franja lo dice sin ambigüedad. -->
					<div class="sub">{picoTxt}</div>
				{/if}
			</div>
		</Celda>

		<!-- Serie 2×1: el precio del litro y dónde se carga. -->
		<Celda area="3/1/4/3" rotulo="Precio del litro · dónde cargan" i={5}>
			<div class="cuerpo arriba">
				<div class="linea">
					<div class="cifra md" class:verde={precioL != null} class:sin={precioL == null}>
						{precioTxt(precioL)}
					</div>
					<div class="sub">
						{#if litros != null}
							por litro · <b>{entero(litros)} L</b> en 4 semanas
						{:else}
							por litro · sin litros facturados
						{/if}
					</div>
				</div>
				{#if estaciones.length === 0}
					<div class="sin-dato">
						<b>{sinDatos ? 'Sin datos todavía' : 'Sin gasolineras'}</b>
						<span>
							{sinDatos ? 'El snapshot no trae el bloque.' : 'No hay tickets en las últimas 4 semanas.'}
						</span>
					</div>
				{:else}
					<div class="estaciones">
						{#each estaciones as e, k (k)}
							{@const n = aNumero(e?.tickets) ?? 0}
							<div class="est-row">
								<b>{e?.estacion || 'Sin estación'}</b>
								<div class="est-pista" aria-hidden="true">
									<i style="width:{Math.max(4, Math.round((n / maxEst) * 100))}%"></i>
								</div>
								<span>{entero(n)}</span>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</Celda>

		<!-- Cifra 1×1 con foto: el auto que más pide. -->
		<Celda area="3/3/4/4" rotulo="Auto que más pide" i={6}>
			<div class="cuerpo">
				{#if !top}
					<div class="sin-dato">
						<b>{sinDatos ? 'Sin datos todavía' : 'Sin autos'}</b>
						<span>
							{sinDatos ? 'El snapshot no trae el bloque.' : 'No hay vales en las últimas 4 semanas.'}
						</span>
					</div>
				{:else}
					<div class="auto">
						<!-- La foto va encima de las iniciales: si el archivo no
						     está, `onerror` la quita y queda el respaldo. -->
						<div class="auto-foto" aria-hidden="true">
							<span>{iniciales(top.marca ?? '?')}</span>
							{#if foto}
								<img src={foto} alt="" onerror={(e) => (e.currentTarget as HTMLImageElement).remove()} />
							{/if}
						</div>
						<div class="datos">
							<b>{top.marca || 'Sin modelo'}</b>
							{#if top.placas}<span class="placa">{top.placas}</span>{/if}
							<span>
								{entero(aNumero(top.vales) ?? 0)} vales · {pesos(aNumero(top.monto))}
							</span>
						</div>
					</div>
					<div class="sub">
						{#if aNumero(top.km) != null && (aNumero(top.km) ?? 0) > 0}
							{entero(aNumero(top.km) ?? 0)} km{#if aNumero(top.costo_km) != null}{` · ${precioTxt(
									aNumero(top.costo_km)
								)} / km`}{/if}
						{:else}
							sin lecturas de odómetro en el periodo
						{/if}
					</div>
				{/if}
			</div>
		</Celda>

		<!-- 3/4/4/5 NO se usa: es el rincón de Volt (placa de 112 px + globo). -->
	</Bento>
</Marco>

<style>
	.cuerpo {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
		justify-content: flex-end;
		gap: 10px;
	}
	.cuerpo.centro {
		justify-content: center;
	}
	.cuerpo.arriba {
		justify-content: flex-start;
	}

	/* ── cifras ───────────────────────────────────────────────── */
	.cifra {
		font-size: var(--k-f-cifra);
		font-weight: 900;
		line-height: 0.92;
		letter-spacing: -4px;
		font-variant-numeric: tabular-nums;
		margin-bottom: 6px;
		white-space: nowrap;
	}
	.cifra.ancla {
		font-size: var(--k-f-ancla);
		letter-spacing: -10px;
	}
	/* Cifras largas: se encogen antes de recortarse. */
	.cifra.md {
		font-size: 76px;
		letter-spacing: -2.5px;
	}
	.cifra.sm {
		font-size: 58px;
		letter-spacing: -1.5px;
	}
	.cifra.ancla.md {
		font-size: 168px;
		letter-spacing: -8px;
	}
	.cifra.ancla.sm {
		font-size: 132px;
		letter-spacing: -6px;
	}
	.cur {
		font-size: 0.5em;
		vertical-align: 0.26em;
		margin-right: 6px;
		font-weight: 800;
		letter-spacing: 0;
	}
	/* Sin dato: un guion chico y apagado, no una barra negra de 96 px. */
	.cifra.sin {
		font-size: 64px;
		letter-spacing: 0;
		opacity: 0.28;
	}
	.verde {
		color: var(--k-verde);
	}

	.sub {
		font-size: 21px;
		font-weight: 600;
		opacity: 0.62;
	}
	.sub b {
		font-weight: 800;
		opacity: 1;
	}

	.delta {
		display: flex;
		align-items: center;
		gap: 10px;
		font-size: 20px;
		font-weight: 800;
		/* Gastar más no es una buena noticia: sube en rojo, baja en menta.
		   Solo se usa dentro del ancla oscura, así que el color es fijo. */
		color: #7fe3cf;
	}
	.delta.sube {
		color: #ff8f9f;
	}
	.delta.neutro {
		color: #f7f3ea;
	}
	.delta span {
		font-weight: 600;
		opacity: 0.6;
	}

	/* ── series ───────────────────────────────────────────────── */
	.barras {
		display: flex;
		align-items: flex-end;
		gap: 18px;
		height: 100%;
	}
	.bcol {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: flex-end;
		gap: 8px;
		height: 100%;
	}
	.bval {
		font-size: 20px;
		font-weight: 800;
	}
	.bbar {
		width: 100%;
		max-width: 78px;
		border-radius: 8px 8px 0 0;
		background: var(--k-verde);
	}
	.bpiso {
		font-size: 20px;
		font-weight: 700;
		opacity: 0.45;
	}

	.mini24 {
		display: flex;
		align-items: flex-end;
		gap: 3px;
		height: 54px;
	}
	.mini24 i {
		flex: 1;
		min-width: 0;
		background: var(--k-rojo);
		border-radius: 2px 2px 0 0;
		opacity: 0.9;
	}

	/* ── precio y gasolineras ─────────────────────────────────── */
	.linea {
		display: flex;
		align-items: baseline;
		gap: 14px;
		margin-bottom: 6px;
	}
	.linea .cifra {
		margin-bottom: 0;
	}
	.estaciones {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.est-row {
		display: flex;
		align-items: center;
		gap: 10px;
		font-size: 20px;
		line-height: 1.2;
	}
	.est-row b {
		flex: 1;
		min-width: 0;
		font-weight: 600;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.est-row span {
		font-weight: 900;
		font-variant-numeric: tabular-nums;
	}
	.est-pista {
		width: 90px;
		flex: 0 0 90px;
		height: 6px;
		border-radius: 3px;
		background: rgba(18, 20, 26, 0.08);
		overflow: hidden;
	}
	.est-pista i {
		display: block;
		height: 100%;
		background: var(--k-verde);
	}

	/* ── auto ─────────────────────────────────────────────────── */
	.auto {
		display: flex;
		align-items: center;
		gap: 16px;
	}
	.auto-foto {
		position: relative;
		width: 132px;
		height: 84px;
		flex: 0 0 132px;
		border-radius: 14px;
		background: #e6ddcd;
		color: #6d6455;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
		font-size: 28px;
		font-weight: 900;
		letter-spacing: 0.5px;
	}
	.auto-foto img {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
	.datos {
		display: flex;
		flex-direction: column;
		min-width: 0;
	}
	.datos b {
		font-size: 26px;
		font-weight: 800;
		letter-spacing: -0.4px;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.datos span {
		font-size: 20px;
		font-weight: 600;
		opacity: 0.6;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.datos .placa {
		font-weight: 800;
		opacity: 0.75;
		letter-spacing: 0.5px;
	}

	/* ── celda vacía ──────────────────────────────────────────── */
	.sin-dato {
		margin: auto 0;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.sin-dato b {
		font-size: 24px;
		font-weight: 800;
		opacity: 0.45;
	}
	.sin-dato span {
		font-size: 20px;
		font-weight: 600;
		opacity: 0.4;
	}
</style>
