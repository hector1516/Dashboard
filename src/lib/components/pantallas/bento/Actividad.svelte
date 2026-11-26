<script lang="ts">
	// Actividad, en la retícula bento: qué se movió, quién lo movió y a qué hora.
	//
	// Cuatro celdas: el ancla dice cuántos reportes van en la semana (un número
	// estable y verdadero); la línea de contexto baja a la última hora
	// (`actividad_hora`: reportes + km + tickets) y a la última lectura de km.
	// La lista nombra los cinco reportes más recientes; las barras muestran en
	// qué días de la semana se mueve la oficina; y la cifra chica es quien más
	// reportes lleva de la semana.
	//
	// CELDA DE VOLT: la 3/4/4/5 (la esquina inferior derecha) la ocupa
	// `<CeldaVolt />` con las últimas tres notificaciones. Es una celda más de
	// la retícula; ya no hay personaje flotante que reservar.
	//
	// DESVÍOS DEL BRIEF, por el dato y no por gusto:
	//   · El ancla no es «acciones de hoy»: el snapshot no publica el acumulado
	//     del día. Lleva `reportes.esta_semana` (COUNT desde el domingo) y la
	//     última hora (`actividad_hora`, que es COUNT de la ÚLTIMA HORA, no del
	//     día) baja a la línea de contexto, con su nombre.
	//   · Las barras no son «por app»: el snapshot no trae un conteo por
	//     aplicación. Lo que sí trae es `pulso` (eventos por día de la semana
	//     y hora, últimos 14 días), y de ahí salen las barras por día. La
	//     etiqueta dice «dos semanas», que es la ventana real.
	//   `cotizaciones_lista` no tiene celda (las cuatro piezas ya llenan las
	//   once de la retícula): va en la frase de Volt, que es donde el pasillo
	//   lee lo que no cabe arriba.
	//
	// Los datos salen del snapshot. Si todavía es el vacío del arranque
	// (`degradado: ['cargando']`) no se pinta un cero: se dice que no hay
	// dato. Un cero de verdad (nadie registró nada en la última hora) sí se
	// pinta.
	import Bento from '$lib/rediseno/Bento.svelte';
	import Celda from '$lib/rediseno/Celda.svelte';
	import CeldaVolt from '$lib/rediseno/CeldaVolt.svelte';
	import Numero from '$lib/rediseno/Numero.svelte';
	import Marco from '$lib/rediseno/Marco.svelte';
	import '$lib/rediseno/tokens.css';
	import { relojKiosco } from '$lib/rediseno/relojKiosco.svelte';
	import { nombreMes } from '$lib/kiosk/format';

	interface Reporte {
		Folio?: string;
		Cliente?: string;
		ingeniero?: string;
		fecha?: string;
		Estatus?: string;
	}
	interface Pulso {
		dia?: number;
		hora?: number;
		valor?: number;
	}
	interface Top {
		nombre?: string;
		valor?: number;
		unidad?: string;
	}

	interface Props {
		/** Snapshot del kiosco. Solo se leen `metricas`, `reportes` y `cotizaciones_lista`. */
		datos?: any;
		/** Hora `HH:MM` ya formateada. Sin ella la toma del reloj. */
		reloj?: string;
		/** Fecha larga. Sin ella, la de hoy. */
		fecha?: string;
		/** «datos de hace 1 min». Sin ella, se calcula de `generado_en`. */
		antiguedad?: string;
		/** Posición en la rotación (`6/10`). Sin ella, un guion. */
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

	const m = $derived(datos?.metricas ?? null);
	// El snapshot vacío del arranque trae `degradado: ['cargando']` y métricas
	// en cero. Eso NO es «no pasó nada»: es «todavía no hay dato».
	const cargando = $derived((datos?.degradado ?? []).includes('cargando'));
	const sinDatos = $derived(!m || cargando);

	/** Acciones en la última hora (reportes + km + tickets). */
	const accionHora = $derived(sinDatos ? null : aNumero(m?.actividad_hora));

	/** Reportes de la semana en curso (es el número del ancla). */
	const reportesSemana = $derived(
		sinDatos ? null : aNumero(datos?.reportes?.esta_semana)
	);

	const reportes = $derived(
		(sinDatos || !Array.isArray(datos?.reportes?.ultimos)
			? []
			: (datos.reportes.ultimos as Reporte[])
		)
			.filter(Boolean)
			.slice(0, 5)
	);

	/** Quien más reportes lleva de la semana (el backend lo llama «del día»). */
	const top = $derived(!sinDatos && m?.top_del_dia ? (m.top_del_dia as Top) : null);
	const topValor = $derived(top ? aNumero(top.valor) : null);
	/** El rótulo usa la unidad que publica el snapshot, no una palabra fija. */
	const unidadTop = $derived(String(top?.unidad ?? '').trim());

	// ── pulso: eventos por día de la semana, últimos 14 días ────────
	const DIAS = ['DOM', 'LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SÁB'];
	const DIAS_LARGO = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'];
	const pulso = $derived(
		sinDatos || !Array.isArray(m?.pulso) ? [] : (m.pulso as Pulso[]).filter(Boolean)
	);
	/**
	 * `dia` viene de SQL con `DATEPART(weekday) - 1`: 0 = domingo (la semana de
	 * ECCSA arranca en domingo, ver `domingo_de_hoy`). Se suma por día; la
	 * ventana son 14 días, así que cada barra son dos días iguales, no uno.
	 */
	const porDia = $derived(
		Array.from({ length: 7 }, (_, d) =>
			pulso.reduce((s, p) => (Number(p?.dia) === d ? s + (aNumero(p?.valor) ?? 0) : s), 0)
		)
	);
	const totalPulso = $derived(porDia.reduce((a, b) => a + b, 0));
	const maxDia = $derived(Math.max(0, ...porDia));
	const diaPico = $derived(maxDia > 0 ? porDia.indexOf(maxDia) : null);

	const entero = (n: number) => String(Math.round(n));

	/** `2026-11-24·10:37` → `{ dia: '24', mes: 'nov', hora: '10:37' }`. Se
	 *  arma a mano: `new Date('2026-11-24')` es UTC y de noche cambiaría de
	 *  día; además el snapshot ya viene en hora local del servidor. */
	function partes(iso: unknown): { dia: string; mes: string; hora: string } | null {
		const g = /^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2}))?/.exec(String(iso ?? ''));
		if (!g) return null;
		const mes = Number(g[2]);
		if (!(mes >= 1 && mes <= 12)) return null;
		return {
			dia: String(Number(g[3])),
			mes: nombreMes(new Date(2026, mes - 1, 1)).slice(0, 3).toLowerCase(),
			hora: g[4] && g[5] ? `${g[4]}:${g[5]}` : ''
		};
	}

	function fechaDe(iso: unknown): string {
		const p = partes(iso);
		return p ? `${p.dia} ${p.mes}` : '';
	}

	/** «Ricardo Barajas · 24 nov». Se arma en una sola cadena: si el
	 *  separador va en el HTML, Svelte se come el espacio de antes del «·». */
	function metaReporte(r: Reporte): string {
		const quien = String(r?.ingeniero ?? '').trim() || 'Sin ingeniero';
		const cuando = fechaDe(r?.fecha);
		return cuando ? `${quien} · ${cuando}` : quien;
	}

	/**
	 * La última lectura de kilómetros. `texto` viene como «Nombre · Modelo ·
	 * lectura 129,757 km»; se queda el nombre (es lo que se lee de un vistazo)
	 * y la fecha del registro. Es la lectura de km, no «la última actividad»:
	 * un ticket o un reporte pueden ser más recientes y la línea no lo niega
	 * porque lo dice.
	 */
	const ultimaLectura = $derived.by(() => {
		const u = m?.ultimo_evento;
		if (!u) return null;
		const texto = String(u.texto ?? '').trim();
		const quien = texto.split('·')[0]?.trim() ?? '';
		const p = partes(u.meta);
		if (!quien && !p) return null;
		const cuando = p ? `${p.dia} ${p.mes}${p.hora ? ` · ${p.hora}` : ''}` : '';
		return { detalle: [quien, cuando].filter(Boolean).join(' · ') };
	});

	/** «Firmado» en verde, «Borrador» en ámbar; el resto, apagado. */
	function estadoDe(e: unknown): { texto: string; clase: string } {
		const t = String(e ?? '').trim();
		const s = t.toLowerCase();
		if (s === 'firmado') return { texto: `✓ ${t}`, clase: 'ok' };
		if (s === 'borrador') return { texto: t, clase: 'medio' };
		return { texto: t, clase: '' };
	}

	// Reloj, fecha y antigüedad: el mismo módulo en todas las pantallas bento.
	const k = relojKiosco(() => ({ reloj, fecha, antiguedad, generadoEn: datos?.generado_en }));

	const cotis = $derived(aNumero(datos?.cotizaciones_lista?.total));

	const linea = $derived(volt ?? frase());
	function frase(): string {
		if (sinDatos) {
			return 'El snapshot todavía no trae la actividad; no invento un cero.';
		}
		const semana =
			reportesSemana == null
				? 'el snapshot no trae los reportes de la semana'
				: `${reportesSemana} ${reportesSemana === 1 ? 'reporte' : 'reportes'} esta semana`;
		const factura =
			cotis == null
				? ''
				: cotis === 0
					? ' y las cotizaciones están al día'
					: ` y ${cotis} ${cotis === 1 ? 'cotización espera' : 'cotizaciones esperan'} factura`;
		return mayus(semana) + factura + '.';
	}
	function mayus(s: string): string {
		return s.charAt(0).toUpperCase() + s.slice(1);
	}
