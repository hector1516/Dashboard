<!-- Clima.svelte - Pantalla de clima rediseñada con oficina isométrica -->
<script lang="ts">
	import { haceCuanto, esLluvioso, esNublado, esSoleado } from '$lib/kiosk/format';
	import type { Snapshot } from '$lib/kiosk/types';
	import OficinaIsometrica from '$lib/components/OficinaIsometrica.svelte';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const c = $derived(datos.clima);
	const a = $derived(c.actual);
	const viejo = $derived(!a.temperatura);
	const antiguedad = $derived(haceCuanto(c.leido_en));
</script>

<div class="screen clima-screen">
	<div class="screen-titulo"><span class="ic">🌤️</span> Clima — Monterrey, Nuevo León</div>

	{#if viejo}
		<div class="vacio">
			Clima no disponible
			<span class="vacio-sub">El servidor no pudo leer el clima · último dato: {antiguedad}</span>
		</div>
	{:else}
		<!-- Oficina isométrica con efectos climáticos -->
		<div class="iso-container">
			<OficinaIsometrica
				codigo_clima={a.codigo_clima}
				es_dia={a.es_dia}
				temperatura={a.temperatura}
				descripcion={a.descripcion}
				icono={a.icono}
			/>
		</div>

		<!-- Datos del clima -->
		<div class="clima-data">
			<div class="clima-hero">
				<span class="clima-icono">{a.icono}</span>
				<span class="clima-temp">{a.temperatura}°C</span>
				<span class="clima-desc">{a.descripcion}</span>
			</div>
			<div class="clima-detalles">
				<span>💧 {a.humedad}% humedad</span>
				<span>🌬️ {a.viento} km/h viento</span>
				<span>🕐 leído {antiguedad}</span>
			</div>
		</div>

		<!-- Pronóstico -->
		<div class="pronostico">
			{#if c.hoy.max !== null}
				<div class="pcard">
					<div class="pdia">Hoy</div>
					<div class="ptemp">{c.hoy.min}° — {c.hoy.max}°</div>
					<div class="plluvia">🌧️ {c.hoy.prob_lluvia ?? 0}% de lluvia</div>
				</div>
			{/if}
			{#if c.manana.max !== null}
				<div class="pcard">
					<div class="pdia">Mañana</div>
					<div class="ptemp">{c.manana.min}° — {c.manana.max}°</div>
					<div class="plluvia">🌧️ {c.manana.prob_lluvia ?? 0}% de lluvia</div>
				</div>
			{/if}
			<div class="pcard nota">
				<div class="pdia">Sensación en la oficina</div>
				<div class="ptemp">{(a.temperatura ?? 0) > 30 ? 'Caluroso 🔥' : (a.temperatura ?? 0) > 24 ? 'Agradable 😊' : (a.temperatura ?? 0) > 18 ? 'Fresco 🧊' : 'Frío ❄️'}</div>
				<div class="plluvia">{#if esLluvioso(a.codigo_clima) || esNublado(a.codigo_clima)}Agua paraguas en la entrada{/if}</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.clima-screen { align-items: center; justify-content: center; gap: 8px; }
	.iso-container { flex: 1; min-height: 50vh; }

	.iso-container {
		width: 100%;
		max-width: 900px;
		aspect-ratio: 600 / 420;
		border-radius: 16px;
		overflow: hidden;
		background: linear-gradient(180deg, #1a237e 0%, #42a5f5 100%);
		box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
	}

	.clima-data { text-align: center; }
	.clima-hero { display: flex; align-items: center; justify-content: center; gap: 16px; margin-bottom: 8px; }
	.clima-icono { font-size: 48px; }
	.clima-temp { font-size: 64px; font-weight: 900; color: var(--color-primary-light); line-height: 1; }
	.clima-desc { font-size: 22px; font-weight: 700; color: var(--color-text); }
	.clima-detalles { display: flex; gap: 24px; justify-content: center; font-size: 16px; color: var(--color-text-muted); }

	.pronostico { display: flex; gap: 14px; flex-wrap: wrap; justify-content: center; }
	.pcard {
		text-align: center; padding: 14px 24px; border-radius: 14px;
		background: rgba(255,255,255,0.045); border: 1px solid rgba(255,255,255,0.09);
	}
	.pcard.nota { background: rgba(255,107,0,0.08); border-color: rgba(255,107,0,0.22); }
	.pdia { font-weight: 800; font-size: 16px; color: var(--color-primary-light); }
	.ptemp { font-size: 20px; font-weight: 700; color: var(--color-text); margin: 4px 0; }
	.plluvia { font-size: 14px; color: #60A5FA; }
	.pcard.nota .plluvia { color: var(--color-text-muted); }

	.vacio { text-align: center; color: var(--color-text-muted); font-size: 24px; }
	.vacio-sub { display: block; font-size: 16px; margin-top: 8px; }
</style>
