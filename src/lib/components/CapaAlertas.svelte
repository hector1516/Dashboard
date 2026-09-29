<!--
	Capa de alertas: tres niveles, porque un solo nivel no funciona en una
	pantalla a 3 metros.

	  info     → banda tipo ticker abajo (no interrumpe la pantalla actual)
	  exito    → toast de esquina 6s, con sonido de 2 notas
	  pantalla → AVISO A PANTALLA COMPLETA 10s, con el nombre de quien lo hizo
	             en grande y el módulo de dónde viene. Pausa la rotación y va en
	             cola: si llegan cuatro de golpe se muestran uno por uno.
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
		/** Aviso a pantalla completa que se está mostrando ahora (o null). */
		aviso: EventoKiosko | null;
		onCerrarAviso: () => void;
	}

	let { banda, toast, aviso, onCerrarAviso }: Props = $props();

	let restantePantalla = $state(0);

	// Cuenta atrás del aviso a pantalla completa, y confeti si es celebración.
	$effect(() => {
		if (!aviso) {
			restantePantalla = 0;
			return;
		}
		const seg = aviso.segundos ?? 10;
		const t0 = Date.now();
		const paso = () => {
			restantePantalla = Math.max(0, seg - Math.floor((Date.now() - t0) / 1000));
			if (restantePantalla > 0) requestAnimationFrame(paso);
		};
		requestAnimationFrame(paso);
		// Confeti una sola vez al abrir el aviso (no en cada re-render).
		if (aviso.confeti) lanzarConfeti(120);
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

<!--
	AVISO A PANTALLA COMPLETA (nivel 'pantalla').

	Es lo que pidió el usuario para las entradas/salidas, los kilómetros, los
	tickets y los reportes firmados: toda la pantalla, de un color llamativo, con
	el nombre de QUIÉN arriba en grande, el módulo de dónde viene, y SIN
	fotografías (una foto de 200 px a 3 metros no dice nada y roba el espacio del
	texto).

	El fondo es el color del evento al 88% con una viñeta más oscura en el centro:
	llamativo y sin perder legibilidad. El blanco del texto lleva sombra porque
	encima de un color saturado un blanco plano vibra y deja de leerse.
-->
{#if aviso}
	<div class="aviso" style="--c:{colorDe('pantalla')}" role="alertdialog">
		<div class="aviso-fondo" aria-hidden="true"></div>
		<div class="aviso-caja">
			<div class="aviso-modulo">
				<span class="aviso-ic">{aviso.icono}</span>
				{aviso.modulo ?? 'ECCSA'}
			</div>

			{#if aviso.persona}
				<div class="aviso-persona">{aviso.persona}</div>
			{/if}

			<div class="aviso-titulo">{aviso.titulo}</div>
			{#if aviso.texto}
				<div class="aviso-texto">{aviso.texto}</div>
			{/if}
			{#if aviso.meta}
				<div class="aviso-meta">{aviso.meta}</div>
			{/if}

			<div class="aviso-pie">
				<div class="aviso-barra" style="--r:{restantePantalla}">
					<span class="lleno" style="width:{restantePantalla * 10}%"></span>
				</div>
				<button class="aviso-cerrar" onclick={onCerrarAviso}>
					Continuar <span class="cuenta">{restantePantalla}s</span>
				</button>
			</div>
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
				alerta: 'var(--color-warning)',
				// Verde saturado: es la capa que se come la pantalla, tiene que
				// ser inconfundible con la de las bandas informationales.
				pantalla: '#16a34a'
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

	/* ── Aviso a pantalla completa ──────────────────────────── */
	.aviso {
		position: absolute;
		inset: 0;
		z-index: 55;
		display: flex;
		align-items: center;
		justify-content: center;
		/* El color del evento se ve en los bordes y en la viñeta; el centro se
		   apaga para que el texto blanco sea legible. */
		background: color-mix(in srgb, var(--c) 90%, #04121f);
	}
	.aviso-fondo {
		position: absolute;
		inset: 0;
		background:
			radial-gradient(ellipse at 50% 50%, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0.1) 64%, rgba(0,0,0,0.42) 100%),
			radial-gradient(circle at 50% 118%, rgba(255,255,255,0.18) 0%, rgba(255,255,255,0) 58%);
		pointer-events: none;
	}
	.aviso-caja {
		position: relative;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 6px;
		text-align: center;
		padding: 0 90px;
		max-width: 1750px;
		animation: entraCaja 0.55s cubic-bezier(0.16, 1, 0.3, 1) both;
	}

	.aviso-modulo {
		display: flex;
		align-items: center;
		gap: 14px;
		font-size: 40px;
		font-weight: 800;
		letter-spacing: 0.18em;
		text-transform: uppercase;
		color: rgba(255, 255, 255, 0.72);
	}
	.aviso-ic { font-size: 52px; line-height: 1; }

	/* Lo primero que se lee a 6 metros: quién. */
	.aviso-persona {
		font-size: 168px;
		font-weight: 800;
		line-height: 0.98;
		letter-spacing: -0.025em;
		color: #fff;
		text-shadow: 0 6px 40px rgba(0, 0, 0, 0.55), 0 2px 6px rgba(0, 0, 0, 0.4);
	}
	.aviso-titulo {
		font-size: 120px;
		font-weight: 900;
		line-height: 1;
		color: #fff;
		text-shadow: 0 5px 32px rgba(0, 0, 0, 0.5), 0 2px 6px rgba(0, 0, 0, 0.35);
	}
	/* Si no hay persona, el título es el que manda y toma su tamaño. */
	.aviso-texto {
		font-size: 54px;
		font-weight: 700;
		color: rgba(255, 255, 255, 0.94);
		text-shadow: 0 4px 22px rgba(0, 0, 0, 0.5);
	}
	.aviso-meta {
		font-size: 34px;
		font-weight: 600;
		color: rgba(255, 255, 255, 0.68);
	}

	.aviso-pie {
		margin-top: 34px;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 14px;
	}
	/* Barra de tiempo: deja claro que la pantalla vuelve sola. */
	.aviso-barra {
		width: 420px;
		height: 6px;
		border-radius: 999px;
		background: rgba(0, 0, 0, 0.35);
		overflow: hidden;
	}
	.aviso-barra .lleno {
		display: block;
		height: 100%;
		background: rgba(255, 255, 255, 0.85);
	}
	.aviso-cerrar {
		font-size: 22px;
		font-weight: 700;
		cursor: pointer;
		color: rgba(255, 255, 255, 0.75);
		background: rgba(0, 0, 0, 0.3);
		border: 1px solid rgba(255, 255, 255, 0.28);
		border-radius: 999px;
		padding: 10px 30px;
	}
	.aviso-cerrar:hover { background: rgba(0, 0, 0, 0.5); }

	/*
		SÓLO transform, nunca opacity. Una animación de opacidad que se queda a
		media camino (tabs en segundo plano, ahorro de energía, o un navegador
		que congela animaciones) deja el texto del aviso en un verde pálido sobre
		verde: literalmente ilegible desde el pasillo. El golpe de entrada se
		logra con escala y desplazamiento, que además van por el compositor y no
		repintan nada.
	*/
	@keyframes entraCaja {
		from { transform: scale(0.9) translateY(26px); }
		to   { transform: none; }
	}

</style>
