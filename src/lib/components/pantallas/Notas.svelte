<!--
	📌 Notas y avisos.

	Solo LECTURA: el kiosco no escribe nada. El CRUD de notas vive en el
	módulo de Admon (o en HUB) y esta pantalla solo refleja `HUB_DashboardNotas`.

	El texto se escribe letra a letra: es la única pantalla donde leer es la
	función, y a 3 metros un bloque de texto que aparece de golpe no se lee.
-->
<script lang="ts">
	import { haceCuanto } from '$lib/kiosk/format';
	import type { Nota, Snapshot } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	// Las fijas van primero (ya viene ordenado del backend) y se muestran 3.
	const notas = $derived((datos.notas ?? []).slice(0, 3));

	/** Texto revelado progresivamente. Un `setInterval` por nota. */
	function escribir(destino: { get: () => string; set: (v: string) => void }, texto: string, velocidad = 22) {
		let i = 0;
		destino.set('');
		const t = setInterval(() => {
			i += 2;
			destino.set(texto.slice(0, i));
			if (i >= texto.length) clearInterval(t);
		}, velocidad);
		return () => clearInterval(t);
	}

	// Svelte 5: un estado por nota para el texto revelado.
	let revelados = $state<Record<number, string>>({});
	$effect(() => {
		const timers = notas.map((n) => escribir({ get: () => '', set: (v) => (revelados[n.Id] = v) }, n.Contenido || ''));
		return () => timers.forEach((clear) => clear());
	});
</script>

<div class="screen centro">
	<div class="screen-titulo"><span class="ic">📌</span> Notas y Avisos</div>

	{#if notas.length}
		<div class="notas">
			{#each notas as n, i}
				<div class="nota" style="--c:{n.Color || '#F59E0B'};animation-delay:{i * 0.25}s">
					<div class="titulo">
						{#if n.Fija}<span class="fija">📌 fija</span>{/if}
						{n.Titulo}
					</div>
					<div class="contenido">{revelados[n.Id] ?? ''}<span class="cursor">▌</span></div>
					<div class="autor">— {n.Autor || 'Sistema'} · {haceCuanto(n.fecha_modificado || n.fecha_creacion)}</div>
				</div>
			{/each}
		</div>
	{:else}
		<div class="vacio">
			Sin notas pendientes
			<span class="vacio-sub">Aparecen aquí cuando se crean desde el panel</span>
		</div>
	{/if}
</div>

<style>
	.centro { align-items: center; justify-content: center; }
	.notas { display: flex; flex-direction: column; gap: 18px; width: 100%; max-width: 1500px; }
	.nota {
		padding: 26px 34px; border-radius: 20px;
		background: rgba(255,255,255,0.045); backdrop-filter: blur(10px);
		border-left: 9px solid var(--c);
		animation: entrarNota 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
	}
	.titulo { font-size: 40px; font-weight: 900; color: var(--c); line-height: 1.1; display: flex; align-items: center; gap: 14px; }
	.fija { font-size: 16px; font-weight: 700; color: var(--color-text-muted); background: rgba(255,255,255,0.08); padding: 4px 12px; border-radius: 999px; }
	.contenido { font-size: 27px; font-weight: 600; color: var(--color-text); line-height: 1.35; margin-top: 8px; min-height: 38px; }
	.cursor { color: var(--c); animation: parpadeo 0.9s steps(2) infinite; }
	.autor { font-size: 16px; color: #64748B; margin-top: 12px; }
	@keyframes entrarNota { from { opacity: 0; transform: scale(0.94); } to { opacity: 1; transform: none; } }
	@keyframes parpadeo { 50% { opacity: 0; } }
</style>
