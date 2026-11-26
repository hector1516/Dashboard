<script lang="ts">
	// Equipo, en la retícula bento: cuánta gente hay, quién juega Legends y
	// quién celebra algo, en cualquier mes.
	//
	// Cuatro celdas:
	//   · ancla 2×2 → personas activas y la línea de ECCSA Legends;
	//   · lista 2×2 → TODOS los integrantes de Legends con sus puntos (sin
	//     tope ni «+N más»: la celda tiene alto de sobra para la plantilla);
	//   · dos 1×1   → los próximos cumpleaños y los próximos aniversarios.
	//
	// Las celebraciones son RODANTES (`proximos_cumpleanos` y
	// `proximos_aniversarios` del snapshot): los 3 más cercanos, cuente el mes
	// que cuente. Antes esta pantalla enseñaba el mes en curso y en noviembre
	// —que no cumple nadie— quedaba vacía once meses al año. Un cumpleaños de
	// enero se anuncia en diciembre, que es cuando sirve.
	//
	// RESERVA DE VOLT: la esquina inferior derecha (3/3 y 3/4 de la retícula)
	// NO se usa. Sin dibujar nada ahí, la placa y el globo no tapan ningún
	// dato; el hueco es a propósito y no un hueco olvidado.
	//
	// Los bloques pueden venir vacíos o no venir: `proximos_*` es opcional
	// porque el snapshot en disco puede ser de antes del cambio. Se dice «sin
	// datos» en vez de inventar un cero o un cumpleaños.
	import Bento from '$lib/rediseno/Bento.svelte';
	import Celda from '$lib/rediseno/Celda.svelte';
	import Numero from '$lib/rediseno/Numero.svelte';
	import Marco from '$lib/rediseno/Marco.svelte';
	import '$lib/rediseno/tokens.css';
	import { relojKiosco } from '$lib/rediseno/relojKiosco.svelte';
	import { iniciales } from '$lib/kiosk/format';
	import type { ProximoAniversario, ProximoCumple } from '$lib/kiosk/types';

	interface FilaRank {
		id_usuario?: number;
		nombre?: string;
		nickname?: string;
		puntos_semana?: number | null;
		puntos_temporada?: number | null;
		avatar?: string | null;
	}

	interface Props {
		/** Snapshot del kiosco. Solo se leen `equipo`, `legends` y celebraciones. */
		datos?: any;
		/** Hora `HH:MM` ya formateada. Sin ella la toma del reloj. */
		reloj?: string;
		/** Fecha larga. Sin ella, la de hoy. */
		fecha?: string;
		/** «datos de hace 1 min». Sin ella, se calcula de `generado_en`. */
		antiguedad?: string;
		/** Posición en la rotación (`8/10`). Sin ella, un guion. */
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

	const cargando = $derived((datos?.degradado ?? []).includes('cargando'));

	// ── Ancla: cuánta gente activa hay ───────────────────────────
	const eq = $derived(datos?.equipo ?? null);
	const personas = $derived(aNumero(eq?.personas));

	// ── Legends: participantes y tabla completa ──────────────────
	const lg = $derived(datos?.legends ?? null);
	const sinLegends = $derived(!lg || cargando);
	const ranking = $derived(
		(Array.isArray(lg?.ranking) ? (lg.ranking as FilaRank[]) : []).filter(Boolean)
	);
	// `participantes` lo publica el backend; si el snapshot es viejo y no lo
	// trae, se cuenta el ranking, que es la misma lista.
	const participantes = $derived(aNumero(lg?.participantes) ?? ranking.length);
	const puntos = $derived(aNumero(lg?.total_puntos));

	// ── Celebraciones rodantes ───────────────────────────────────
	// `undefined` = el snapshot no trae la lista (es opcional y puede ser de
	// antes del cambio). `[]` = la trae y no hay nadie. No es lo mismo.
	const crudoCumples = $derived(datos?.cumpleanos?.proximos_cumpleanos);
	const crudoAnivs = $derived(datos?.aniversarios?.proximos_aniversarios);
	const hayCumples = $derived(Array.isArray(crudoCumples));
	const hayAnivs = $derived(Array.isArray(crudoAnivs));
	const cumples = $derived(
		(hayCumples ? (crudoCumples as ProximoCumple[]) : []).filter(Boolean).slice(0, 3)
	);
	const anivs = $derived(
		(hayAnivs ? (crudoAnivs as ProximoAniversario[]) : []).filter(Boolean).slice(0, 3)
	);

	const entero = (n: number) => String(Math.round(n));
	const miles = (n: number | null) => (n == null ? '—' : Math.round(n).toLocaleString('es-MX'));

	/**
	 * Días que faltan HOY a la próxima ocurrencia.
	 *
	 * El snapshot trae `dias` calculado el día que se generó. Si el snapshot
	 * lleva dos días en disco, ese 0 ya no es «hoy». Primero se usa `p.fecha`
	 * (la fecha absoluta de la próxima ocurrencia); si no viene, se suma la
	 * edad del snapshot (`generado_en`) a `dias`. Si la fecha absoluta ya pasó
	 * —snapshot viejo—, se avanza al mismo día del año siguiente, que es
	 * cuando vuelve a caer la fiesta.
	 */
	function diasHasta(fecha: unknown, diasSnapshot: unknown): number {
		const m = typeof fecha === 'string' ? /^(\d{4})-(\d{2})-(\d{2})/.exec(fecha) : null;
		if (m) {
			const hoy = new Date();
			const base = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate());
			const objetivo = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
			if (!Number.isNaN(objetivo.getTime())) {
				let d = Math.round((objetivo.getTime() - base.getTime()) / 86_400_000);
				// Un snapshot de hace meses no puede decir «en -40 días».
				for (let vuelta = 0; d < 0 && vuelta < 3; vuelta++) {
					objetivo.setFullYear(objetivo.getFullYear() + 1);
					d = Math.round((objetivo.getTime() - base.getTime()) / 86_400_000);
				}
				if (d >= 0) return d;
			}
		}
		// Sin fecha utilizable: el día que decía el snapshot, más los días que
		// el snapshot lleva esperando en disco.
		return Math.max(0, Math.round(Number(diasSnapshot ?? 0) || 0) + edadSnapshot());
	}

	/** Días completos que el snapshot lleva generado (0 si no se sabe). */
	function edadSnapshot(): number {
		const iso = datos?.generado_en;
		if (typeof iso !== 'string') return 0;
		const t = Date.parse(iso);
		if (!Number.isFinite(t)) return 0;
		return Math.max(0, Math.floor((Date.now() - t) / 86_400_000));
	}

	/** «hoy» o «en N días». El día 0 se dice hoy, no «en 0 días». */
	function cuando(fecha: unknown, diasSnapshot: unknown): string {
		const d = diasHasta(fecha, diasSnapshot);
		if (d === 0) return 'hoy';
		return d === 1 ? 'en 1 día' : `en ${d} días`;
	}

	/** «1 año» / «5 años», sin NaN si el snapshot trae basura. */
	function anosTexto(n: unknown): string {
		const a = Math.max(0, Math.round(Number(n ?? 0) || 0));
		return a === 1 ? '1 año' : `${a} años`;
	}

	// Reloj, fecha y antigüedad: el mismo módulo en todas las pantallas bento.
	const k = relojKiosco(() => ({ reloj, fecha, antiguedad, generadoEn: datos?.generado_en }));

	const linea = $derived(volt ?? frase());
	function frase(): string {
		if (personas == null && sinLegends) {
			return 'El snapshot todavía no trae al equipo; no invento un cero.';
		}
		const partes: string[] = [];
		if (personas != null) {
			partes.push(
				personas === 1 ? '1 persona activa' : `${personas} personas activas`
			);
		}
		if (!sinLegends) {
			partes.push(
				participantes === 1
					? '1 en ECCSA Legends'
					: `${participantes} en ECCSA Legends`
			);
		}
		return `${partes.join(' · ')}.`;
	}
