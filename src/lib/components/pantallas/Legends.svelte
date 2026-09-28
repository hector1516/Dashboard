<!--
	🏆 ECCSA Legends — carrera semanal.

	El 1er lugar ocupa la mitad de arriba (con corona, rayos y partículas) y el
	resto son tarjetas con escala decreciente: a 3 metros se lee quién ganó sin
	leer el número. Las tarjetas son grandes (avatar de hasta 104 px) y el
	podio puede ocupar dos filas si ya no caben en una: lo que NO se toca es el
	tamaño del ganador, que es el que tiene que dominar la pantalla.

	Novedades: flecha ↑↓ cuando alguien sube o baja de puesto (el backend
	compara con el ranking anterior) y cuenta regresiva al reinicio semanal.
	El confeti del ganador lo dispara el orquestador al detectar un cambio en
	el primer lugar, no este componente: así no se repite en cada rotación.
-->
<script lang="ts">
	import { avatarSrc } from '$lib/kiosk/api';
	import { medalla, rankScale, NIVEL_EMOJI, hhmmDiff, num } from '$lib/kiosk/format';
	import type { Snapshot } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const ranking = $derived(datos.legends.ranking ?? []);
	const ganador = $derived(ranking[0]);
	const resto = $derived(ranking.slice(1));
</script>

