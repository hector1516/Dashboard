<!--
	🎂 Celebraciones — cumpleaños y aniversarios del mes.

	Lo que cambia frente a Field: los de HOY van primero y en grande (es lo que
	la gente quiere ver en el pasillo a las 11 de la mañana), y el tamaño de las
	tarjetas se adapta al número de personas: 2 personas pueden ocupar media
	pantalla cada una; 12 personas necesitan tarjetas compactas o no caben.

	La EDAD de los cumpleañeros la calcula el backend desde el RFC/CURP (año en
	las posiciones 5-6, mes 7-8, día 9-10) o desde `FechaNacimiento` si existe.
	Ojo: es el campo `edad`; los aniversarios usan `anos` (antigüedad). Se
	confundir los dos hacía que las tarjetas del mes mostraran "— años".

	El confeti lo dispara el orquestador cuando detectan un cumpleaños HOY.
-->
<script lang="ts">
	import { avatarSrc } from '$lib/kiosk/api';
	import { nombreMes } from '$lib/kiosk/format';
	import type { Aniversariero, Cumpleanero, Snapshot } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const cumples = $derived<Cumpleanero[]>(datos.cumpleanos?.del_mes ?? []);
	const anivers = $derived<Aniversariero[]>(datos.aniversarios?.del_mes ?? []);
	const hoyCumples = $derived<Cumpleanero[]>(datos.cumpleanos?.hoy ?? []);
	const hoyAnivers = $derived<Aniversariero[]>(datos.aniversarios?.hoy ?? []);

	const total = $derived(cumples.length + anivers.length);
	const tam = $derived(total <= 2 ? 'xl' : total <= 4 ? 'lg' : total <= 8 ? 'md' : 'sm');
	const mes = $derived(nombreMes());

	/** Hoy primero, y sin repetirlo en la lista del mes. */
	const cumplesMes = $derived(
		cumples.filter((c) => !hoyCumples.some((h) => h.Nombre === c.Nombre && h.dia === c.dia))
	);
</script>

