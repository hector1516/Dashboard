<script lang="ts">
	// Clima de la oficina, en la retícula bento.
	//
	// Seis piezas en once celdas (la 12.ª es el rincón de Volt):
	//   · ancla 2×2: la temperatura de ahora, con su icono y la descripción
	//   · 2×1 «Hoy» y 2×1 «Mañana»: máxima y mínima de cada día
	//   · 1×1 lluvia (probabilidad), 1×1 viento, 1×1 humedad
	//
	// DESVÍO DEL BRIEF — «2×1 próximos 3 días»: el snapshot NO publica un
	// tercer día. `datos.clima` trae `actual`, `hoy` y `manana`, y nada más
	// (`src/lib/kiosk/types.ts`); inventar el día 3 sería un cero falso con
	// formato de pronóstico. Se pintan los DOS días que existen, cada uno en su
	// 2×1 apilado a la derecha del ancla: son las mismas dos celdas que pedía
	// el brief y además llenan la retícula sin dejar un hueco en medio.
	//
	// RESERVA DE VOLT: la celda 3/4/4/5 (la esquina inferior derecha) no se
	// usa. La placa mide 112 px a 18 px del borde y su globo se apila encima;
	// al no dibujar nada ahí, no tapan ningún dato.
	//
	// Sin dato no hay cero: si `clima.actual.temperatura` viene `null` (el
	// snapshot del arranque, o el servidor sin salida a internet en el primer
	// ciclo) las celdas dicen «—» y Volt lo explica. Si el snapshot trae la
	// última lectura buena con `degradado: ['clima']`, el dato SÍ es real: se
	// pinta, y el chip ámbar del marco avisa de que es la lectura anterior.
	import Bento from '$lib/rediseno/Bento.svelte';
	import Celda from '$lib/rediseno/Celda.svelte';
	import Marco from '$lib/rediseno/Marco.svelte';
	import '$lib/rediseno/tokens.css';
	import { relojKiosco } from '$lib/rediseno/relojKiosco.svelte';
	import { haceCuanto } from '$lib/kiosk/format';

	interface Props {
		/** Snapshot del kiosco. Solo se lee `clima`. */
		datos?: any;
		/** Hora `HH:MM` ya formateada. Sin ella la toma del reloj. */
		reloj?: string;
		/** Fecha larga. Sin ella, la de hoy. */
		fecha?: string;
		/** «datos de hace 1 min». Sin ella, se calcula de `generado_en`. */
		antiguedad?: string;
		/** Posición en la rotación (`2/10`). Sin ella, un guion. */
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

	const c = $derived(datos?.clima ?? null);
	const ahora = $derived(c?.actual ?? null);
	const hoy = $derived(c?.hoy ?? null);
	const manana = $derived(c?.manana ?? null);

	/** Sin temperatura no hay pantalla de clima: ni «0°» ni un icono fingido. */
	const sinDatos = $derived(!c || aNumero(ahora?.temperatura) == null);

	const temp = $derived(aNumero(ahora?.temperatura));
	const humedad = $derived(aNumero(ahora?.humedad));
	const viento = $derived(aNumero(ahora?.viento));
	const lluviaHoy = $derived(aNumero(hoy?.prob_lluvia));
	const lluviaManana = $derived(aNumero(manana?.prob_lluvia));
	const descripcion = $derived(String(ahora?.descripcion ?? '').trim());
	const icono = $derived(String(ahora?.icono ?? '').trim());

	/** «19°»: entero, igual que la temperatura de la barra del marco. El
	 *  kiosco no muestra «18.7°» a 3 metros. */
	function grados(n: number | null): string {
		return n == null ? '—' : String(Math.round(n));
	}

	/** Cuándo se leyó el clima. `leido_en` es de la última lectura buena y
	 *  puede ser MUCHO más viejo que el snapshot (si Open-Meteo falla, el
	 *  servidor re-sirve la última lectura y marca `degradado: ['clima']`).
	 *  Por eso se dice aquí: el chip del marco habla del snapshot, no del clima.
	 *  El reloj se refresca cada 30 s para que la frase no se congele si la
	 *  pantalla queda fija con `?pantalla=clima`. */
	let ahoraMs = $state(Date.now());
	$effect(() => {
		const t = setInterval(() => (ahoraMs = Date.now()), 30_000);
		return () => clearInterval(t);
	});
	const leido = $derived.by(() => {
		const h = haceCuanto(c?.leido_en, ahoraMs);
		if (h === '—') return '';
		return h === 'ahora' ? 'ahora' : h;
	});

	/** «19° y despejado; hoy entre 9° y 19°.» Con lluvia, se avisa. */
	function frase(): string {
		if (sinDatos) {
			return 'El snapshot todavía no trae el clima; no invento una temperatura.';
		}
		const donde = descripcion ? ` y ${descripcion.toLowerCase()}` : '';
		const partes: string[] = [];
		if (hoy?.min != null && hoy?.max != null) {
			partes.push(`hoy entre ${grados(aNumero(hoy.min))}° y ${grados(aNumero(hoy.max))}°`);
		}
		if (lluviaHoy != null && lluviaHoy >= 30) {
			partes.push(`${Math.round(lluviaHoy)}% de lluvia`);
		}
		const cola = partes.length ? `; ${partes.join(' y ')}` : '';
		return `${grados(temp)}°${donde}${cola}.`;
	}

	// Reloj, fecha y antigüedad: el mismo módulo en todas las pantallas bento.
	const k = relojKiosco(() => ({ reloj, fecha, antiguedad, generadoEn: datos?.generado_en }));

	const linea = $derived(volt ?? frase());
</script>

<Marco
	titulo="Clima"
	reloj={k.hora}
	fecha={k.fecha}
	antiguedad={k.antiguedad}
	temperatura={datos?.clima?.actual?.temperatura}
	posicion={posicion ?? '—'}
	volt={linea}
	degradado={datos?.degradado ?? []}
>
	<Bento>
		<!-- Ancla 2×2: la temperatura de ahora, el icono y el estado del cielo.
		     Lleva el dibujo isométrico de la oficina como marca de agua, muy
		     tenue y al pie: sobre la tinta se ve el trazo, no una foto, y la
		     cifra y el texto quedan por delante. -->
		<Celda
			area="1/1/3/3"
			tono="dark"
			rotulo="Ahora en Monterrey"
			i={0}
			marcaAgua="/images/oficina-eccsa.webp"
			fondo
		>
			<div class="cuerpo centro">
				{#if sinDatos}
					<div class="cifra sin sobre-tinta">—</div>
					<div class="sub">sin datos del clima</div>
				{:else}
					<div class="temp">
						{#if icono}<span class="ico" aria-hidden="true">{icono}</span>{/if}
						<span class="tempnum"
							>{grados(temp)}<span class="deg">°C</span></span
						>
					</div>
					<div class="sub">
						<b>{descripcion || 'Sin descripción'}</b>
					</div>
					<div class="delta">
						{#if leido}
							leído {leido}
						{:else}
							sin hora de lectura
						{/if}
						{#if ahora?.es_dia === false} · de noche{/if}
					</div>
				{/if}
			</div>
		</Celda>

		<!-- 2×1: el día de hoy. -->
		<Celda area="1/3/2/5" rotulo="Hoy" i={1}>
			<div class="cuerpo centro">
				{#if aNumero(hoy?.max) == null && aNumero(hoy?.min) == null}
					<div class="cifra sin">—</div>
					<div class="sub">sin pronóstico de hoy</div>
				{:else}
					<div class="rango">
						<span class="max">{grados(aNumero(hoy?.max))}°</span>
						<span class="min">/ {grados(aNumero(hoy?.min))}°</span>
					</div>
					<div class="sub">máxima y mínima</div>
				{/if}
			</div>
		</Celda>

		<!-- 2×1: el día de mañana. -->
		<Celda area="2/3/3/5" rotulo="Mañana" i={2}>
			<div class="cuerpo centro">
				{#if aNumero(manana?.max) == null && aNumero(manana?.min) == null}
					<div class="cifra sin">—</div>
					<div class="sub">sin pronóstico de mañana</div>
				{:else}
					<div class="rango">
						<span class="max">{grados(aNumero(manana?.max))}°</span>
						<span class="min">/ {grados(aNumero(manana?.min))}°</span>
					</div>
					<div class="sub">máxima y mínima</div>
				{/if}
			</div>
		</Celda>

		<!-- 1×1: probabilidad de lluvia de hoy, con la de mañana de contexto. -->
		<Celda area="3/1/4/2" rotulo="Lluvia hoy" i={3}>
			<div class="cuerpo">
				{#if lluviaHoy == null}
					<div class="cifra sin">—</div>
					<div class="sub">sin dato de lluvia</div>
				{:else}
					<div class="cifra">{Math.round(lluviaHoy)}<span class="pct">%</span></div>
					<div class="sub">
						{#if lluviaManana != null}
							mañana <b>{Math.round(lluviaManana)}%</b>
						{:else}
							probabilidad de lluvia
						{/if}
					</div>
				{/if}
			</div>
		</Celda>

		<!-- 1×1: viento de ahora. -->
		<Celda area="3/2/4/3" rotulo="Viento" i={4}>
			<div class="cuerpo">
				{#if viento == null}
					<div class="cifra sin">—</div>
					<div class="sub">sin dato de viento</div>
				{:else}
					<div class="cifra">{grados(viento)}<span class="uni">km/h</span></div>
					<div class="sub">viento ahora</div>
				{/if}
			</div>
		</Celda>

		<!-- 1×1: humedad relativa. -->
		<Celda area="3/3/4/4" rotulo="Humedad" i={5}>
			<div class="cuerpo">
				{#if humedad == null}
					<div class="cifra sin">—</div>
					<div class="sub">sin dato de humedad</div>
				{:else}
					<div class="cifra">{Math.round(humedad)}<span class="pct">%</span></div>
					<div class="sub">humedad relativa</div>
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

	/* ── ancla: temperatura ───────────────────────────────────── */
	.temp {
		display: flex;
		align-items: center;
		gap: 16px;
		min-width: 0;
	}
	/* 176 px y no los 214 del token: «19°C» son pocos glifos y a 214 px la
	   cifra se salía de la celda con el icono al lado. Sigue siendo lo más
	   grande de la pantalla. */
	.tempnum {
		font-size: 176px;
		font-weight: 900;
		line-height: 0.92;
		letter-spacing: -7px;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}
	.deg {
		font-size: 0.3em;
		letter-spacing: 0;
		vertical-align: 0.62em;
		margin-left: 4px;
		opacity: 0.8;
	}
	.ico {
		font-size: 120px;
		line-height: 1;
		flex: 0 0 auto;
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
	/* Sin dato: un guion chico y apagado, no una barra negra de 96 px. */
	.cifra.sin {
		font-size: 64px;
		letter-spacing: 0;
		opacity: 0.28;
	}
	/* Sobre la tinta del ancla el guion necesita más opacidad para leerse. */
	.cifra.sin.sobre-tinta {
		opacity: 0.6;
	}
	.pct {
		font-size: 0.38em;
		vertical-align: 0.5em;
		letter-spacing: 0;
		margin-left: 2px;
	}
	.uni {
		font-size: 0.26em;
		letter-spacing: 0;
		margin-left: 8px;
		font-weight: 800;
		opacity: 0.62;
	}
	/* Máxima grande y mínima a su lado, en la misma línea de base. */
	.rango {
		display: flex;
		align-items: baseline;
		gap: 10px;
		min-width: 0;
		margin-bottom: 6px;
	}
	.rango .max {
		font-size: var(--k-f-cifra);
		font-weight: 900;
		line-height: 0.92;
		letter-spacing: -4px;
		font-variant-numeric: tabular-nums;
	}
	.rango .min {
		font-size: 44px;
		font-weight: 800;
		letter-spacing: -1px;
		font-variant-numeric: tabular-nums;
		opacity: 0.62;
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
		font-weight: 700;
		opacity: 0.6;
	}
</style>
