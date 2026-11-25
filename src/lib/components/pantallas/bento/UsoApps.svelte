<script module lang="ts">
	/**
	 * Última lectura buena del resumen de uso, compartida entre montajes. Vive
	 * en el módulo (y no en el estado del componente) a propósito: sobrevive a
	 * la rotación, que desmonta la pantalla cada 45 s, y evita una consulta
	 * pesada a la BD por vuelta.
	 */
	let cache: { datos: any; en: number } | null = null;
	const CACHE_MS = 60_000;
</script>

<script lang="ts">
	// Uso de las apps (Admon y Field), en la retícula bento.
	//
	// Cuatro piezas en once celdas (la 12.ª es el rincón de Volt):
	//   · ancla 2×2: la app más usada, con sus llamadas
	//   · lista 2×2: quiénes son los que más la usan
	//   · serie 2×1: llamadas por app (barras)
	//   · 1×1: usuarios activos
	//
	// DE DÓNDE SALEN LOS DATOS: no están en el snapshot. Se piden a
	// `/api/uso/resumen`, que es del PROPIO servidor del kiosco (lee
	// `HUB_ApiUsage` y devuelve JSON). No hay ninguna petición a internet; si
	// el endpoint no responde, la pantalla lo dice y no pinta ceros.
	//
	// DESVÍOS DEL BRIEF:
	//   · «minutos por app»: el resumen publica LLAMADAS por app, no minutos
	//     (no hay campo de duración agregado). Las barras dicen «llamadas».
	//   · «sesiones»: tampoco existe el concepto de sesión en `HUB_ApiUsage`;
	//     la cifra chica es «usuarios activos» (distintos en 7 días), que es
	//     el otro dato real del endpoint.
	//
	// RESERVA DE VOLT: la celda 3/4/4/5 (la esquina inferior derecha) no se
	// usa. La placa mide 112 px a 18 px del borde y su globo se apila encima;
	// al no dibujar nada ahí, no tapan ningún dato.
	import { onMount } from 'svelte';
	import Bento from '$lib/rediseno/Bento.svelte';
	import Celda from '$lib/rediseno/Celda.svelte';
	import Marco from '$lib/rediseno/Marco.svelte';
	import '$lib/rediseno/tokens.css';
	import { relojKiosco } from '$lib/rediseno/relojKiosco.svelte';

	interface UsuarioUso {
		usuario?: string;
		llamadas?: number;
	}

	interface Props {
		/** Snapshot del kiosco: solo se usa para los chips del marco. */
		datos?: any;
		/** Hora `HH:MM` ya formateada. Sin ella la toma del reloj. */
		reloj?: string;
		/** Fecha larga. Sin ella, la de hoy. */
		fecha?: string;
		/** «datos de hace 1 min». Sin ella, se calcula de `generado_en`. */
		antiguedad?: string;
		/** Posición en la rotación (`9/10`). Sin ella, un guion. */
		posicion?: string;
		/** Frase del pie. Sin ella, se arma del dato. */
		volt?: string;
	}
	let { datos, reloj, fecha, antiguedad, posicion, volt }: Props = $props();

	/** El resumen de uso. `null` = todavía no llegó (o no responde). */
	let uso = $state<any>(null);
	let cargando = $state(true);
	/** La última petición falló. Con `uso` en mano, el dato bueno se conserva. */
	let fallo = $state(false);

	async function cargar() {
		// La rotación remonta la pantalla cada 45 s y el resumen pega en la BD
		// (es lo más caro del kiosco): si la última lectura tiene menos de un
		// minuto se reusa en vez de volver a pedirla.
		if (cache && Date.now() - cache.en < CACHE_MS) {
			uso = cache.datos;
			fallo = false;
			cargando = false;
			return;
		}
		try {
			// El endpoint pega en la BD y en producción puede tardar más de lo que
			// dura la pantalla (45 s). Sin este tope, el kiosco se quedaría
			// «leyendo» todo el turno; a los 12 s se dice que no responde.
			const ctl = new AbortController();
			const tope = setTimeout(() => ctl.abort(), 12_000);
			let r: Response;
			try {
				r = await fetch('/api/uso/resumen', { cache: 'no-store', signal: ctl.signal });
			} finally {
				clearTimeout(tope);
			}
			if (!r.ok) throw new Error(String(r.status));
			const j = await r.json();
			// El endpoint devuelve `{error}` con 200 en algunos fallos: eso no es
			// un resumen, es un error disfrazado.
			if (!j || typeof j !== 'object' || 'error' in j) throw new Error('forma');
			uso = j;
			cache = { datos: j, en: Date.now() };
			fallo = false;
		} catch {
			fallo = true;
		}
		cargando = false;
	}

	onMount(() => {
		cargar();
		const t = setInterval(cargar, 60_000);
		return () => clearInterval(t);
	});

	/** Un número del resumen, o `null`. `0` es un dato; ausente no lo es. */
	function aNumero(v: any): number | null {
		if (v === null || v === undefined || v === '') return null;
		const n = Number(v);
		return Number.isFinite(n) ? n : null;
	}

	const nf = new Intl.NumberFormat('es-MX');
	const cuenta = (n: number | null) => (n == null ? '—' : nf.format(Math.round(n)));

	const sinDatos = $derived(!uso);
	const total = $derived(aNumero(uso?.total_7d));
	const activos = $derived(aNumero(uso?.activos_7d));

	/** `admon` → «Admon», `field` → «Field»; una app nueva se capitaliza. */
	function nombreApp(clave: string): string {
		const t = String(clave ?? '').trim();
		if (!t) return 'Sin nombre';
		return t.charAt(0).toUpperCase() + t.slice(1);
	}

	/** Llamadas por app, de mayor a menor. Las de 0 no se dibujan como barra. */
	const apps = $derived.by(() => {
		const pa = uso?.por_app;
		if (!pa || typeof pa !== 'object') return [] as { clave: string; nombre: string; n: number }[];
		return Object.entries(pa)
			.map(([clave, v]) => ({ clave, nombre: nombreApp(clave), n: aNumero(v) ?? 0 }))
			.filter((a) => a.n > 0)
			.sort((a, b) => b.n - a.n)
			.slice(0, 3);
	});
	const topApp = $derived(apps[0] ?? null);
	const maxApp = $derived(Math.max(1, ...apps.map((a) => a.n)));
	/** La parte del total que se lleva la app más usada. */
	const parteTop = $derived(
		topApp && total && total > 0 ? Math.round((topApp.n / total) * 100) : null
	);

	const topUsuarios = $derived(
		(Array.isArray(uso?.top_usuarios) ? (uso.top_usuarios as UsuarioUso[]) : [])
			.filter((u) => u && (aNumero(u.llamadas) ?? 0) > 0)
			.slice(0, 4)
	);

	const inactivos = $derived(Array.isArray(uso?.inactivos) ? uso.inactivos.length : null);

	/**
	 * Cómo se llama el «no hay dato»: no es lo mismo un resumen que todavía no
	 * llega que uno que no responde. La pantalla lo dice con el verbo correcto.
	 */
	const tituloSinUso = $derived(fallo ? 'Sin respuesta' : 'Sin datos todavía');
	const motivoSinUso = $derived(
		fallo ? 'El resumen de uso no responde.' : 'El resumen de uso no ha llegado.'
	);

	/** La parte del total que se lleva un usuario («12%» o «<1%»). */
	function parte(n: number | null): string | null {
		if (n == null || !total || total <= 0) return null;
		const pct = Math.round((n / total) * 100);
		if (pct === 0 && n > 0) return '<1% de las llamadas';
		return `${pct}% de las llamadas`;
	}

	// Reloj, fecha y antigüedad: el mismo módulo en todas las pantallas bento.
	const k = relojKiosco(() => ({ reloj, fecha, antiguedad, generadoEn: datos?.generado_en }));

	function frase(): string {
		if (sinDatos) {
			return cargando
				? 'Todavía no llega el resumen de uso de las apps.'
				: 'El resumen de uso no responde; el kiosco no inventa ceros.';
		}
		if (!total) return 'Nadie ha usado Admon ni Field en los últimos 7 días.';
		if (!topApp) return `${cuenta(total)} llamadas en 7 días, sin desglose por app.`;
		const cola =
			inactivos && inactivos > 0
				? `; ${inactivos} ${inactivos === 1 ? 'persona sigue' : 'personas siguen'} sin usarlas`
				: '';
		return `${topApp.nombre} se lleva ${parteTop ?? '—'}% de las ${cuenta(total)} llamadas en 7 días${cola}.`;
	}

	const linea = $derived(volt ?? frase());