</script>

<Marco
	titulo="Equipo"
	reloj={k.hora}
	fecha={k.fecha}
	antiguedad={k.antiguedad}
	temperatura={datos?.clima?.actual?.temperatura}
	posicion={posicion ?? '—'}
	volt={linea}
	degradado={datos?.degradado ?? []}
>
	<Bento>
		<!-- Ancla 2×2: cuántas personas activas hay y cuántas juegan Legends. -->
		<Celda area="1/1/3/3" tono="azul" rotulo="En el equipo" i={0}>
			<div class="cuerpo centro">
				{#if personas == null}
					<div class="cifra sin">—</div>
					<div class="sub">sin datos del snapshot</div>
				{:else}
					<div class="cifra ancla"><Numero valor={personas} formato={entero} /></div>
					<div class="sub">
						<b>{personas === 1 ? 'persona activa' : 'personas activas'}</b>
					</div>
				{/if}
				<!-- La línea de Legends, siempre; sin bloque se dice, no se deja vacía. -->
				<div class="delta" class:vacio={sinLegends}>
					{#if sinLegends}
						<span>sin datos de ECCSA Legends</span>
					{:else}
						<b>{participantes}</b>
						<span>en ECCSA Legends</span>
						{#if puntos != null && puntos > 0}
							<span>· {miles(puntos)} pts esta semana</span>
						{/if}
					{/if}
				</div>
			</div>
		</Celda>

		<!-- Tabla 2×2: todos los integrantes de Legends, con sus puntos. -->
		<Celda area="1/3/3/5" rotulo="ECCSA Legends · semana" i={1}>
			<div class="rank">
				{#if sinLegends}
					<div class="sin-filas">
						<b>Sin datos todavía</b>
						<span>El snapshot no trae el bloque de ECCSA Legends.</span>
					</div>
				{:else if ranking.length === 0}
					<div class="sin-filas">
						<b>Sin participantes</b>
						<span>Nadie de la plantilla juega ECCSA Legends todavía.</span>
					</div>
				{:else}
					<div class="rank-lista">
						{#each ranking as r, i (r.id_usuario ?? i)}
							<div class="r-fila">
								<span class="pos">{i + 1}</span>
								<b class="nom">{r.nombre || r.nickname || 'Sin nombre'}</b>
								<span class="pts">
									{aNumero(r.puntos_semana) == null ? '—' : miles(aNumero(r.puntos_semana))}
									<small>pts</small>
								</span>
							</div>
						{/each}
					</div>
					<div class="rank-pie">
						{participantes}
						{participantes === 1 ? 'participante' : 'participantes'}{#if puntos != null && puntos > 0}
							· {miles(puntos)} pts en la semana{/if}
					</div>
				{/if}
			</div>
		</Celda>

		<!-- 1×1: los 3 cumpleaños más cercanos, sin importar el mes. -->
		<Celda area="3/1/4/2" rotulo="Próximos cumpleaños" i={2}>
			<div class="pers">
				{#if !hayCumples}
					<div class="sin-filas">
						<b>Sin datos todavía</b>
						<span>El snapshot no trae las próximas fechas.</span>
					</div>
				{:else if cumples.length === 0}
					<div class="sin-filas">
						<b>Sin fechas</b>
						<span>Ninguna persona activa tiene fecha de nacimiento.</span>
					</div>
				{:else}
					{#each cumples as p, i (p.nombre + i)}
						<div class="p-fila">
							<div class="ava" aria-hidden="true">
								<span>{iniciales(p.nombre)}</span>
								{#if p.foto ?? p.avatar}
									<img
										src={p.foto ?? p.avatar ?? ''}
										alt=""
										onerror={(e) => (e.currentTarget as HTMLImageElement).remove()}
									/>
								{/if}
							</div>
							<div class="quien">
								<b>{p.nombre || 'Sin nombre'}</b>
								<span class:hoy={diasHasta(p.fecha, p.dias) === 0}
									>{cuando(p.fecha, p.dias)}</span
								>
							</div>
						</div>
					{/each}
				{/if}
			</div>
		</Celda>

		<!-- 1×1: los 3 aniversarios más cercanos (sólo años cumplidos). -->
		<Celda area="3/2/4/3" rotulo="Próximos aniversarios" i={3}>
			<div class="pers">
				{#if !hayAnivs}
					<div class="sin-filas">
						<b>Sin datos todavía</b>
						<span>El snapshot no trae las próximas fechas.</span>
					</div>
				{:else if anivs.length === 0}
					<div class="sin-filas">
						<b>Sin fechas</b>
						<span>Nadie con un año cumplido tiene fecha de ingreso.</span>
					</div>
				{:else}
					{#each anivs as a, i (a.nombre + i)}
						<div class="p-fila">
							<div class="ava" aria-hidden="true">
								<span>{iniciales(a.nombre)}</span>
								{#if a.foto ?? a.avatar}
									<img
										src={a.foto ?? a.avatar ?? ''}
										alt=""
										onerror={(e) => (e.currentTarget as HTMLImageElement).remove()}
									/>
								{/if}
							</div>
							<div class="quien">
								<b>{a.nombre || 'Sin nombre'}</b>
								<span class:hoy={diasHasta(a.fecha, a.dias) === 0}>
									{anosTexto(a.anos)} · {cuando(a.fecha, a.dias)}
								</span>
							</div>
						</div>
					{/each}
				{/if}
			</div>
		</Celda>

		<!-- 3/3 y 3/4 NO se usan: es el rincón de Volt (placa de 112 px + globo). -->
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
		display: flex;
		align-items: baseline;
		flex-wrap: wrap;
		gap: 8px;
		font-size: 22px;
		font-weight: 700;
		color: #7fe3cf;
	}
	.delta b {
		font-weight: 900;
	}
	.delta span {
		font-weight: 600;
		color: #f7f3ea;
		opacity: 0.72;
	}
	.delta.vacio span {
		color: #f7f3ea;
		opacity: 0.45;
	}

	/* ── tabla de ECCSA Legends ───────────────────────────────── */
	.rank {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
		justify-content: center;
		gap: 8px;
	}
	.rank-lista {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
		justify-content: center;
	}
	/* Filas flexibles: 12 integrantes caben en ~40 px cada uno y 20 se
	   aprietan a 24 px sin scroll. No hay tope: se ven todos. */
	.r-fila {
		flex: 1 1 0;
		min-height: 24px;
		max-height: 44px;
		display: flex;
		align-items: center;
		gap: 14px;
		border-bottom: 1px solid rgba(18, 20, 26, 0.07);
		font-size: 21px;
	}
	.r-fila:last-child {
		border-bottom: 0;
	}
	.pos {
		flex: 0 0 22px;
		text-align: right;
		font-weight: 700;
		opacity: 0.35;
		font-variant-numeric: tabular-nums;
	}
	.nom {
		flex: 1;
		min-width: 0;
		font-weight: 800;
		letter-spacing: -0.2px;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.pts {
		flex: 0 0 auto;
		font-weight: 900;
		font-variant-numeric: tabular-nums;
		letter-spacing: -0.4px;
	}
	.pts small {
		/* 20 px: en este sistema nada baja de ahí (se lee a 3 m). */
		font-size: 20px;
		font-weight: 700;
		opacity: 0.62;
		margin-left: 2px;
	}
	/* La suma de la semana: contexto de los puntos de arriba, no otra cifra. */
	.rank-pie {
		font-size: 20px;
		font-weight: 600;
		opacity: 0.45;
	}

	/* ── cumpleaños y aniversarios (1×1) ─────────────────────── */
	.pers {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
		justify-content: center;
		gap: 6px;
	}
	.p-fila {
		display: flex;
		align-items: center;
		gap: 14px;
		min-width: 0;
	}
	.ava {
		position: relative;
		width: 44px;
		height: 44px;
		flex: 0 0 44px;
		border-radius: 50%;
		background: #e6ddcd;
		color: #6d6455;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
		/* 20 px: el mínimo de letra del sistema, también en las iniciales. */
		font-size: 20px;
		font-weight: 900;
		letter-spacing: 0.5px;
	}
	.ava img {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: cover;
		border-radius: 50%;
	}
	.quien {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 1px;
	}
	.quien b {
		font-size: 23px;
		font-weight: 800;
		letter-spacing: -0.3px;
		line-height: 1.15;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.quien span {
		font-size: 20px;
		font-weight: 600;
		opacity: 0.62;
		line-height: 1.15;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	/* Hoy sí se pinta en rojo: es el único dato que cambia de un día a otro. */
	.quien span.hoy {
		color: var(--k-rojo);
		opacity: 1;
		font-weight: 800;
	}

	.sin-filas {
		margin: auto 0;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.sin-filas b {
		font-size: 22px;
		font-weight: 800;
		opacity: 0.45;
	}
	.sin-filas span {
		font-size: 20px;
		font-weight: 600;
		opacity: 0.4;
	}
</style>
