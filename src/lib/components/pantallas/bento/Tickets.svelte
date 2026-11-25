<script lang="ts">
	// Tickets OxxoGas, en la retícula bento.
	//
	// Cuatro celdas: el ancla con los tickets registrados y la fecha del
	// último; la lista con los cuatro más recientes, su miniatura y el
	// cliente; una banda 2×1 con dos estados (con vale entre los últimos que
	// publica el snapshot, con foto entre los cuatro en pantalla); y la cifra
	// chica con el auto que más carga.
	//
	// RESERVA DE VOLT: la celda 3/4/4/5 (la esquina inferior derecha) NO se
	// usa. La placa y el globo viven ahí; sin dibujar nada, no tapan ningún
	// dato.
	//
	// TRES COSAS QUE EL DATO NO PERMITE Y NO SE FINGEN:
	//   · El ancla NO dice «tickets de la semana». `tickets.total_semana` es
	//     COUNT(*) de TODA la tabla (`api/datos.py::tickets`); la pantalla
	//     vieja ya lo rotulaba «tickets total». Aquí se dice «en total».
	//   · «Con factura» se rotula «con vale»: el snapshot trae el vale
	//     (`id_solicitud_vale`/`estatus_vale`/`monto_vale`), no una factura.
	//   · «Con foto» no es un campo del snapshot: solo se sabe pidiendo la
	//     imagen. Se cuenta entre los CUATRO que están en pantalla y se dice
	//     así; si la API no responde, el número es 0 y la miniatura cae al
	//     folio, que es el respaldo honesto.
	//
	// La miniatura sale de `/api/tickets/<id>/imagen`, que es del propio
	// servidor (nunca de internet). Debajo va el folio: si la imagen tarda,
	// no está o el endpoint falla, se sigue leyendo el ticket.
	import Bento from '$lib/rediseno/Bento.svelte';
	import Celda from '$lib/rediseno/Celda.svelte';
	import Numero from '$lib/rediseno/Numero.svelte';
	import Marco from '$lib/rediseno/Marco.svelte';
	import '$lib/rediseno/tokens.css';
	import { relojKiosco } from '$lib/rediseno/relojKiosco.svelte';
	import { nombreMes } from '$lib/kiosk/format';

	interface FilaTicket {
		id_ticket?: number;
		folio?: string;
		vehiculo?: string;
		Placas?: string;
		fecha?: string;
		cliente?: string;
		id_solicitud_vale?: number | null;
	}
	interface PorVehiculo {
		vehiculo?: string;
		total_tickets?: number;
	}

	interface Props {
		/** Snapshot del kiosco. Solo se lee `tickets`. */
		datos?: any;
		/** Hora `HH:MM` ya formateada. Sin ella la toma del reloj. */
		reloj?: string;
		/** Fecha larga. Sin ella, la de hoy. */
		fecha?: string;
		/** «datos de hace 1 min». Sin ella, se calcula de `generado_en`. */
		antiguedad?: string;
		/** Posición en la rotación (`7/10`). Sin ella, un guion. */
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

	const t = $derived(datos?.tickets ?? null);
	// El snapshot vacío del arranque trae `degradado: ['cargando']` y las
	// listas en cero. Eso NO es «no hay tickets»: es «todavía no hay dato».
	const cargando = $derived((datos?.degradado ?? []).includes('cargando'));
	const sinDatos = $derived(!t || cargando);

	/** Total registrado (toda la tabla, no la semana: ver cabecera). */
	const total = $derived(sinDatos ? null : aNumero(t?.total_semana));

	const ultimos = $derived(
		sinDatos || !Array.isArray(t?.ultimos) ? [] : (t.ultimos as FilaTicket[]).filter(Boolean)
	);
	const filas = $derived(ultimos.slice(0, 4));

	/** Los que traen vale emitido entre los últimos que publica el snapshot. */
	const conVale = $derived(
		ultimos.filter((f) => (aNumero(f?.id_solicitud_vale) ?? 0) > 0).length
	);

	// ── miniaturas: qué se pudo cargar de verdad ──────────────────
	// La foto no viene en el snapshot: se sabe pidiéndola. Se anotan las que
	// cargaron y las que ya se resolvieron (bien o mal); con eso la cifra de
	// «con foto» no miente ni se queda en «cargando…» para siempre.
	let cargadas = $state<string[]>([]);
	let resueltas = $state<string[]>([]);
	const clave = (f: FilaTicket) => (f?.id_ticket == null ? '' : String(f.id_ticket));
	const conFoto = $derived(
		filas.filter((f) => {
			const k = clave(f);
			return !!k && cargadas.includes(k);
		}).length
	);
	const fotosListas = $derived(
		filas.every((f) => {
			const k = clave(f);
			return !k || resueltas.includes(k);
		})
	);
	function fotoCargo(f: FilaTicket) {
		const k = clave(f);
		if (!k) return;
		if (!cargadas.includes(k)) cargadas = [...cargadas, k];
		if (!resueltas.includes(k)) resueltas = [...resueltas, k];
	}
	function fotoFallo(e: Event, f: FilaTicket) {
		// Un src roto deja el hueco; se quita y queda el folio de debajo.
		(e.currentTarget as HTMLImageElement).remove();
		const k = clave(f);
		if (k && !resueltas.includes(k)) resueltas = [...resueltas, k];
	}

	// ── por auto: cuál carga más (toda la historia) ───────────────
	const porAuto = $derived(
		(sinDatos || !Array.isArray(t?.por_vehiculo)
			? []
			: (t.por_vehiculo as PorVehiculo[])
		)
			.filter(Boolean)
			.slice(0, 4)
	);
	const topAuto = $derived(porAuto[0] ?? null);

	const entero = (n: number) => String(Math.round(n));

	/** `2026-11-25·09:20` → `{ dia: '25', mes: 'nov', hora: '09:20' }`. Se
	 *  arma a mano: `new Date('2026-11-25')` es UTC y de noche cambiaría de
	 *  día; el snapshot ya viene en hora local del servidor. */
	function partes(iso: unknown): { dia: string; mes: string; hora: string } {
		const g = /^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2}))?/.exec(String(iso ?? ''));
		const mes = g ? Number(g[2]) : NaN;
		if (!g || !(mes >= 1 && mes <= 12)) return { dia: '—', mes: '', hora: '' };
		return {
			dia: String(Number(g[3])),
			mes: nombreMes(new Date(2026, mes - 1, 1)).slice(0, 3).toLowerCase(),
			hora: g[4] && g[5] ? `${g[4]}:${g[5]}` : ''
		};
	}

	/** La fecha del ticket más reciente de la lista (viene ordenada por Id). */
	const ultimo = $derived.by(() => {
		const p = partes(filas[0]?.fecha);
		if (!p.mes) return '';
		return `${p.dia} ${p.mes}${p.hora ? ` · ${p.hora}` : ''}`;
	});

	/** «Kia Rio 21 · SNE979 · 325363820». Una sola cadena: el espacio antes
	 *  del «·» se pierde si el separador va como texto suelto en el HTML. El
	 *  folio va aquí y no solo en el respaldo de la foto: con la imagen
	 *  cargada, si no, no habría forma de identificar el ticket. */
	function metaTicket(f: FilaTicket): string {
		const v = String(f?.vehiculo ?? '').trim() || 'Sin vehículo';
		const p = String(f?.Placas ?? '').trim();
		const folio = String(f?.folio ?? '').trim();
		return [v, p, folio].filter(Boolean).join(' · ');
	}

	/** La segunda línea de la columna del día: «NOV · 09:20». */
	function mesHora(f: FilaTicket): string {
		const p = partes(f?.fecha);
		return p.mes ? `${p.mes}${p.hora ? ` · ${p.hora}` : ''}` : '';
	}

	// Reloj, fecha y antigüedad: el mismo módulo en todas las pantallas bento.
	const k = relojKiosco(() => ({ reloj, fecha, antiguedad, generadoEn: datos?.generado_en }));

	const linea = $derived(volt ?? frase());
	function frase(): string {
		if (sinDatos) {
			return 'El snapshot todavía no trae los tickets; no invento un cero.';
		}
		if (total == null) return 'El snapshot no trae el total de tickets.';
		if (total === 0) return 'Sin tickets registrados todavía.';
		const ultimoTxt = ultimo ? `el último es del ${ultimo}` : 'sin fecha en el último';
		return `${entero(total)} ${total === 1 ? 'ticket' : 'tickets'} registrados; ${ultimoTxt}.`;
	}