</script>

<Marco
	titulo="Uso de apps"
	reloj={k.hora}
	fecha={k.fecha}
	antiguedad={k.antiguedad}
	sinFoto={datos?.pendientes?.vales ?? null}
	posicion={posicion ?? '—'}
	volt={linea}
	degradado={datos?.degradado ?? []}
>
	<Bento>
		<!-- Ancla 2×2: la app más usada. La palabra es la cifra del ancla: lo
		     que el pasillo tiene que leer es «Admon», no un número de seis
		     dígitos que no cabe a 214 px. -->
		<Celda area="1/1/3/3" tono="dark" rotulo="App más usada · 7 días" i={0}>
			<div class="cuerpo centro">
				{#if sinDatos}
					<div class="cifra sin sobre-tinta">—</div>
					<div class="sub">
						{cargando ? 'leyendo el uso de las apps' : 'el resumen de uso no responde'}
					</div>
				{:else if !total}
					<div class="cifra sin-uso sobre-tinta">Sin uso</div>
					<div class="sub">0 llamadas en 7 días</div>
				{:else if !topApp}
					<div class="cifra ancla"><span class="texto">—</span></div>
					<div class="sub">sin desglose por app</div>
				{:else}
					<div class="cifra ancla"><span class="texto">{topApp.nombre}</span></div>
					<div class="sub">
						<b>{cuenta(topApp.n)} llamadas</b> en 7 días
					</div>
					<div class="delta">
						{#if parteTop != null && parteTop !== 100}
							{parteTop}% de las {cuenta(total)} del periodo
						{:else}
							con {cuenta(activos)} usuarios activos
						{/if}
					</div>
				{/if}
			</div>
		</Celda>

		<!-- Lista 2×2: quién usa más las apps. -->
		<Celda area="1/3/3/5" rotulo="Quién usa más · 7 días" i={1}>
			<div class="lista">
				{#if topUsuarios.length === 0}
					<div class="sin-filas">
						<b>{sinDatos ? tituloSinUso : 'Sin actividad'}</b>
						<span>
							{sinDatos ? motivoSinUso : 'Nadie ha hecho llamadas en los últimos 7 días.'}
						</span>
					</div>
				{:else}
					{#each topUsuarios as u, i (u?.usuario ?? i)}
						<div class="fila">
							<div class="puesto">{i + 1}</div>
							<div class="quien">
								<b>{u?.usuario || 'Sin usuario'}</b>
								<span>{parte(aNumero(u?.llamadas)) ?? 'llamadas en 7 días'}</span>
							</div>
							<div class="cuenta">{cuenta(aNumero(u?.llamadas))}</div>
						</div>
					{/each}
				{/if}
			</div>
		</Celda>

		<!-- Serie 2×1: llamadas por app, de mayor a menor. -->
		<Celda area="3/1/4/3" rotulo="Llamadas por app · 7 días" i={2}>
			<div class="cuerpo">
				{#if apps.length === 0}
					<div class="sin-dato">
						<b>{sinDatos ? tituloSinUso : 'Sin llamadas'}</b>
						<span>
							{sinDatos ? motivoSinUso : 'Ni Admon ni Field registraron llamadas en 7 días.'}
						</span>
					</div>
				{:else}
					<div class="barras">
						{#each apps as a (a.clave)}
							<div class="barra">
								<span class="app">{a.nombre}</span>
								<div class="pista" aria-hidden="true">
									<i style="width:{Math.max(4, Math.round((a.n / maxApp) * 100))}%"></i>
								</div>
								<span class="n">{cuenta(a.n)}</span>
							</div>
						{/each}
					</div>
					<div class="sub">
						{#if total != null}
							<b>{cuenta(total)} llamadas</b> en total
						{:else}
							sin total del periodo
						{/if}
						{#if fallo}· última lectura buena{/if}
					</div>
				{/if}
			</div>
		</Celda>

		<!-- 1×1: usuarios activos (distintos) en la semana. -->
		<Celda area="3/3/4/4" rotulo="Usuarios activos" i={3}>
			<div class="cuerpo">
				{#if activos == null}
					<div class="cifra sin">—</div>
					<div class="sub">{sinDatos ? 'sin datos del resumen' : 'sin dato de usuarios'}</div>
				{:else}
					<div class="cifra">{cuenta(activos)}</div>
					<div class="sub">en los últimos 7 días</div>
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
	/* El ancla es una PALABRA (el nombre de la app), no un número: se baja a
	   112 px para que «Admon» y «Field» quepan enteros. */
	.cifra.ancla {
		font-size: 112px;
		letter-spacing: -4px;
		line-height: 0.95;
	}
	.cifra .texto {
		white-space: nowrap;
	}
	/* Sin actividad: se dice con palabras, no con un cero gigante. */
	.cifra.sin-uso {
		font-size: 76px;
		letter-spacing: -2px;
		color: #7fe3cf;
	}
	/* Sin dato: un guion chico y apagado, no una barra negra de 96 px. */
	.cifra.sin {
		font-size: 64px;
		letter-spacing: 0;
		opacity: 0.28;
	}
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
		font-size: 20px;
		font-weight: 700;
		opacity: 0.6;
	}

	/* ── lista de usuarios ────────────────────────────────────── */
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
		gap: 20px;
		padding: 8px 0;
		border-bottom: 1px solid rgba(18, 20, 26, 0.08);
	}
	.fila:last-child {
		border-bottom: 0;
	}
	.puesto {
		width: 44px;
		flex: 0 0 44px;
		font-size: 30px;
		font-weight: 900;
		font-variant-numeric: tabular-nums;
		opacity: 0.32;
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
		font-size: 20px;
		font-weight: 600;
		opacity: 0.5;
	}
	.cuenta {
		font-size: 30px;
		font-weight: 800;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
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

	/* ── barras por app ───────────────────────────────────────── */
	.barras {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}
	.barra {
		display: flex;
		align-items: center;
		gap: 16px;
	}
	.app {
		width: 150px;
		flex: 0 0 150px;
		font-size: 24px;
		font-weight: 800;
		letter-spacing: -0.2px;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.pista {
		flex: 1;
		height: 22px;
		border-radius: 6px;
		background: rgba(18, 20, 26, 0.07);
		overflow: hidden;
	}
	.pista i {
		display: block;
		height: 100%;
		border-radius: 6px;
		background: var(--k-tinta);
	}
	/* La más usada en tinta llena; las demás, en tinta apagada: no compiten. */
	.barra:not(:first-child) .pista i {
		background: rgba(18, 20, 26, 0.34);
	}
	.n {
		width: 96px;
		flex: 0 0 96px;
		text-align: right;
		font-size: 24px;
		font-weight: 800;
		font-variant-numeric: tabular-nums;
	}
</style>
