<!--
	🌤️ Clima de Monterrey.

	La pantalla muestra de qué TAN VIEJO es el dato: si el snapshot viene sin
	clima (sin internet en el servidor), el termómetro se apaga y se dice por
	qué, en vez de fingir que hace 0°. Es el mismo criterio que el resto: la
	pantalla no miente aunque se quede fea.
-->
<script lang="ts">
	import { haceCuanto, esLluvioso, esNublado, esSoleado } from '$lib/kiosk/format';
	import type { Snapshot } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const c = $derived(datos.clima);
	const a = $derived(c.actual);
	const viejo = $derived(!a.temperatura);
	const antiguedad = $derived(haceCuanto(c.leido_en));
</script>

<div class="screen centro">
	<div class="screen-titulo"><span class="ic">🌤️</span> Clima — Monterrey, Nuevo León</div>

	{#if viejo}
		<div class="vacio">
			Clima no disponible
			<span class="vacio-sub">El servidor no pudo leer el clima · último dato: {antiguedad}</span>
		</div>
	{:else}
		<div class="heroe">
			<div class="ic-grande">{a.icono}</div>
			<div class="temp">{a.temperatura}°C</div>
			<div class="desc">{a.descripcion}</div>
			<div class="detalles">
				<span>💧 {a.humedad}% humedad</span>
				<span>🌬️ {a.viento} km/h viento</span>
				<span>🕒 leído {antiguedad}</span>
			</div>
		</div>

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
				<div class="ptemp">{(a.temperatura ?? 0) > 30 ? 'Caluroso 🥵' : (a.temperatura ?? 0) > 24 ? 'Agradable 🙂' : (a.temperatura ?? 0) > 18 ? 'Fresco 🧥' : 'Frío 🥶'}</div>
				<div class="plluvia">{#if esLluvioso(a.codigo_clima) || esNublado(a.codigo_clima)}Agua paraguas en la entrada{/if}</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.centro { align-items: center; justify-content: center; }
	.heroe { text-align: center; margin-bottom: 26px; animation: entrar 0.8s cubic-bezier(0.16, 1, 0.3, 1) both; }
	.ic-grande { font-size: 120px; line-height: 1; filter: drop-shadow(0 0 36px rgba(255,200,50,0.3)); animation: latir 3.4s ease-in-out infinite; }
	.temp { font-size: 108px; font-weight: 900; color: var(--color-primary-light); line-height: 1; text-shadow: 0 0 46px rgba(255,174,0,0.3); }
	.desc { font-size: 30px; font-weight: 700; color: var(--color-text); margin-top: 6px; }
	.detalles { display: flex; gap: 30px; justify-content: center; margin-top: 14px; font-size: 19px; color: var(--color-text-muted); }

	.pronostico { display: flex; gap: 18px; }
	.pcard {
		text-align: center; padding: 18px 34px; border-radius: 18px;
		background: rgba(255,255,255,0.045); border: 1px solid rgba(255,255,255,0.09);
		animation: entrar 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
	}
	.pcard.nota { background: rgba(255,107,0,0.08); border-color: rgba(255,107,0,0.22); }
	.pdia { font-weight: 800; font-size: 19px; color: var(--color-primary-light); }
	.ptemp { font-size: 26px; font-weight: 700; color: var(--color-text); margin: 6px 0; }
	.plluvia { font-size: 16px; color: #60A5FA; }
	.pcard.nota .plluvia { color: var(--color-text-muted); }

	@keyframes entrar { from { opacity: 0; transform: scale(0.92) translateY(18px); } to { opacity: 1; transform: none; } }
	@keyframes latir { 0%,100% { transform: scale(1); } 50% { transform: scale(1.06); } }
</style>
