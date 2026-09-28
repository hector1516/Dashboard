<!--
	📸 Fotografías de los reportes — carrusel a pantalla completa.

	AQUÍ ESTÁ EL ARREGLO: en el dashboard de Field el índice de foto NUNCA se
	incrementaba (`photoIdx` solo se reseteaba), así que la pantalla se quedaba
	clavada en la misma foto los 20s de su turno, con una precarga de la
	siguiente que no servía para nada. Aquí el carrusel avanza de verdad, con
	crossfade entre fotos y efecto ken-burns lento.
-->
<script lang="ts">
	import { anchoFotos, thumbFoto } from '$lib/kiosk/api';
	import type { Snapshot } from '$lib/kiosk/types';

	interface Props {
		datos: Snapshot;
		/** Segundos por foto. */
		intervalo?: number;
	}
	let { datos, intervalo = 6 }: Props = $props();

	const fotos = $derived(datos.fotos?.ids ?? []);
	// El ancho lo publica el backend (ver api.ts): si no coinciden, 404 → negro.
	const ancho = $derived(anchoFotos(datos as any));
	let idx = $state(0);
	let visible = $state<string | null>(null);

	// Al cambiar la lista (llegó otro snapshot) se reinicia el carrusel.
	let base: unknown = null;
	$effect(() => {
		const lista = datos.fotos?.ids;
		if (lista !== base) {
			base = lista;
			idx = 0;
		}
	});

	$effect(() => {
		if (fotos.length < 2) return;
		const t = setInterval(() => {
			idx = (idx + 1) % fotos.length;
		}, intervalo * 1000);
		return () => clearInterval(t);
	});

	const actual = $derived(fotos.length ? fotos[idx % fotos.length] : null);

	// Crossfade: al cambiar de foto se muestra la nueva encima.
	$effect(() => {
		if (!actual) {
			visible = null;
			return;
		}
		const url = thumbFoto(actual.IdReporte, actual.Orden, ancho);
		visible = url;
	});

	function precargar(siguiente: number) {
		const f = fotos[siguiente % fotos.length];
		if (f) {
			const img = new Image();
			img.src = thumbFoto(f.IdReporte, f.Orden, ancho);
		}
	}
</script>

<div class="screen sin-padding">
	{#if actual && visible}
		<div class="marco">
			<img class="foto" src={visible} alt={actual.Cliente} onload={() => precargar(idx + 1)} />
			<div class="velo"></div>
			<div class="credito">
				<div class="cliente">{actual.Cliente}</div>
				<div class="fila">
					<span class="autor">👤 {actual.ingeniero}</span>
					<span class="folio">{actual.Folio}</span>
				</div>
			</div>
			<div class="puntos">
				{#each fotos.slice(0, 12) as _, i}
					<span class="pt" class:on={i === (idx % 12)}></span>
				{/each}
			</div>
		</div>
	{:else}
		<div class="vacio">
			Sin fotos disponibles
			<span class="vacio-sub">Se toman de los reportes de servicio que llevan imágenes</span>
		</div>
	{/if}
</div>

<style>
	.sin-padding { padding: 0; }
	/* z-index: el crédito va por ENCIMA de todo; sin esto, el pie de la pantalla
	   (que tiene z-index 20) le cortaba la última línea. */
	.marco { position: absolute; inset: 0; overflow: hidden; background: #020617; z-index: 1; }
	.foto {
		position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover;
		animation: entrarFoto 1.1s ease both, kenburns 9s ease-out both;
	}
	.velo {
		position: absolute; inset: 0;
		background: linear-gradient(0deg, rgba(0,0,0,0.88) 0%, rgba(0,0,0,0.35) 32%, transparent 58%);
	}
	.credito { position: absolute; left: 0; right: 0; bottom: 0; padding: 30px 44px 34px; z-index: 3; }
	.cliente { font-size: 48px; font-weight: 900; color: #fff; text-shadow: 0 3px 26px rgba(0,0,0,0.85); line-height: 1.1; }
	.fila { display: flex; align-items: center; justify-content: space-between; margin-top: 6px; }
	.autor { font-size: 22px; font-weight: 700; color: var(--color-primary-light); }
	.folio { font-size: 17px; color: var(--color-text-muted); }
	.puntos { position: absolute; top: 22px; right: 26px; display: flex; gap: 6px; }
	.pt { width: 8px; height: 8px; border-radius: 50%; background: rgba(255,255,255,0.25); }
	.pt.on { background: var(--color-primary); box-shadow: 0 0 8px rgba(255,107,0,0.7); }

	@keyframes entrarFoto { from { opacity: 0; } to { opacity: 1; } }
	/* Zoom lentísimo: da vida a una foto estática sin distraer. */
	@keyframes kenburns { from { transform: scale(1.04); } to { transform: scale(1.12); } }
</style>
