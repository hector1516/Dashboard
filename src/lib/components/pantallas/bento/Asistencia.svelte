<script lang="ts">
	// Asistencia del día, en la retícula bento.
	//
	// Cinco celdas: el ancla dice cuántos siguen en la oficina y con qué caras;
	// la lista nombra a cuatro de ellos; dos cifras chicas contestan «cuántos
	// llegaron» y «cuántos ya se fueron»; y «Últimos movimientos» resume los
	// tres eventos más recientes de la red.
	//
	// RESERVA DE VOLT: la celda 3/4/4/5 (la esquina inferior derecha) NO se
	// usa. La placa (112 px a 18 px del borde) y su globo viven ahí; al no
	// dibujar nada, no tapan ningún dato. Con eso quedan 11 celdas ocupadas y
	// las cinco piezas caben así: ancla 2×2, lista 2×2 y tres celdas de una
	// en la banda de abajo.
	//
	// El plan pedía «últimos movimientos» en 2×1, pero eso pedía 12 celdas
	// (ancla 4 + lista 4 + 1 + 1 + 2) cuando la retícula solo tiene 11 con el
	// rincón de Volt apartado. Se queda 1×1 con las mismas tres filas: en 446
	// px caben nombre y hora en la misma línea.
	//
	// Los datos salen del snapshot (`datos.asistencia`), que el snapshotter
	// arma de `HUB_NetworkPresence`. Si el snapshot todavía es el vacío del
	// arranque (`degradado: ['cargando']`) no se pinta un cero: se dice que no
	// hay dato. Un cero de verdad (nadie se ha conectado hoy) sí se pinta.
	import Bento from '$lib/rediseno/Bento.svelte';
	import Celda from '$lib/rediseno/Celda.svelte';
	import Numero from '$lib/rediseno/Numero.svelte';
	import Marco from '$lib/rediseno/Marco.svelte';
	import '$lib/rediseno/tokens.css';
	import { relojKiosco } from '$lib/rediseno/relojKiosco.svelte';
	import { hhmm, iniciales } from '$lib/kiosk/format';

	interface Persona {
		id_usuario?: number;
		nombre?: string;
		/** "YYYY-MM-DD HH:MM" de la primera ENTRADA del día. */
		entrada?: string;
		/** Última SALIDA; vacío si sigue dentro. */
		salida?: string;
		/** Entrada de la visita en la que sigue (si salió y volvió). */
		reingreso?: string;
		eventos?: number;
		en_sitio?: boolean;
		avatar?: string | null;
		/** Foto real; el snapshotter la prefiere sobre `avatar`. */
		foto?: string | null;
	}

	interface Movimiento {
		nombre: string;
		hora: string;
		entro: boolean;
	}

	interface Props {
		/** Snapshot del kiosco. Solo se lee `asistencia`. */
		datos?: any;
		/** Hora `HH:MM` ya formateada. Sin ella la toma del reloj. */
		reloj?: string;
		/** Fecha larga. Sin ella, la de hoy. */
		fecha?: string;
		/** «datos de hace 1 min». Sin ella, se calcula de `generado_en`. */
		antiguedad?: string;
		/** Posición en la rotación (`1/10`). Sin ella, un guion. */
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

	const a = $derived(datos?.asistencia ?? null);
	// El snapshot vacío del arranque trae `degradado: ['cargando']` y listas en
	// cero. Eso NO es «nadie vino»: es «todavía no hay dato».
	const sinDatos = $derived(!a || (datos?.degradado ?? []).includes('cargando'));

	const personas = $derived(
		(Array.isArray(a?.personas) ? (a.personas as Persona[]) : []).filter(Boolean)
	);
	/** Siguen dentro (último evento del día = ENTRADA). */
	const dentro = $derived(personas.filter((p) => p?.en_sitio));
	/** Ya se fueron: su última salida sí pasó. */
	const fuera = $derived(personas.filter((p) => p && !p.en_sitio));

	const dentroN = $derived(aNumero(a?.dentro) ?? dentro.length);
	const total = $derived(aNumero(a?.total) ?? personas.length);
	const salieronN = $derived(aNumero(a?.salieron) ?? fuera.length);

	/** Las caras del ancla: hasta cinco, con «+N» para el resto. */
	const caras = $derived(dentro.slice(0, 5));
	const masCaras = $derived(Math.max(0, dentro.length - caras.length));
	/** La lista nombra a cuatro; si hay más, se dice cuántos quedan fuera. */
	const enLista = $derived(dentro.slice(0, 4));
	const masEnLista = $derived(Math.max(0, dentro.length - enLista.length));

	/** La primera llegada y la última salida del día, ya en `HH:MM`. */
	const primera = $derived(horaExtremo(personas.map((p) => p?.entrada), 'min'));
	const ultimaSalida = $derived(horaExtremo(fuera.map((p) => p?.salida), 'max'));

	/**
	 * `sort()` sobre el ISO completo basta dentro de un mismo día: llegan en el
	 * mismo formato "YYYY-MM-DD HH:MM". Se arma la hora con `hhmm` —nunca con
	 * `new Date(iso)`, que en Safari lee la cadena como UTC.
	 */
	function horaExtremo(valores: (string | undefined)[], cual: 'min' | 'max'): string {
		const l = valores.filter((x): x is string => typeof x === 'string' && x.length > 0).sort();
		if (!l.length) return '';
		const iso = cual === 'min' ? l[0] : l[l.length - 1];
		const h = hhmm(iso);
		return h === '—' ? '' : h;
	}

	/**
	 * Los tres movimientos más recientes. El último evento de cada quien es su
	 * ENTRADA si sigue dentro (con `reingreso` cuando salió y volvió) o su
	 * SALIDA si ya se fue. Así «se fue 11:18» y «en la oficina» nunca se
	 * contradicen.
	 */
	const movimientos = $derived.by<Movimiento[]>(() => {
		const m: Movimiento[] = [];
		for (const p of personas) {
			const entro = !!p?.en_sitio;
			const iso = entro ? p?.reingreso || p?.entrada : p?.salida || p?.entrada;
			const hora = iso ? hhmm(iso) : '—';
			if (hora === '—') continue;
			m.push({ nombre: p?.nombre || 'Sin nombre', hora, entro });
		}
		return m.sort((x, y) => y.hora.localeCompare(x.hora)).slice(0, 3);
	});

	const entero = (n: number) => String(Math.round(n));

	// Reloj, fecha y antigüedad: el mismo módulo en todas las pantallas bento.
	const k = relojKiosco(() => ({ reloj, fecha, antiguedad, generadoEn: datos?.generado_en }));

	const linea = $derived(volt ?? frase());
	function frase(): string {
		if (sinDatos) return 'El snapshot todavía no trae la asistencia del día; no invento un cero.';
		if (total === 0) {
			return 'Sin movimientos hoy: la red de la oficina avisa en cuanto alguien se conecta.';
		}
		if (dentroN === 0) {
			return 'Ya no queda nadie en la oficina; todos los registros de hoy tienen su salida.';
		}
		const quien = dentroN === 1 ? 'Una persona sigue' : `${dentroN} siguen`;
		return ultimaSalida
			? `${quien} en la oficina; la última salida fue a las ${ultimaSalida}.`
			: `${quien} en la oficina; todavía no sale nadie.`;
	}
</script>

<Marco
	titulo="Asistencia de hoy"
	reloj={k.hora}
	fecha={k.fecha}
	antiguedad={k.antiguedad}
	temperatura={datos?.clima?.actual?.temperatura}
	posicion={posicion ?? '—'}
	volt={linea}
	degradado={datos?.degradado ?? []}
>
	<Bento>
		<!-- Ancla 2×2: quién sigue en la oficina, con sus caras. -->
		<Celda area="1/1/3/3" tono="dark" rotulo="En la oficina" i={0}>
			<div class="cuerpo centro">
				{#if sinDatos}
					<div class="cifra sin">—</div>
					<div class="sub">sin datos del snapshot</div>
				{:else}
					<div class="cifra ancla"><Numero valor={dentroN} formato={entero} /></div>
					<div class="sub">
						{#if total > 0}
							<b>de {total}</b> que registraron hoy
						{:else}
							nadie se ha conectado todavía
						{/if}
					</div>
					{#if caras.length}
						<div class="caras" aria-hidden="true">
							{#each caras as p, i (i)}
								<div class="cara">
									<!-- Iniciales debajo: si la foto no está (o la ruta
									     es vieja), `onerror` la quita y queda el círculo. -->
									<span>{iniciales(p?.nombre)}</span>
									{#if p?.foto ?? p?.avatar}
										<img
											src={p.foto ?? p.avatar ?? ''}
											alt=""
											onerror={(e) => (e.currentTarget as HTMLImageElement).remove()}
										/>
									{/if}
								</div>
							{/each}
							{#if masCaras > 0}<div class="mas">+{masCaras}</div>{/if}
						</div>
					{/if}
				{/if}
			</div>
		</Celda>

		<!-- Lista 2×2: cuatro de los que siguen aquí. -->
		<Celda area="1/3/3/5" rotulo="Quién sigue aquí" i={1}>
			<div class="lista">
				{#if enLista.length === 0}
					<div class="sin-filas">
						<b>{sinDatos ? 'Sin datos todavía' : 'Nadie en la oficina'}</b>
						<span>
							{sinDatos
								? 'El snapshot no trae el bloque de asistencia.'
								: total > 0
									? 'Todos los que registraron hoy ya se fueron.'
									: 'La lista se llena con la primera conexión a la red de la oficina.'}
						</span>
					</div>
				{:else}
					{#each enLista as p, i (p?.id_usuario ?? i)}
						<div class="fila">
							<div class="ava" aria-hidden="true">
								<span>{iniciales(p?.nombre)}</span>
								{#if p?.foto ?? p?.avatar}
									<img
										src={p.foto ?? p.avatar ?? ''}
										alt=""
										onerror={(e) => (e.currentTarget as HTMLImageElement).remove()}
									/>
								{/if}
							</div>
							<div class="quien">
								<b>{p?.nombre || 'Sin nombre'}</b>
								<span>
									{#if p?.reingreso}
										de vuelta desde las {hhmm(p.reingreso)}
									{:else if p?.entrada}
										desde las {hhmm(p.entrada)}
									{:else}
										en la oficina
									{/if}
								</span>
							</div>
							<div class="punto" aria-hidden="true"></div>
						</div>
					{/each}
					<div class="mas-fila">
						{#if masEnLista > 0}+{masEnLista} más en la oficina · {/if}según la red de la
						oficina
					</div>
				{/if}
			</div>
		</Celda>

		<!-- Cifra 1×1: cuántos llegaron y a qué hora fue la primera llegada. -->
		<Celda area="3/1/4/2" rotulo="Llegaron hoy" i={2}>
			<div class="cuerpo">
				{#if sinDatos}
					<div class="cifra sin">—</div>
					<div class="sub">sin datos del snapshot</div>
				{:else}
					<div class="cifra">{total}</div>
					<div class="sub">
						{#if primera}
							primera, <b>{primera}</b>
						{:else}
							sin registros hoy
						{/if}
					</div>
				{/if}
			</div>
		</Celda>

		<!-- Cifra 1×1: cuántos ya se fueron y la última salida del día. -->
		<Celda area="3/2/4/3" rotulo="Ya se fueron" i={3}>
			<div class="cuerpo">
				{#if sinDatos}
					<div class="cifra sin">—</div>
					<div class="sub">sin datos del snapshot</div>
				{:else}
					<div class="cifra">{salieronN}</div>
					<div class="sub">
						{#if ultimaSalida}
							última, <b>{ultimaSalida}</b>
						{:else if salieronN > 0}
							sin hora de salida
						{:else}
							nadie ha salido
						{/if}
					</div>
				{/if}
			</div>
		</Celda>

		<!-- Movimientos 1×1: los tres eventos más recientes de la red. -->
		<Celda area="3/3/4/4" rotulo="Últimos movimientos" i={4}>
			<div class="movs">
				{#if movimientos.length === 0}
					<div class="sin-filas">
						<b>{sinDatos ? 'Sin datos' : 'Sin movimientos'}</b>
						<span>
							{sinDatos
								? 'El snapshot no trae el bloque de asistencia.'
								: 'La red no ha marcado entradas ni salidas hoy.'}
						</span>
					</div>
				{:else}
					{#each movimientos as m, i (i)}
						<div class="mov">
							<div class="ico" class:in={m.entro} class:out={!m.entro} aria-hidden="true">
								{m.entro ? '→' : '←'}
							</div>
							<div class="nom">{m.nombre}</div>
							<div class="hora">{m.hora}</div>
						</div>
					{/each}
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
		opacity: 0.82;
	}
	.sub b {
		font-weight: 800;
		opacity: 1;
	}

	/* ── caras del ancla ──────────────────────────────────────── */
	.caras {
		display: flex;
		align-items: center;
		margin-top: 14px;
	}
	.cara,
	.mas {
		width: 76px;
		height: 76px;
		border-radius: 50%;
		border: 3px solid var(--k-tinta);
		margin-left: -16px;
		background: #e6ddcd;
		color: #6d6455;
		font-size: 24px;
		font-weight: 900;
		letter-spacing: 0.5px;
	}
	.cara:first-child,
	.mas:first-child {
		margin-left: 0;
	}
	.cara {
		position: relative;
		overflow: hidden;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.cara img {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
	.mas {
		display: flex;
		align-items: center;
		justify-content: center;
	}

	/* ── lista de quién sigue ─────────────────────────────────── */
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
		opacity: 0.62;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	/* Punto verde: sigue dentro. Sin texto a 3 metros, un punto se lee. */
	.punto {
		width: 14px;
		height: 14px;
		flex: 0 0 14px;
		border-radius: 50%;
		background: var(--k-verde);
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

	/* ── últimos movimientos ──────────────────────────────────── */
	.movs {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
		justify-content: flex-end;
	}
	.mov {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 9px 0;
		border-bottom: 1px solid rgba(18, 20, 26, 0.08);
	}
	.mov:last-child {
		border-bottom: 0;
	}
	.ico {
		width: 40px;
		height: 40px;
		flex: 0 0 40px;
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 22px;
		font-weight: 900;
	}
	.ico.in {
		background: rgba(14, 143, 126, 0.14);
		color: var(--k-verde);
	}
	.ico.out {
		background: rgba(217, 154, 0, 0.16);
		color: var(--k-ambar);
	}
	.nom {
		flex: 1;
		min-width: 0;
		font-size: 24px;
		font-weight: 700;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.hora {
		font-size: 22px;
		font-weight: 800;
		font-variant-numeric: tabular-nums;
		opacity: 0.65;
	}
</style>