<div class="screen">
	<div class="screen-titulo">
		<span class="ic">🏆</span> ECCSA Legends — Carrera Semanal
		{#if datos.legends.reset_en_segundos > 0}
			<span class="reset">reinicia en {hhmmDiff(datos.legends.reset_en_segundos)}</span>
		{/if}
	</div>

	{#if ganador}
		<div class="escenario">
			<div class="rayos" aria-hidden="true"></div>
			<div class="corona">👑</div>
			<div class="avatar-grande">
				{#if ganador.avatar}
					<img src={avatarSrc(ganador.avatar)} alt="" class="img-grande" />
				{:else}
					<div class="ph-grande">{(ganador.nickname || ganador.nombre || '?')[0]}</div>
				{/if}
			</div>
			<div class="info-grande">
				<div class="nombre-grande">
					{ganador.nickname || ganador.nombre}
					{#if ganador.puesto_anterior && ganador.puesto_anterior > 1}
						<span class="subio" title="Subió de puesto">▲</span>
					{/if}
				</div>
				<div class="puntos-grande">{num(ganador.puntos)} <span class="pts-lab">pts</span></div>
				<div class="nivel-grande">{NIVEL_EMOJI[ganador.nivel] ?? ''} {ganador.nivel}</div>
			</div>
		</div>

		{#if resto.length}
			<div class="podio">
				{#each resto as r, i}
					{@const esc = rankScale(i + 2)}
					{@const antes = r.puesto_anterior}
					<div
						class="tarjeta"
						style="--rs:{esc};animation-delay:{(i + 1) * 0.08}s"
						class:oro={i === 0}
						class:plata={i === 1}
						class:bronce={i === 2}
					>
						<span class="pos">{medalla(i + 2)}</span>
						<div class="avatar-med" style="width:calc(60px * var(--rs));height:calc(60px * var(--rs))">
							{#if r.avatar}
								<img src={avatarSrc(r.avatar)} alt="" class="img-med" />
							{:else}
								<div class="ph-med">{(r.nickname || r.nombre || '?')[0]}</div>
							{/if}
						</div>
						<div class="meta">
							<span class="nombre">{r.nickname || r.nombre}</span>
							<span class="pts">{num(r.puntos)} pts</span>
						</div>
						{#if antes}
							<span class="delta" class:subio={antes > i + 2} class:bajo={antes < i + 2}>
								{antes > i + 2 ? '▲' : antes < i + 2 ? '▼' : '='}
							</span>
						{/if}
					</div>
				{/each}
			</div>
		{/if}
	{:else}
		<div class="vacio">
			Sin ranking esta semana
			<span class="vacio-sub">El ranking se arma con la puntuación de los usuarios</span>
		</div>
	{/if}
</div>

<style>
	.reset { font-size: 15px; font-weight: 700; color: var(--color-text-muted); letter-spacing: 0; }

	.escenario {
		position: relative; flex: 1 1 auto; min-height: 300px; max-height: 520px;
		display: flex; align-items: center; justify-content: center; gap: 56px;
		border-radius: 26px;
		background: linear-gradient(160deg, rgba(255,215,0,0.10), rgba(255,107,0,0.03) 55%, transparent);
		border: 1px solid rgba(255,215,0,0.18);
		overflow: hidden;
	}
	/* El rays tiene máscara radial: sin ella el conic-gradient pinta un disco
	   oscuro enorme en el centro de la pantalla (se veía como una mancha). */
	.rayos {
		position: absolute; top: 50%; left: 50%; width: 640px; height: 640px;
		transform: translate(-50%, -50%);
		background: conic-gradient(from 0deg, transparent, rgba(255,215,0,0.22), transparent, rgba(255,107,0,0.14), transparent, rgba(255,215,0,0.22), transparent);
		-webkit-mask-image: radial-gradient(circle, #000 8%, rgba(0,0,0,0.35) 45%, transparent 72%);
		mask-image: radial-gradient(circle, #000 8%, rgba(0,0,0,0.35) 45%, transparent 72%);
		border-radius: 50%; animation: girar 9s linear infinite;
	}
	.corona {
		position: absolute; top: 26px; left: 50%; transform: translateX(-50%);
		font-size: 62px; z-index: 4;
		filter: drop-shadow(0 0 18px rgba(255,215,0,0.85));
		animation: flotar 2.6s ease-in-out infinite;
	}
	.avatar-grande {
		position: relative; z-index: 3;
		width: 330px; height: 330px; border-radius: 50%; flex-shrink: 0;
		animation: latirGrande 2.4s ease-in-out infinite;
	}
	.img-grande { width: 100%; height: 100%; border-radius: 50%; object-fit: cover; border: 7px solid #FFD700; box-shadow: 0 0 80px rgba(255,215,0,0.5), 0 0 160px rgba(255,107,0,0.22); }
	.ph-grande {
		width: 100%; height: 100%; border-radius: 50%;
		background: linear-gradient(135deg, #FFD700, #FF6B00);
		display: flex; align-items: center; justify-content: center;
		font-weight: 900; font-size: 130px; color: #0F172A; border: 7px solid #FFD700;
	}
	.info-grande { z-index: 3; text-align: center; }
	.nombre-grande { font-size: 62px; font-weight: 900; color: #FFD700; line-height: 1.05; text-shadow: 0 0 28px rgba(255,215,0,0.4); }
	.puntos-grande { font-size: 92px; font-weight: 900; color: var(--color-primary-light); line-height: 1; text-shadow: 0 0 40px rgba(255,174,0,0.5); font-variant-numeric: tabular-nums; }
	.pts-lab { font-size: 24px; color: var(--color-text-muted); font-weight: 600; }
	.nivel-grande { font-size: 22px; font-weight: 700; color: var(--color-primary-light); margin-top: 4px; }
	.subio { font-size: 26px; color: #4ADE80; }

	.podio { display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 14px; flex-shrink: 0; max-height: 340px; overflow: hidden; padding-bottom: 2px; }
	.tarjeta {
		display: flex; align-items: center; gap: calc(14px * var(--rs));
		padding: calc(13px * var(--rs)) calc(20px * var(--rs));
		border-radius: calc(18px * var(--rs) + 4px);
		background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
		animation: entrarTarjeta 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
	}
	.tarjeta.oro    { background: linear-gradient(135deg, rgba(192,132,252,0.17), rgba(168,85,247,0.05)); border-color: rgba(192,132,252,0.38); }
	.tarjeta.plata  { background: linear-gradient(135deg, rgba(203,213,225,0.15), rgba(148,163,184,0.05)); border-color: rgba(203,213,225,0.32); }
	.tarjeta.bronce { background: linear-gradient(135deg, rgba(217,119,6,0.15), rgba(180,83,9,0.05)); border-color: rgba(217,119,6,0.32); }
	.pos { font-weight: 800; font-size: calc(28px * var(--rs)); color: var(--color-text-muted); min-width: calc(46px * var(--rs)); text-align: center; }
	.avatar-med { border-radius: 50%; overflow: hidden; flex-shrink: 0; border: calc(3px * var(--rs)) solid rgba(255,255,255,0.22); }
	.img-med { width: 100%; height: 100%; object-fit: cover; }
	.ph-med { width: 100%; height: 100%; background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light)); display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: calc(38px * var(--rs)); color: #0F172A; }
	.meta { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
	.nombre { font-weight: 700; font-size: calc(27px * var(--rs)); color: var(--color-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: calc(330px * var(--rs)); }
	.pts { font-size: calc(21px * var(--rs)); font-weight: 800; color: var(--color-primary-light); background: rgba(255,174,0,0.14); padding: calc(3px * var(--rs)) calc(10px * var(--rs)); border-radius: 10px; align-self: flex-start; white-space: nowrap; }
	.delta { font-size: calc(22px * var(--rs)); font-weight: 900; color: #64748B; }
	.delta.subio { color: #4ADE80; }
	.delta.bajo { color: #F87171; }

	@keyframes girar { to { transform: translate(-50%, -50%) rotate(360deg); } }
	@keyframes flotar { 0%,100% { transform: translateX(-50%) translateY(0); } 50% { transform: translateX(-50%) translateY(-12px); } }
	@keyframes latirGrande { 0%,100% { transform: scale(1); } 50% { transform: scale(1.03); } }
	@keyframes entrarTarjeta { from { opacity: 0; transform: translateY(16px) scale(0.92); } to { opacity: 1; transform: none; } }
</style>