</script>

<Marco
	titulo="Tickets OxxoGas"
	reloj={k.hora}
	fecha={k.fecha}
	antiguedad={k.antiguedad}
	sinFoto={datos?.pendientes?.vales ?? null}
	posicion={posicion ?? '—'}
	volt={linea}
	degradado={datos?.degradado ?? []}
>
	<Bento>
		<!-- Ancla 2×2: todos los tickets registrados y el último que llegó. -->
		<Celda area="1/1/3/3" tono="dark" rotulo="Tickets registrados" i={0}>
			<div class="cuerpo centro">
				{#if total == null}
					<div class="cifra sin">—</div>
					<div class="sub">
						{sinDatos ? 'sin datos del snapshot' : 'el snapshot no trae el total de tickets'}
					</div>
				{:else}
					<div class="cifra ancla"><Numero valor={total} formato={entero} /></div>
					<div class="sub"><b>{total === 1 ? 'ticket' : 'tickets'}</b> en total</div>
					{#if ultimo}
						<div class="delta">el último, <span>{ultimo}</span></div>
					{:else}
						<div class="delta neutro"><span>sin tickets registrados</span></div>
					{/if}
				{/if}
			</div>
		</Celda>

		<!-- Lista 2×2: los cuatro tickets más recientes, con su foto. -->
		<Celda area="1/3/3/5" rotulo="Últimos tickets" i={1}>
			<div class="lista">
				{#if filas.length === 0}
					<div class="sin-filas">
						<b>{sinDatos ? 'Sin datos todavía' : 'Sin tickets'}</b>
						<span>
							{sinDatos
								? 'El snapshot no trae el bloque de tickets.'
								: 'Se muestran los que llegan del correo o del campo.'}
						</span>
					</div>
				{:else}
					{#each filas as f, i (f?.id_ticket ?? i)}
						{@const p = partes(f?.fecha)}
						<div class="fila">
							<!-- El folio vive debajo: es el respaldo de la foto. -->
							<div class="thumb" aria-hidden="true">
								<span>{f?.folio || '—'}</span>
								{#if f?.id_ticket != null}
									<img
										src={`/api/tickets/${f.id_ticket}/imagen`}
										alt=""
										onload={() => fotoCargo(f)}
										onerror={(e) => fotoFallo(e, f)}
									/>
								{/if}
							</div>
							<div class="quien">
								<b>{f?.cliente || 'Sin cliente'}</b>
								<span>{metaTicket(f)}</span>
							</div>
							<div class="dia">
								<b>{p.dia}</b><span>{mesHora(f)}</span>
							</div>
						</div>
					{/each}
				{/if}
			</div>
		</Celda>

		<!-- 2×1: los dos estados de los tickets que están en pantalla. -->
		<Celda area="3/1/4/3" rotulo="Con vale · con foto" i={2}>
			<div class="cuerpo">
				{#if sinDatos || ultimos.length === 0}
					<div class="sin-dato">
						<b>{sinDatos ? 'Sin datos todavía' : 'Sin tickets'}</b>
						<span>
							{sinDatos
								? 'El snapshot no trae el bloque de tickets.'
								: 'No hay vales ni fotos que contar todavía.'}
						</span>
					</div>
				{:else}
					<div class="par">
						<div class="mitad">
							<div class="cifra">{conVale}</div>
							<div class="sub">
								<b>con vale</b>
								{ultimos.length === 1 ? 'del único' : `de los últimos ${ultimos.length}`}
							</div>
						</div>
						<div class="raya" aria-hidden="true"></div>
						<div class="mitad">
							{#if !fotosListas}
								<div class="cifra pend">—</div>
							{:else}
								<div class="cifra">{conFoto}</div>
							{/if}
							<div class="sub">
								<b>con foto</b>
								{filas.length === 1 ? 'del único en pantalla' : `de los ${filas.length} en pantalla`}
							</div>
						</div>
					</div>
				{/if}
			</div>
		</Celda>

		<!-- Cifra 1×1: el auto con más tickets en la historia del registro. -->
		<Celda area="3/3/4/4" rotulo="Auto que más carga" i={3}>
			<div class="cuerpo">
				{#if !topAuto}
					<div class="cifra sin">—</div>
					<div class="sub">{sinDatos ? 'sin datos del snapshot' : 'sin tickets registrados'}</div>
				{:else}
					<div class="cifra">{aNumero(topAuto?.total_tickets) ?? 0}</div>
					<div class="sub"><b>{topAuto?.vehiculo || 'Sin vehículo'}</b></div>
					<div class="nota">tickets en total</div>
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
	/* «Con foto» mientras se resuelven las cuatro imágenes: no es un cero. */
	.cifra.pend {
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
		font-size: 20px;
		font-weight: 800;
		color: #fff;
		opacity: 0.85;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.delta.neutro {
		color: #f7f3ea;
	}
	.delta span {
		font-weight: 600;
		opacity: 0.6;
	}

	.nota {
		font-size: 20px;
		font-weight: 600;
		opacity: 0.55;
	}

	/* ── lista de tickets ─────────────────────────────────────── */
	.lista {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
	}
	.fila {
		flex: 1 1 0;
		max-height: 130px;
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
	/* La miniatura: la foto del ticket encima y el folio debajo de respaldo. */
	.thumb {
		position: relative;
		width: 112px;
		height: 88px;
		flex: 0 0 112px;
		border-radius: 12px;
		background: #e6ddcd;
		color: #6d6455;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
		font-size: 20px;
		font-weight: 900;
		letter-spacing: -0.6px;
		font-variant-numeric: tabular-nums;
	}
	.thumb img {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: cover;
		object-position: center;
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
		opacity: 0.55;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	/* El día en columna: se lee desde el otro lado del pasillo. */
	.dia {
		flex: 0 0 auto;
		display: flex;
		flex-direction: column;
		align-items: center;
		min-width: 124px;
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
		letter-spacing: 0.6px;
		text-transform: uppercase;
		opacity: 0.45;
		font-variant-numeric: tabular-nums;
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

	/* ── dos estados (2×1) ────────────────────────────────────── */
	.par {
		display: flex;
		align-items: center;
		gap: 28px;
		min-height: 0;
	}
	.mitad {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		align-items: flex-start;
	}
	.mitad .cifra {
		margin-bottom: 2px;
	}
	.raya {
		width: 1px;
		height: 116px;
		flex: 0 0 1px;
		background: rgba(18, 20, 26, 0.12);
	}
</style>