<div class="screen" class:denso={tam === 'sm'}>
	<div class="screen-titulo"><span class="ic">🎂</span> {mes} — Celebraciones</div>

	<div class="contenedor">
		{#if hoyCumples.length || hoyAnivers.length}
			<div class="seccion hoy">
				<div class="seccion-titulo hoy-titulo">⭐ Hoy en ECCSA</div>
				<div class="rejilla r-{tam}">
					{#each hoyCumples as c, i}
						<div class="tarjeta t-xl" style="--c:236,72,153;animation-delay:{i * 0.1}s">
							{#if c.avatar}<img class="avatar-g" src={avatarSrc(c.avatar)} alt={c.Nombre} />{:else}<div class="avatar-g ph">{(c.Nombre || '?')[0]}</div>{/if}
							<div class="nombre">{c.Nombre}</div>
							<div class="detalle">cumpleaños hoy</div>
							<div class="edad">{c.edad ?? '—'} años</div>
							<div class="flotante">🎂</div>
						</div>
					{/each}
					{#each hoyAnivers as a, i}
						<div class="tarjeta t-xl" style="--c:34,197,94;animation-delay:{(i + 1) * 0.1}s">
							{#if a.avatar}<img class="avatar-g" src={avatarSrc(a.avatar)} alt={a.Nombre} />{:else}<div class="avatar-g ph">{(a.Nombre || '?')[0]}</div>{/if}
							<div class="nombre">{a.Nombre}</div>
							<div class="detalle">aniversario hoy</div>
							<div class="edad">{a.anos ?? '—'} años en ECCSA</div>
							<div class="flotante">🎉</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		{#if cumplesMes.length}
			<div class="seccion">
				<div class="seccion-titulo">🎂 Cumpleaños del mes <span class="conteo">({cumplesMes.length})</span></div>
				<div class="rejilla r-{tam}">
					{#each cumplesMes as c, i}
						<div class="tarjeta" style="--c:236,72,153;animation-delay:{i * 0.08}s">
							{#if c.avatar}<img class="avatar-g" src={avatarSrc(c.avatar)} alt={c.Nombre} />{:else}<div class="avatar-g ph">{(c.Nombre || '?')[0]}</div>{/if}
							<div class="nombre">{c.Nombre}</div>
							<div class="detalle">{c.dia} de {mes}</div>
							<div class="edad">{c.edad ?? '—'} años</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		{#if anivers.length}
			<div class="seccion">
				<div class="seccion-titulo">🎉 Aniversarios en ECCSA <span class="conteo">({anivers.length})</span></div>
				<div class="rejilla r-{tam}">
					{#each anivers as a, i}
						<div class="tarjeta" style="--c:34,197,94;animation-delay:{i * 0.08}s">
							{#if a.avatar}<img class="avatar-g" src={avatarSrc(a.avatar)} alt={a.Nombre} />{:else}<div class="avatar-g ph">{(a.Nombre || '?')[0]}</div>{/if}
							<div class="nombre">{a.Nombre}</div>
							<div class="detalle">{a.dia} de {mes}</div>
							<div class="edad">{a.anos ?? '—'} años</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		{#if !total}
			<div class="vacio">
				Sin celebraciones este mes 🎉
				<span class="vacio-sub">Se leen del CURP o de la fecha de nacimiento de cada usuario</span>
			</div>
		{/if}
	</div>
</div>

<style>
	.contenedor { flex: 1; min-height: 0; display: flex; flex-direction: column; gap: 14px; overflow: hidden; justify-content: center; }
	.seccion-titulo { font-size: 26px; font-weight: 900; color: var(--color-primary-light); text-align: center; margin-bottom: 6px; }
	.hoy-titulo { color: #fff; text-shadow: 0 0 26px rgba(255,215,0,0.5); }
	.conteo { font-size: 18px; color: var(--color-text-muted); }
	.rejilla { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; align-items: stretch; }

	.tarjeta {
		position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center;
		gap: 4px; padding: 14px 18px; border-radius: 22px; text-align: center; overflow: hidden;
		background: linear-gradient(145deg, rgba(var(--c) / 0.18), rgba(var(--c) / 0.04));
		border: 2px solid rgba(var(--c) / 0.32);
		box-shadow: 0 12px 32px rgba(0,0,0,0.3);
		animation: entrarCel 0.55s cubic-bezier(0.16, 1, 0.3, 1) both;
		flex: 1 1 auto; min-width: 0;
	}
	.avatar-g { border-radius: 50%; object-fit: cover; border: 4px solid rgba(var(--c) / 0.5); box-shadow: 0 0 30px rgba(var(--c) / 0.28); }
	.avatar-g.ph { display: flex; align-items: center; justify-content: center; font-weight: 900; color: #0F172A; background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light)); }
	.nombre { font-weight: 900; color: #fff; line-height: 1.15; }
	.detalle { color: #CBD5E1; line-height: 1.2; }
	.edad { font-weight: 800; color: var(--color-primary-light); }
	.flotante { position: absolute; top: 10px; right: 16px; font-size: 28px; opacity: 0.6; animation: flotar 3s ease-in-out infinite; }

	/* Tamaño según cuántas hay: ≤2 enorme · ≤4 grande · ≤8 media · más compacta */
	.r-xl .tarjeta { padding: 26px 30px; min-height: 300px; max-width: 620px; }
	.r-xl .avatar-g { width: 190px; height: 190px; }
	.r-xl .nombre { font-size: 34px; }
	.r-xl .detalle { font-size: 21px; }
	.r-xl .edad { font-size: 26px; }

	.r-lg .tarjeta { padding: 20px 24px; min-height: 240px; max-width: 430px; }
	.r-lg .avatar-g { width: 145px; height: 145px; }
	.r-lg .nombre { font-size: 26px; }
	.r-lg .detalle { font-size: 17px; }
	.r-lg .edad { font-size: 21px; }

	.r-md .tarjeta { padding: 12px 16px; min-height: 180px; max-width: min(calc(50% - 7px), 340px); }
	.r-md .avatar-g { width: 105px; height: 105px; }
	.r-md .nombre { font-size: 21px; }
	.r-md .detalle { font-size: 15px; }
	.r-md .edad { font-size: 18px; }

	.r-sm .tarjeta { padding: 9px 12px; min-height: 140px; max-width: calc(33.33% - 9px); }
	.r-sm .avatar-g { width: 78px; height: 78px; }
	.r-sm .nombre { font-size: 17px; }
	.r-sm .detalle { font-size: 13px; }
	.r-sm .edad { font-size: 15px; }
	.r-sm .tarjeta.t-xl { max-width: calc(50% - 7px); min-height: 220px; }
	.r-sm .tarjeta.t-xl .avatar-g { width: 130px; height: 130px; }
	.r-sm .tarjeta.t-xl .nombre { font-size: 24px; }

	@keyframes entrarCel { from { opacity: 0; transform: scale(0.85) rotate(-2deg); } to { opacity: 1; transform: none; } }
	@keyframes flotar { 0%,100% { transform: translateY(0) rotate(0deg); } 50% { transform: translateY(-9px) rotate(9deg); } }
</style>
