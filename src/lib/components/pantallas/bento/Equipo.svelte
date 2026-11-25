<script lang="ts">
	// Equipo, en la retícula bento: cuántos andan en ECCSA Legends y quién
	// celebra algo este mes.
	//
	// Cuatro celdas: el ancla con el número de participantes; la lista con los
	// cumpleaños del mes (con foto); una banda 2×1 con los aniversarios y una
	// cifra chica con los ingresos del mes.
	//
	// RESERVA DE VOLT: la celda 3/4/4/5 (la esquina inferior derecha) NO se
	// usa. Sin dibujar nada ahí, la placa y el globo no tapan ningún dato.
	//
	// El plan pedía dos 1×1 (aniversarios y nuevos), pero eso dejaba una celda
	// vacía en 3/3/4/4 —un hueco visible que no es el rincón de Volt—. Con 11
	// celdas disponibles, los aniversarios van en 2×1: así el dato tiene sitio
	// para tres nombres y se llena la banda inferior.
	//
	// Los datos salen del snapshot (`datos.legends`, `datos.cumpleanos` y
	// `datos.aniversarios`). El bloque de celebraciones puede venir vacío sin
	// que eso signifique un error: en noviembre no siempre cumple nadie. Se
	// dice «sin cumpleaños» en vez de inventar uno.
	import Bento from '$lib/rediseno/Bento.svelte';
	import Celda from '$lib/rediseno/Celda.svelte';
	import Numero from '$lib/rediseno/Numero.svelte';
	import Marco from '$lib/rediseno/Marco.svelte';
	import '$lib/rediseno/tokens.css';
	import { relojKiosco } from '$lib/rediseno/relojKiosco.svelte';
	import { iniciales, nombreMes } from '$lib/kiosk/format';

	interface Cumple {
		Nombre?: string;
		dia?: number | null;
		mes?: number | null;
		edad?: number | null;
		avatar?: string | null;
		foto?: string | null;
	}
	interface Aniv {
		Nombre?: string;
		dia?: number | null;
		anos?: number | null;
		avatar?: string | null;
		foto?: string | null;
	}

	interface Props {
		/** Snapshot del kiosco. Solo se leen `legends`, `cumpleanos` y `aniversarios`. */
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

	// ── Legends: cuántos andan en el equipo ──────────────────────
	const lg = $derived(datos?.legends ?? null);
	const sinLegends = $derived(!lg || cargando);
	const ranking = $derived(Array.isArray(lg?.ranking) ? lg.ranking : []);
	// `participantes` es el conteo que publica el backend. Si el snapshot es
	// viejo y no lo trae, se cuenta el ranking, que es la misma lista.
	const participantes = $derived(aNumero(lg?.participantes) ?? ranking.length);
	const puntos = $derived(aNumero(lg?.total_puntos));

	// ── Celebraciones del mes ────────────────────────────────────
	const hayBloque = $derived(!!datos?.cumpleanos && !!datos?.aniversarios && !cargando);
	const cumples = $derived(
		(hayBloque && Array.isArray(datos.cumpleanos.del_mes)
			? (datos.cumpleanos.del_mes as Cumple[])
			: []
		).filter(Boolean)
	);
	const anivs = $derived(
		(hayBloque && Array.isArray(datos.aniversarios.del_mes)
			? (datos.aniversarios.del_mes as Aniv[])
			: []
		).filter(Boolean)
	);
	/**
	 * «Nuevos del mes» son los ingresos de este mes. En `aniversarios.del_mes`
	 * llegan con `anos: 0` porque su `FechaIngreso` cae en el mes en curso; es
	 * el mismo dato que el backend ya calcula, no se inventa un conteo nuevo.
	 */
	const nuevos = $derived(anivs.filter((a) => a?.anos != null && Number(a.anos) === 0));

	// El mes y el día se leen de un reloj que avanza cada minuto: una TV puede
	// estar encendida semanas y la pantalla no se vuelve a montar. Con un
	// `new Date()` dentro de un `$derived` el «noviembre» se congelaría al
	// montar y el día 1 la pantalla seguiría hablando del mes anterior.
	let ahora = $state(new Date());
	$effect(() => {
		const t = setInterval(() => (ahora = new Date()), 60_000);
		return () => clearInterval(t);
	});
	const mes = $derived(nombreMes(ahora).toLowerCase());
	const mesCorto = $derived(nombreMes(ahora).slice(0, 3).toLowerCase());

	const enLista = $derived(cumples.slice(0, 4));
	const masCumples = $derived(Math.max(0, cumples.length - enLista.length));
	const anivLista = $derived(anivs.slice(0, 3));
	const masAnivs = $derived(Math.max(0, anivs.length - anivLista.length));

	const entero = (n: number) => String(Math.round(n));
	const miles = (n: number) => Math.round(n).toLocaleString('es-MX');

	/** `dia` del snapshot (1-31) contra el día de hoy: solo para el rótulo. */
	function esHoy(dia: unknown): boolean {
		return dia != null && Number(dia) === ahora.getDate();
	}

	// Reloj, fecha y antigüedad: el mismo módulo en todas las pantallas bento.
	const k = relojKiosco(() => ({ reloj, fecha, antiguedad, generadoEn: datos?.generado_en }));

	const linea = $derived(volt ?? frase());
	function frase(): string {
		if (sinLegends) return 'El snapshot todavía no trae al equipo; no invento un cero.';
		const c = cumples.length;
		const nv = nuevos.length;
		const partes: string[] = [];
		if (c) partes.push(c === 1 ? `un cumpleaños en ${mes}` : `${c} cumpleaños en ${mes}`);
		if (nv) partes.push(nv === 1 ? 'un ingreso nuevo' : `${nv} ingresos nuevos`);
		if (!partes.length) {
			return `Sin cumpleaños ni ingresos en ${mes}; ${participantes} en ECCSA Legends.`;
		}
		return `${partes.join(' y ')}; ${participantes} en ECCSA Legends.`;
	}
</script>

<Marco
	titulo="Equipo"
	reloj={k.hora}
	fecha={k.fecha}
	antiguedad={k.antiguedad}
	sinFoto={datos?.pendientes?.vales ?? null}
	posicion={posicion ?? '—'}
	volt={linea}
	degradado={datos?.degradado ?? []}
>
	<Bento>
		<!-- Ancla 2×2: cuántos andan en Legends y cuánto suman esta semana. -->
		<Celda area="1/1/3/3" tono="dark" rotulo="En el equipo" i={0}>
			<div class="cuerpo centro">
				{#if sinLegends}
					<div class="cifra sin">—</div>
					<div class="sub">sin datos del snapshot</div>
				{:else}
					<div class="cifra ancla"><Numero valor={participantes} formato={entero} /></div>
					<div class="sub"><b>en ECCSA Legends</b></div>
					{#if puntos != null && puntos > 0}
						<div class="delta">▲ {miles(puntos)} pts <span>esta semana</span></div>
					{:else}
						<div class="delta neutro"><span>sin puntos esta semana</span></div>
					{/if}
				{/if}
			</div>
		</Celda>

		<!-- Lista 2×2: los cumpleaños del mes, con foto y día. -->
		<Celda area="1/3/3/5" rotulo="Cumpleaños · {mes}" i={1}>
			<div class="lista">
				{#if enLista.length === 0}
					<div class="sin-filas">
						<b>{hayBloque ? `Sin cumpleaños en ${mes}` : 'Sin datos todavía'}</b>
						<span>
							{hayBloque
								? 'El snapshot no trae cumpleaños este mes.'
								: 'El snapshot no trae el bloque de celebraciones.'}
						</span>
					</div>
				{:else}
					{#each enLista as c, i (i)}
						<div class="fila">
							<div class="ava" aria-hidden="true">
								<span>{iniciales(c?.Nombre)}</span>
								{#if c?.foto ?? c?.avatar}
									<img
										src={c.foto ?? c.avatar ?? ''}
										alt=""
										onerror={(e) => (e.currentTarget as HTMLImageElement).remove()}
									/>
								{/if}
							</div>
							<div class="quien">
								<b>{c?.Nombre || 'Sin nombre'}</b>
								<span>
									{#if esHoy(c?.dia)}
										<em class="hoy">hoy</em>
									{/if}
									{#if c?.edad != null}
										cumple {c.edad}
									{:else}
										cumpleaños
									{/if}
								</span>
							</div>
							<div class="dia" class:hoy={esHoy(c?.dia)}>
								<b>{c?.dia ?? '—'}</b><span>{mesCorto}</span>
							</div>
						</div>
					{/each}
					{#if masCumples > 0}
						<div class="mas-fila">+{masCumples} más en {mes}</div>
					{/if}
				{/if}
			</div>
		</Celda>

		<!-- Aniversarios 2×1: cuántos son y quiénes, con sus años. -->
		<Celda area="3/1/4/3" rotulo="Aniversarios · {mes}" i={2}>
			<div class="cuerpo">
				{#if !hayBloque}
					<div class="cifra sin">—</div>
					<div class="sub">sin datos del snapshot</div>
				{:else}
					<div class="aniv">
						<div class="aniv-cifra">
							<div class="cifra">{anivs.length}</div>
							<div class="sub">
								{#if anivs.length === 1}
									aniversario en {mes}
								{:else}
									aniversarios en {mes}
								{/if}
							</div>
						</div>
						<div class="aniv-lista">
							{#if anivLista.length === 0}
								<div class="sin-aniv">nadie cumple años en ECCSA este mes</div>
							{:else}
								{#each anivLista as a, i (i)}
									<div class="mini">
										<b>{a?.Nombre || 'Sin nombre'}</b>
										<span>
											{a?.dia ?? '—'} {mesCorto}{#if a?.anos != null}
												· <em class:cero={Number(a.anos) === 0}
													>{Number(a.anos) === 0 ? 'nuevo' : `${a.anos} años`}</em
												>{/if}
										</span>
									</div>
								{/each}
								{#if masAnivs > 0}
									<div class="mas-fila">+{masAnivs} más</div>
								{/if}
							{/if}
						</div>
					</div>
				{/if}
			</div>
		</Celda>

		<!-- Cifra 1×1: ingresos de este mes (aniversarios de 0 años). -->
		<Celda area="3/3/4/4" rotulo="Nuevos del mes" i={3}>
			<div class="cuerpo">
				{#if !hayBloque}
					<div class="cifra sin">—</div>
					<div class="sub">sin datos del snapshot</div>
				{:else}
					<div class="cifra">{nuevos.length}</div>
					<div class="sub">
						{#if nuevos.length === 0}
							sin ingresos en {mes}
						{:else if nuevos.length === 1}
							ingreso en {mes}
						{:else}
							ingresos en {mes}
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
		color: #7fe3cf;
	}
	.delta.neutro {
		color: #f7f3ea;
	}
	.delta span {
		font-weight: 600;
		opacity: 0.6;
	}

	/* ── lista de cumpleaños ──────────────────────────────────── */
	.lista {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
	}
	.fila {
		flex: 1 1 0;
		max-height: 116px;
		min-height: 0;
		display: flex;
		align-items: center;
		gap: 18px;
		padding: 8px 0;
		border-bottom: 1px solid rgba(18, 20, 26, 0.08);
	}
	.fila:last-child {
		border-bottom: 0;
	}
	.ava {
		position: relative;
		width: 68px;
		height: 68px;
		flex: 0 0 68px;
		border-radius: 50%;
		background: #e6ddcd;
		color: #6d6455;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
		font-size: 26px;
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
	}
	.quien b {
		font-size: 30px;
		font-weight: 800;
		letter-spacing: -0.4px;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.quien span {
		font-size: 21px;
		font-weight: 600;
		opacity: 0.55;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	/* El día, en columna: el número se lee desde el otro lado del pasillo. */
	.dia {
		flex: 0 0 auto;
		display: flex;
		flex-direction: column;
		align-items: center;
		min-width: 74px;
	}
	.dia b {
		font-size: 44px;
		font-weight: 900;
		line-height: 0.9;
		letter-spacing: -1.5px;
		font-variant-numeric: tabular-nums;
	}
	.dia span {
		font-size: 20px;
		font-weight: 700;
		letter-spacing: 1.2px;
		text-transform: uppercase;
		opacity: 0.45;
	}
	/* Hoy sí se pinta en rojo: es el único cumpleaños que cambia de un día a otro. */
	.dia.hoy b,
	.dia.hoy span,
	.hoy {
		color: var(--k-rojo);
		opacity: 1;
		font-style: normal;
		font-weight: 800;
	}
	.mas-fila {
		font-size: 21px;
		font-weight: 700;
		opacity: 0.5;
		padding-top: 8px;
	}
	.sin-filas {
		margin: auto 0;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.sin-filas b {
		font-size: 24px;
		font-weight: 800;
		opacity: 0.45;
	}
	.sin-filas span {
		font-size: 20px;
		font-weight: 600;
		opacity: 0.4;
	}

	/* ── aniversarios (2×1) ───────────────────────────────────── */
	.aniv {
		display: flex;
		align-items: center;
		gap: 36px;
		min-height: 0;
	}
	.aniv-cifra {
		flex: 0 0 auto;
	}
	.aniv-cifra .cifra {
		margin-bottom: 2px;
	}
	.aniv-cifra .sub {
		max-width: 210px;
	}
	.aniv-lista {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.mini {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 16px;
		font-size: 21px;
		line-height: 1.25;
	}
	.mini b {
		font-weight: 700;
		min-width: 0;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.mini span {
		font-weight: 600;
		opacity: 0.55;
		white-space: nowrap;
	}
	.mini em {
		font-style: normal;
		font-weight: 800;
		opacity: 1;
	}
	.mini em.cero {
		color: var(--k-verde);
	}
	.sin-aniv {
		font-size: 21px;
		font-weight: 600;
		opacity: 0.45;
	}
</style>
