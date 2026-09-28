<!--
	Capa de alertas: tres niveles, porque un solo nivel no funciona en una
	pantalla a 3 metros.

	  info     → banda tipo ticker abajo (no interrumpe la pantalla actual)
	  exito    → toast de esquina 6s, con sonido de 2 notas
	  destaque → TOMA DE PANTALLA completa 8s + confeti + arpegio. Pausa la
	             rotación: si algo importante pasó, no se cambia de pantalla
	             encima del mensaje.
	  alerta   → banda ámbar/roja en el ticker, 3 notas graves

	Reglas que evitan que esto se vuelva ruido (el riesgo real de un kiosco):
	  · dedup por `id` de evento (vienen de cursores por Id en el backend),
	  · máximo 1 `destaque` cada 3 min,
	  · tope de 3 bandas simultáneas (la más vieja sale),
	  · en silencio nocturno no suena nada, pero el evento se sigue viendo.

	El componente NO reproduce eventos: recibe la cola ya deduplicada desde el
	orquestador, que es quien conoce los timers de rotación.
-->
<script lang="ts">
	import type { EventoKiosko } from '$lib/kiosk/types';
	import { lanzarConfeti } from '$lib/kiosk/fx';

	interface Props {
		/** Últimos eventos a mostrar como bandas (info/alert), más nuevos primero. */
		banda: EventoKiosko[];
		toast: EventoKiosko | null;
		toma: EventoKiosko | null;
		onCerrarToma: () => void;
	}

	let { banda, toast, toma, onCerrarToma }: Props = $props();

	let restante = $state(0);

	// Cuenta regresiva de la toma de pantalla, en segundos.
	$effect(() => {
		if (!toma) {
			restante = 0;
			return;
		}
		restante = toma.segundos ?? 8;
		const t0 = Date.now();
		const paso = () => {
			restante = Math.max(0, (toma.segundos ?? 8) - Math.floor((Date.now() - t0) / 1000));
			if (restante > 0) requestAnimationFrame(paso);
		};
		requestAnimationFrame(paso);
		// Confeti una vez al abrir la toma (no en cada re-render).
		lanzarConfeti(120);
	});
</script>

