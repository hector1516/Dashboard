<script lang="ts">
	// Pantalla de comprobantes pendientes, en la retícula bento.
	//
	// Tres estados, con el mismo esqueleto:
	//   · con pendientes  → ancla ROJA con el número de vales de la temporada
	//   · sin pendientes  → ancla de tinta con «Todo al día» en verde
	//   · sin bloque      → snapshot viejo: un «—», nunca un cero fingido
	//
	// La lista NO se queda vacía: son los últimos 6 vales lleven foto o no.
	// El pendiente lleva sus días en grande y en color (7+ rojo, 3-6 ámbar,
	// 0-2 gris); el cerrado va atenuado con «✓ con foto». Así se lee como una
	// bandeja de trabajo y no como un muro de la vergüenza.
	//
	// RESERVA DE VOLT: la celda 3/4/4/5 de la retícula (la esquina inferior
	// derecha) no se usa. La placa de Volt mide 112 px y vive a 18 px del
	// borde, y su globo se apila encima hasta ~250 px sobre el pie; por eso la
	// lista acaba dos filas más arriba. Al no dibujar nada ahí, la placa y el
	// globo no tapan ningún dato.
	//
	// Los datos salen del snapshot (`datos.pendientes`). El bloque es
	// OPCIONAL: tras un deploy, el primer ciclo del snapshotter todavía no lo
	// trae. Todo se lee con `?.` y con valores por defecto.
	import { onMount } from 'svelte';
	import Bento from '$lib/rediseno/Bento.svelte';
	import Celda from '$lib/rediseno/Celda.svelte';
	import Numero from '$lib/rediseno/Numero.svelte';
	import Marco from '$lib/rediseno/Marco.svelte';
	import '$lib/rediseno/tokens.css';
	import { colorEdad, dinero } from '$lib/rediseno/formato';
	import { haceCuanto, iniciales, nombreDia, nombreMes } from '$lib/kiosk/format';

	interface Fila {
		nombre?: string;
		placa?: string;
		/** null = el vale no tiene monto emitido (no es cero). */
		monto?: number | null;
		dias?: number;
		cerrado?: boolean;
		/** Foto real de la persona (`/media/usuarios/u<Id>.jpg`); el
		 *  snapshotter la resuelve y no la pone si el archivo no existe. */
		foto?: string | null;
	}

	interface Props {
		/** Snapshot del kiosco. Solo se lee `pendientes`. */
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

	const p = $derived(datos?.pendientes ?? null);
	// Sin bloque no se sabe nada: no es «todo al día» ni un cero. Se muestra
	// «—» y se dice que el snapshot no lo trae (regla: nunca ceros falsos).
	const sinDatos = $derived(!p);
	const vales = $derived(Math.max(0, Math.round(Number(p?.vales ?? 0) || 0)));
	const monto = $derived(Number(p?.monto ?? 0) || 0);
	const desde = $derived(typeof p?.desde === 'string' ? p.desde : '');
	const filas = $derived(
		(Array.isArray(p?.ultimos) ? (p.ultimos as Fila[]) : []).slice(0, 6)
	);
	const cerrados = $derived(filas.filter((f) => f?.cerrado).length);
	const cobertura = $derived(
		filas.length ? Math.round((cerrados / filas.length) * 100) : null
	);
	// «El más viejo» solo se puede afirmar de los que vienen en la lista: el
	// resto de pendientes no está en el bloque. Si no hay ninguno, se calla.
	const masViejo = $derived(
		filas.reduce((m, f) => (f?.cerrado ? m : Math.max(m, diasDe(f?.dias))), -1)
	);
	const corte = $derived(desdeTexto(desde));

	const entero = (n: number) => String(Math.round(n));
	const diasDe = (n: number | undefined) => Math.max(0, Math.round(Number(n ?? 0) || 0));

	/** `2026-11-23` → «lunes 23». Se arma a mano: `new Date('2026-11-23')` es
	 *  UTC y de noche cambiaría de día. */
	function desdeTexto(iso: string): string {
		const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso ?? '');
		if (!m) return '';
		const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
		if (Number.isNaN(d.getTime())) return '';
		return `${nombreDia(d).toLowerCase()} ${d.getDate()}`;
	}

	// El marco es tonto a propósito: el reloj y la fecha se arman aquí para
	// que la pantalla se pueda montar con solo `datos`. Se escriben después
	// de hidratar (si no, el HTML estático llevaría la hora del build).
	let ahora = $state<Date | null>(null);
	onMount(() => {
		ahora = new Date();
		const t = setInterval(() => (ahora = new Date()), 1000);
		return () => clearInterval(t);
	});

	const hora = $derived(
		reloj ??
			(ahora
				? `${String(ahora.getHours()).padStart(2, '0')}:${String(ahora.getMinutes()).padStart(2, '0')}`
				: '--:--')
	);
	const diaLargo = $derived(
		fecha ??
			(ahora
				? `${nombreDia(ahora).toLowerCase()} ${ahora.getDate()} de ${nombreMes(ahora).toLowerCase()}`
				: '')
	);
	const edad = $derived(antiguedad ?? antiguedadDe(datos?.generado_en, ahora));

	function antiguedadDe(iso: string | undefined, cuando: Date | null): string {
		if (!cuando) return '';
		const h = haceCuanto(iso, cuando.getTime());
		if (h === '—') return 'sin datos';
		if (h === 'ahora') return 'datos al día';
		return `datos de ${h}`;
	}

	const linea = $derived(volt ?? frase(sinDatos, vales));
	function frase(sin: boolean, n: number): string {
		if (sin) return 'El snapshot todavía no trae el bloque de comprobantes; no invento un cero.';
		if (n === 0) return 'Todo al día: nada de esta temporada quedó sin comprobar.';
		return `${n === 1 ? 'Un vale' : `${n} vales`} de esta temporada siguen sin comprobante.`;
	}
