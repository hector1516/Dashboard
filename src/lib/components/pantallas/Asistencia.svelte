<!--
	🕘 Asistencia del día — quién entró y quién salió HOY.

	Fuente: `HUB_NetworkPresence`, que escribe el `network_scanner_worker` del
	contenedor `workersadmon` cuando ve aparecer o desaparecer una MAC conocida
	en la red. No hay que "registrar" nada: la pantalla deduce el día completo
	solo, y por eso las tarjetas se llaman como son: el registro de la red, no
	el de un checador.

	Dos colores, y son los que pidió el usuario porque son los que se entienden
	desde el otro lado de la oficina:
	  · 🟢 verde  = hora de llegada (primera ENTRADA del día)
	  · 🔴 rojo   = hora de salida (última SALIDA del día)

	Quien sigue dentro lleva un punto verde pulsante y NO muestra hora de
	salida: poner una hora roja de algo que todavía no pasa sería inventar
	dato, y en una pantalla que se mira de reojo nadie se da cuenta del error
	pero sí nota el绿色 que parpadea.
-->
<script lang="ts">
	import { avatarSrc } from '$lib/kiosk/api';
	import { hhmm, iniciales } from '$lib/kiosk/format';
	import type { Snapshot } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const a = $derived(datos.asistencia);
	const personas = $derived(a?.personas ?? []);
	// Los que siguen dentro primero: son los que importan ahora mismo, y en
	// una lista corta la diferencia se nota.
	const ordenados = $derived(
		[...personas].sort((x, y) => Number(y.en_sitio) - Number(x.en_sitio))
	);
</script>

<div class="screen">
	<div class="screen-titulo">
		<span class="ic">🕘</span> Asistencia de hoy
		{#if a?.total}
			<span class="contador">
				{(a.total ?? 0).toString().padStart(2, '0')} registradas ·
				<span class="dentro">🟢 {(a.dentro ?? 0).toString().padStart(2, '0')} en sitio</span> ·
				<span class="fuera">🔴 {(a.salieron ?? 0).toString().padStart(2, '0')} fuera</span>
			</span>
		{/if}
	</div>

	{#if !personas.length}
		<div class="vacio">
			Todavía nadie ha registrado movements hoy
			<span class="vacio-sub">
				La pantalla anota sola cuando un celular o computadora conocido se
				conecta a la red de la oficina
			</span>
		</div>
	{:else}
		<div class="rejilla" class:uno={personas.length === 1}>
			{#each ordenados as p (p.id_usuario)}
				<article class="tarjeta" class:en-sitio={p.en_sitio}>
					<div class="quien">
						<div class="avatar">
							{#if p.avatar}
								<img src={avatarSrc(p.avatar)} alt="" />
							{:else}
								<div class="ph">{iniciales(p.nombre)}</div>
							{/if}
						</div>
						<div class="nombres">
							<span class="nombre">{p.nombre}</span>
							{#if p.en_sitio}
								<span class="pill">● en la oficina</span>
							{/if}
						</div>
					</div>

					<div class="horas">
						<div class="hora entrada">
							<span class="rot">Llegó</span>
							<span class="hhmm">{hhmm(p.entrada)}</span>
						</div>
						{#if p.salida}
							<div class="hora salida">
								<span class="rot">Se fue</span>
								<span class="hhmm">{hhmm(p.salida)}</span>
							</div>
						{:else}
							<div class="hora esperando">
								<span class="rot">Se fue</span>
								<span class="hhmm">— — : — —</span>
							</div>
						{/if}
					</div>

					<!--
						Los movimientos no se esconden: 6 entradas significan que el
						celular perdió el WiFi un rato, y si alguien lo ve con la
						tarjeta en la mano vale la pena que sepa por qué.
					-->
					<span class="eventos">
						{p.eventos} {p.eventos === 1 ? 'movimiento' : 'movimientos'} en la red
					</span>
				</article>
			{/each}
		</div>
	{/if}
</div>

<style>
	.contador {
		font-size: 20px;
		font-weight: 700;
		color: var(--color-text-muted);
		letter-spacing: 0;
	}
	.contador .dentro { color: #4ade80; }
	.contador .fuera { color: #f87171; }

	/*
		Las columnas se calculan por ancho disponible y se CENTRAN: con dos
		personas las tarjetas quedan en el medio y no estiradas a 1080 px de
		alto. Antes la grilla usaba filas de altura completa y con poca gente
		 salían dos tarjetas enormes con medio contenido y un mar de vacío
		abajo, que en una TV se lee como pantalla rota.
	*/
	.rejilla {
		flex: 1;
		min-height: 0;
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(400px, 520px));
		justify-content: center;
		align-content: center;
		gap: 16px;
	}

	.tarjeta {
		background: rgba(255, 255, 255, 0.045);
		border: 1px solid rgba(255, 255, 255, 0.08);
		border-left: 5px solid #334155;
		border-radius: 14px;
		padding: 16px 20px 14px;
		display: flex;
		flex-direction: column;
		gap: 11px;
		min-height: 300px;
		backdrop-filter: blur(6px);
		animation: entrarStagger 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
	}
	/* Quien sigue dentro se nota desde lejos por el borde y el punto verde. */
	.tarjeta.en-sitio { border-left-color: #22c55e; }

	.quien { display: flex; align-items: center; gap: 11px; min-width: 0; }
	.avatar {
		width: 64px;
		height: 64px;
		border-radius: 50%;
		overflow: hidden;
		flex-shrink: 0;
		background: rgba(255, 255, 255, 0.07);
		display: grid;
		place-items: center;
	}
	.avatar img { width: 100%; height: 100%; object-fit: cover; }
	.ph { font-size: 26px; font-weight: 800; color: var(--color-primary); }
	.nombres { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
	.nombre {
		font-size: 28px;
		font-weight: 800;
		color: #fff;
		/* Un nombre largo no rompe la tarjeta ni empuja la rejilla. */
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.pill {
		font-size: 13.5px;
		font-weight: 800;
		color: #4ade80;
		letter-spacing: 0.02em;
		animation: parpadeo 2.2s ease-in-out infinite;
	}
	@keyframes parpadeo { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }

	.horas { display: flex; flex-direction: column; gap: 7px; }
	.hora {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 10px;
		padding: 8px 13px;
		border-radius: 10px;
	}
	.rot {
		font-size: 15px;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.12em;
		opacity: 0.9;
	}
	.hhmm {
		font-size: 48px;
		font-weight: 900;
		line-height: 1;
		font-variant-numeric: tabular-nums;
	}

	/* Verde = llegó. */
	.entrada { background: rgba(34, 197, 94, 0.14); border: 1px solid rgba(34, 197, 94, 0.3); }
	.entrada .rot { color: #4ade80; }
	.entrada .hhmm { color: #22c55e; text-shadow: 0 0 22px rgba(34, 197, 94, 0.35); }

	/* Rojo = se fue. */
	.salida { background: rgba(239, 68, 68, 0.14); border: 1px solid rgba(239, 68, 68, 0.3); }
	.salida .rot { color: #f87171; }
	.salida .hhmm { color: #ef4444; text-shadow: 0 0 22px rgba(239, 68, 68, 0.35); }

	/* Todavía no hay salida: rayitas, no una hora inventada. */
	.esperando { background: rgba(148, 163, 184, 0.08); border: 1px solid rgba(148, 163, 184, 0.16); }
	.esperando .rot { color: #64748b; }
	.esperando .hhmm { color: #475569; font-size: 38px; }

	.eventos {
		margin-top: auto;
		font-size: 12.5px;
		font-weight: 700;
		color: #475569;
		text-align: right;
	}
</style>