</script>

<Marco
	titulo="Actividad"
	reloj={k.hora}
	fecha={k.fecha}
	antiguedad={k.antiguedad}
	temperatura={datos?.clima?.actual?.temperatura}
	posicion={posicion ?? '—'}
	volt={linea}
	degradado={datos?.degradado ?? []}
>
	<Bento>
		<!-- Ancla 2×2: los reportes de la semana y el pulso de la última hora. -->
		<Celda area="1/1/3/3" tono="dark" rotulo="Reportes esta semana" i={0} fondo>
			<div class="cuerpo centro">
				{#if reportesSemana == null}
					<div class="cifra sin sobre-tinta">—</div>
					<div class="sub">
						{sinDatos
							? 'sin datos del snapshot'
							: 'el snapshot no trae los reportes de la semana'}
					</div>
				{:else}
					<div class="cifra ancla"><Numero valor={reportesSemana} formato={entero} /></div>
					<div class="sub">desde el domingo</div>
					<div class="delta">
						{#if accionHora == null}
							sin dato de la última hora
						{:else}
							{accionHora} {accionHora === 1 ? 'acción' : 'acciones'} en la última hora
						{/if}
					</div>
					{#if ultimaLectura}
						<div class="nota">última lectura de km: {ultimaLectura.detalle}</div>
					{/if}
				{/if}
			</div>
		</Celda>

		<!-- Lista 2×2: los cinco reportes más recientes. -->
		<Celda area="1/3/3/5" rotulo="Últimos reportes" i={1}>
			<div class="lista">
				{#if reportes.length === 0}
					<div class="sin-filas">
						<b>{sinDatos ? 'Sin datos todavía' : 'Sin reportes'}</b>
						<span>
							{sinDatos
								? 'El snapshot no trae las métricas.'
								: 'La lista se llena con los reportes más recientes.'}
						</span>
					</div>
				{:else}
					{#each reportes as r, i (r?.Folio ?? i)}
						{@const est = estadoDe(r?.Estatus)}
						<div class="fila">
							<div class="fol">{r?.Folio || '—'}</div>
							<div class="quien">
								<b>{r?.Cliente || 'Sin cliente'}</b>
								<span>{metaReporte(r)}</span>
							</div>
							{#if est.texto}
								<div class="estado {est.clase}">{est.texto}</div>
							{/if}
						</div>
					{/each}
				{/if}
			</div>
		</Celda>

		<!-- Serie 2×1: en qué días de las últimas dos semanas hubo movimiento. -->
		<Celda area="3/1/4/3" rotulo="Qué días hay movimiento" i={2}>
			<div class="cuerpo">
				{#if totalPulso === 0}
					<div class="sin-dato">
						<b>{sinDatos ? 'Sin datos todavía' : 'Sin movimiento'}</b>
						<span>
							{sinDatos
								? 'El snapshot no trae el bloque de métricas.'
								: 'Ni reportes, ni kilómetros, ni tickets en dos semanas.'}
						</span>
					</div>
				{:else}
					<div class="dias" aria-hidden="true">
						{#each porDia as v, d (d)}
							<div class="dcol">
								<div class="dval">{v}</div>
								<div
									class="dbar"
									class:pico={d === diaPico}
									style="height:{v > 0 ? Math.max(8, Math.round((v / maxDia) * 90)) : 6}px"
								></div>
								<div class="dpiso" class:pico={d === diaPico}>{DIAS[d]}</div>
							</div>
						{/each}
					</div>
					<div class="sub">
						{#if diaPico != null}el {DIAS_LARGO[diaPico]} es el día más movido · {/if}<b
							>{totalPulso} acciones en dos semanas</b
						>
					</div>
				{/if}
			</div>
		</Celda>

		<!-- Cifra 1×1: quién lleva más reportes de la semana. -->
		<Celda
			area="3/3/4/4"
			rotulo={unidadTop ? `Más ${unidadTop} · semana` : 'Más reportes · semana'}
			i={3}
		>
			<div class="cuerpo">
				{#if !top || topValor == null}
					<div class="cifra sin">—</div>
					<div class="sub">
						{sinDatos ? 'sin datos del snapshot' : 'sin reportes esta semana'}
					</div>
				{:else}
					<div class="cifra">{topValor}</div>
					<div class="sub"><b>{top?.nombre || 'Sin nombre'}</b></div>
				{/if}
			</div>
		</Celda>

		<CeldaVolt />
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

	/* ── cifras ───────────────────────────────────────────────── */
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
	/* Sin dato: un guion chico y apagado, no una barra negra de 96 px. */
	.cifra.sin {
		font-size: 64px;
		letter-spacing: 0;
		opacity: 0.28;
	}
	/* Sobre la tinta del ancla, 0.28 desaparece: el guion sube para leerse. */
	.cifra.sin.sobre-tinta {
		opacity: 0.6;
	}

	.sub {
		font-size: 21px;
		font-weight: 600;
		opacity: 0.82;
	}
	.sub b {
		font-weight: 800;
		opacity: 1;
	}

	.delta {
		display: block;
		font-size: 20px;
		font-weight: 800;
		color: #fff;
		opacity: 0.85;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	/* La última lectura de km: contexto, un escalón por debajo del delta. */
	.nota {
		font-size: 20px;
		font-weight: 600;
		color: #f7f3ea;
		opacity: 0.62;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	/* ── lista de reportes ────────────────────────────────────── */
	.lista {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
	}
	.fila {
		flex: 1 1 0;
		max-height: 108px;
		min-height: 0;
		display: flex;
		align-items: center;
		gap: 16px;
		padding: 8px 0;
		border-bottom: 1px solid rgba(18, 20, 26, 0.08);
	}
	.fila:last-child {
		border-bottom: 0;
	}
	/* El folio es la identidad del reporte; se lee antes que el cliente. */
	.fol {
		flex: 0 0 112px;
		padding: 7px 10px;
		border-radius: 10px;
		background: rgba(18, 20, 26, 0.06);
		font-size: 20px;
		font-weight: 800;
		letter-spacing: 0.4px;
		text-align: center;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}
	.quien {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
	}
	.quien b {
		font-size: 28px;
		font-weight: 800;
		letter-spacing: -0.4px;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.quien span {
		font-size: 20px;
		font-weight: 600;
		opacity: 0.62;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.estado {
		font-size: 20px;
		font-weight: 800;
		opacity: 0.62;
		white-space: nowrap;
	}
	.estado.ok {
		color: var(--k-verde);
		opacity: 1;
	}
	.estado.medio {
		/* El ámbar del token (#D99A00) sobre blanco da 2.5:1: sirve de fondo,
		   no de texto. Para la palabra se usa su versión oscura (5.5:1). */
		color: var(--k-ambar-texto);
		opacity: 1;
	}
	.sin-filas,
	.sin-dato {
		margin: auto 0;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.sin-filas b,
	.sin-dato b {
		font-size: 24px;
		font-weight: 800;
		opacity: 0.45;
	}
	.sin-filas span,
	.sin-dato span {
		font-size: 20px;
		font-weight: 600;
		opacity: 0.4;
	}

	/* ── barras por día (2×1) ─────────────────────────────────── */
	.dias {
		display: flex;
		align-items: flex-end;
		gap: 18px;
		height: 150px;
	}
	.dcol {
		flex: 1;
		min-width: 0;
		height: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: flex-end;
		gap: 6px;
	}
	.dval {
		font-size: 20px;
		font-weight: 800;
		line-height: 1;
		font-variant-numeric: tabular-nums;
	}
	.dbar {
		width: 100%;
		max-width: 96px;
		border-radius: 8px 8px 0 0;
		background: rgba(18, 20, 26, 0.78);
	}
	/* El pico en verde de apoyo: es el único día que se destaca. */
	.dbar.pico {
		background: var(--k-verde);
	}
	.dpiso {
		font-size: 20px;
		font-weight: 700;
		line-height: 1;
		letter-spacing: 0.6px;
		opacity: 0.45;
	}
	.dpiso.pico {
		opacity: 0.9;
	}
</style>