</script>

<Marco
	titulo="Faltan comprobantes"
	reloj={hora}
	fecha={diaLargo}
	antiguedad={edad}
	sinFoto={sinDatos ? null : vales}
	posicion={posicion ?? '—'}
	volt={linea}
>
	<Bento>
		<!-- Ancla 2×2: el número más grande de la pantalla. -->
		<Celda area="1/1/3/3" tono={vales > 0 && !sinDatos ? 'red' : 'dark'} rotulo="Vales sin comprobar" i={0}>
			<div class="cuerpo centro">
				{#if sinDatos}
					<div class="cifra sin">—</div>
					<div class="sub">sin datos del snapshot</div>
				{:else if vales > 0}
					<div class="cifra ancla"><Numero valor={vales} formato={entero} /></div>
					<div class="sub">
						<b>{dinero(monto)}</b>{#if corte} · desde el {corte}{/if}
					</div>
					{#if masViejo > 0}
						<div class="delta">
							el más viejo de la lista lleva {masViejo === 1 ? '1 día' : `${masViejo} días`}
						</div>
					{/if}
				{:else}
					<div class="cifra todo">Todo al día</div>
					<div class="sub">0 vales sin comprobar</div>
				{/if}
			</div>
		</Celda>

		<!-- Lista 2×2: SIEMPRE los últimos vales, cerrados incluidos. -->
		<Celda area="1/3/3/5" rotulo="Últimos vales" i={1}>
			<div class="lista">
				{#if filas.length === 0}
					<div class="sin-filas">
						<b>{sinDatos ? 'Sin datos todavía' : 'Sin vales todavía'}</b>
						<span>
							{sinDatos
								? 'El snapshot no trae el bloque de comprobantes.'
								: 'La lista se llena con los últimos vales de la temporada.'}
						</span>
					</div>
				{:else}
					{#each filas as f}
						<div class="fila" class:ok={f.cerrado}>
							<!-- Foto real y, debajo, las iniciales: si el archivo se
							     perdió (ruta vieja) la imagen se quita sola y queda el
							     círculo con iniciales. -->
							<div class="ava" aria-hidden="true">
								{#if f.foto}
									<img
										src={f.foto}
										alt=""
										onerror={(e) => (e.currentTarget as HTMLImageElement).remove()}
									/>
								{/if}
								<span>{iniciales(f.nombre)}</span>
							</div>
							<div class="quien">
								<b>{f.nombre || 'Sin nombre'}</b>
								<span>
									{#if f.placa}{f.placa} · {/if}{f.monto == null
										? 'sin monto'
										: dinero(f.monto)}
								</span>
							</div>
							{#if f.cerrado}
								<div class="estado">✓ con foto</div>
							{:else}
								<div class="dias {colorEdad(diasDe(f.dias))}">
									<span>{diasDe(f.dias)}</span><small
										>{diasDe(f.dias) === 1 ? 'día' : 'días'}</small
									>
								</div>
							{/if}
						</div>
					{/each}
				{/if}
			</div>
		</Celda>

		<!-- Cifra 2×1: cuántos cerrados hay entre los de la lista, y cuáles. -->
		<Celda area="3/1/4/3" rotulo="Cerrados" i={2}>
			<div class="cuerpo">
				<div class="en-linea">
					{#if sinDatos}
						<div class="cifra sin">—</div>
					{:else}
						<div class="cifra">{cerrados}</div>
					{/if}
					<div class="nota">
						{#if sinDatos}
							<span>sin datos del snapshot</span>
						{:else}
							<!-- «de la lista»: `ultimos` es un TOP 6 sin filtro de fecha,
							     así que no se puede afirmar «esta semana». -->
							<b>de la lista</b>
							<span>
								{filas.length
									? `de los últimos ${filas.length} vales`
									: 'sin vales en la temporada'}
							</span>
						{/if}
					</div>
				</div>
				{#if filas.length}
					<!-- Una barra por vale de la lista: verde el cerrado, y el
					     pendiente con el mismo color de edad que su fila. -->
					<div class="pista" aria-hidden="true">
						{#each filas as f}
							<i class={f.cerrado ? 'cerrado' : colorEdad(diasDe(f.dias))}></i>
						{/each}
					</div>
				{/if}
			</div>
		</Celda>

		<!-- Cifra 1×1: el porcentaje de la lista que ya lleva foto. -->
		<Celda area="3/3/4/4" rotulo="Cobertura" i={3}>
			<div class="cuerpo">
				{#if cobertura == null}
					<div class="cifra sin">—</div>
				{:else}
					<div class="cifra">{cobertura}<span class="pct">%</span></div>
				{/if}
				<div class="sub">con foto</div>
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
	/* Estado bueno: la tinta del ancla y la frase en verde de apoyo. No se
	   pinta una tarjeta verde entera porque el verde del sistema es «apoyo
	   apagado», no un fondo (spec §5.4). */
	.cifra.todo {
		font-size: 112px;
		letter-spacing: -4px;
		line-height: 0.95;
		color: #7fe3cf;
	}
	.pct {
		font-size: 0.38em;
		vertical-align: 0.5em;
		letter-spacing: 0;
		margin-left: 2px;
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
		font-size: 20px;
		font-weight: 800;
		color: #fff;
		opacity: 0.85;
	}

	/* ── lista de vales ───────────────────────────────────────── */
	.lista {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
	}
	.fila {
		flex: 1 1 0;
		max-height: 92px;
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
	/* El cerrado se atenúa: sigue en la bandeja, pero ya no pide nada. */
	.fila.ok {
		opacity: 0.55;
	}
	.ava {
		position: relative;
		width: 62px;
		height: 62px;
		flex: 0 0 62px;
		border-radius: 50%;
		background: #e6ddcd;
		color: #6d6455;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
		font-size: 24px;
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
	.dias {
		display: flex;
		align-items: baseline;
		gap: 6px;
		font-size: 54px;
		font-weight: 900;
		letter-spacing: -2.2px;
	}
	.dias small {
		font-size: 20px;
		font-weight: 700;
		letter-spacing: 0;
		opacity: 0.6;
	}
	.rojo {
		color: var(--k-rojo);
	}
	.ambar {
		color: var(--k-ambar);
	}
	.gris {
		color: #8a8578;
	}
	.estado {
		font-size: 20px;
		font-weight: 800;
		color: var(--k-verde);
		white-space: nowrap;
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

	/* ── cifra ancha (2×1) ────────────────────────────────────── */
	.en-linea {
		display: flex;
		align-items: center;
		gap: 28px;
	}
	.en-linea .cifra {
		margin-bottom: 0;
	}
	.nota {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.nota b {
		font-size: 24px;
		font-weight: 700;
	}
	.nota span {
		font-size: 20px;
		font-weight: 600;
		opacity: 0.55;
	}
	.pista {
		display: flex;
		gap: 6px;
	}
	.pista i {
		flex: 1;
		height: 14px;
		border-radius: 4px;
		background: #8a8578;
	}
	.pista i.cerrado {
		background: var(--k-verde);
		opacity: 0.55;
	}
	.pista i.rojo {
		background: var(--k-rojo);
	}
	.pista i.ambar {
		background: var(--k-ambar);
	}
	.pista i.gris {
		background: #c9beb0;
	}
</style>