<!-- Ticker inferior: los avisos que no quitan la pantalla -->
<div class="ticker" aria-live="polite">
	{#each banda as e (e.id)}
		<div class="banda n-{e.nivel}" style="--c:{colorDe(e.nivel)}">
			{#if e.imagen}
				<img class="banda-img" src={e.imagen} alt="" />
			{:else}
				<span class="banda-ic">{e.icono}</span>
			{/if}
			<div class="banda-txt">
				<span class="banda-titulo">{e.titulo}</span>
				<span class="banda-texto">{e.texto}</span>
			</div>
			<span class="banda-meta">{e.meta}</span>
		</div>
	{/each}
</div>

<!-- Toast de esquina para lo importante pero no dominante -->
{#if toast}
	<div class="toast n-{toast.nivel}" style="--c:{colorDe(toast.nivel)}">
		{#if toast.imagen}
			<img class="toast-img" src={toast.imagen} alt="" />
		{:else}
			<span class="toast-ic">{toast.icono}</span>
		{/if}
		<div>
			<div class="toast-titulo">{toast.titulo}</div>
			<div class="toast-texto">{toast.texto}</div>
		</div>
	</div>
{/if}

<!-- Toma de pantalla completa -->
{#if toma}
	<div class="toma" style="--c:{colorDe(toma.nivel)}" role="alertdialog">
		<div class="toma-caja">
			{#if toma.imagen}
				<img class="toma-img" src={toma.imagen} alt="" />
			{:else}
				<div class="toma-ic">{toma.icono}</div>
			{/if}
			<div class="toma-titulo">{toma.titulo}</div>
			<div class="toma-texto">{toma.texto}</div>
			<div class="toma-meta">{toma.meta}</div>
			<button class="toma-cerrar" onclick={onCerrarToma}>
				Continuar <span class="cuenta">{restante}s</span>
			</button>
		</div>
	</div>
{/if}

<script lang="ts" module>
	function colorDe(nivel: string): string {
		return (
			{
				info: 'var(--color-info)',
				exito: 'var(--color-success)',
				destaque: 'var(--color-primary-light)',
				alerta: 'var(--color-warning)'
			} as Record<string, string>
		)[nivel] ?? 'var(--color-info)';
	}
</script>

<style>
	/* ── Ticker ─────────────────────────────────────────────── */
	.ticker {
		/* El escenario incluye header (56px) y pie (30px): el ticker va sobre el
		   contenido, no encima del pie. */
		position: absolute; left: 0; right: 0; bottom: 34px; z-index: 30;
		display: flex; flex-direction: column; gap: 6px;
		padding: 0 18px 8px; pointer-events: none;
	}
	.banda {
		display: flex; align-items: center; gap: 14px;
		background: color-mix(in srgb, var(--c) 22%, rgba(15,23,42,0.9));
		border: 1px solid color-mix(in srgb, var(--c) 55%, transparent);
		border-left: 5px solid var(--c);
		border-radius: 12px; padding: 9px 16px; color: var(--color-text);
		backdrop-filter: blur(10px);
		animation: entraBanda 0.45s cubic-bezier(0.16, 1, 0.3, 1) both;
		box-shadow: 0 10px 26px rgba(0,0,0,0.45);
	}
	.banda.n-alerta { animation: entraBandaAlerta 0.45s cubic-bezier(0.16, 1, 0.3, 1) both, pulsoAlerta 1.6s ease-in-out 0.45s infinite; }
	.banda-img { width: 64px; height: 40px; object-fit: cover; border-radius: 6px; flex-shrink: 0; }
	.banda-ic { font-size: 26px; }
	.banda-txt { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
	.banda-titulo { font-weight: 800; font-size: 17px; color: var(--c); }
	.banda-texto { font-size: 15px; color: var(--color-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.banda-meta { margin-left: auto; font-size: 13px; color: var(--color-text-muted); flex-shrink: 0; }

	@keyframes entraBanda { from { opacity: 0; transform: translateY(30px) scale(0.98); } to { opacity: 1; transform: none; } }
	@keyframes entraBandaAlerta { from { opacity: 0; transform: translateX(-40px) scale(0.98); } to { opacity: 1; transform: none; } }
	@keyframes pulsoAlerta { 0%,100% { box-shadow: 0 10px 26px rgba(0,0,0,0.45); } 50% { box-shadow: 0 10px 34px color-mix(in srgb, var(--c) 55%, transparent); } }

	/* ── Toast ──────────────────────────────────────────────── */
	.toast {
		position: absolute; right: 22px; bottom: 40px; z-index: 35;
		display: flex; align-items: center; gap: 14px;
		max-width: 560px; padding: 14px 20px; border-radius: 14px;
		background: color-mix(in srgb, var(--c) 20%, rgba(15,23,42,0.94));
		border: 1px solid color-mix(in srgb, var(--c) 60%, transparent);
		box-shadow: 0 14px 40px rgba(0,0,0,0.55);
		animation: entraToast 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
	}
	.toast-img { width: 92px; height: 58px; object-fit: cover; border-radius: 8px; }
	.toast-ic { font-size: 34px; }
	.toast-titulo { font-weight: 800; font-size: 19px; color: var(--c); }
	.toast-texto { font-size: 15px; color: var(--color-text); }
	@keyframes entraToast { from { opacity: 0; transform: translateX(60px); } to { opacity: 1; transform: none; } }

	/* ── Toma de pantalla ───────────────────────────────────── */
	.toma {
		position: absolute; inset: 0; z-index: 50;
		display: flex; align-items: center; justify-content: center;
		background: rgba(2, 6, 23, 0.72);
		backdrop-filter: blur(18px);
		animation: entraToma 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
	}
	.toma-caja {
		display: flex; flex-direction: column; align-items: center; gap: 12px;
		padding: 54px 90px; border-radius: 32px; text-align: center;
		background: linear-gradient(160deg, color-mix(in srgb, var(--c) 18%, rgba(30,41,59,0.96)), rgba(15,23,42,0.96));
		border: 2px solid color-mix(in srgb, var(--c) 60%, transparent);
		box-shadow: 0 0 90px color-mix(in srgb, var(--c) 35%, transparent), 0 30px 70px rgba(0,0,0,0.6);
		max-width: 1300px;
	}
	.toma-img { width: 420px; height: 240px; object-fit: cover; border-radius: 18px; }
	.toma-ic { font-size: 120px; line-height: 1; filter: drop-shadow(0 0 40px color-mix(in srgb, var(--c) 60%, transparent)); animation: rebote 2s ease-in-out infinite; }
	.toma-titulo { font-size: 64px; font-weight: 900; color: var(--c); line-height: 1.05; text-shadow: 0 0 40px color-mix(in srgb, var(--c) 40%, transparent); }
	.toma-texto { font-size: 30px; color: var(--color-text); font-weight: 600; }
	.toma-meta { font-size: 18px; color: var(--color-text-muted); }
	.toma-cerrar {
		margin-top: 10px; font-size: 18px; font-weight: 700; cursor: pointer;
		color: var(--color-text-muted); background: transparent;
		border: 1px solid rgba(255,255,255,0.15); border-radius: 999px; padding: 10px 26px;
	}
	.toma-cerrar:hover { background: rgba(255,255,255,0.08); }
	.cuenta { font-variant-numeric: tabular-nums; color: var(--c); }
	@keyframes entraToma { from { opacity: 0; transform: scale(0.94); } to { opacity: 1; transform: none; } }
	@keyframes rebote { 0%,100% { transform: translateY(0) scale(1); } 50% { transform: translateY(-12px) scale(1.05); } }
</style>
