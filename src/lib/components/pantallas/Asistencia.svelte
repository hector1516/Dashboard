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
				<article class="tarjeta" class:en-sitio={p.en_sitio} class:fuera={!p.en_sitio}>
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
						</div>
						<!--
							El estado ya lo dice el color de toda la tarjeta. Aquí sólo
							va la palabra, en gris, sin punto de color: el punto verde
							encima de una tarjeta verde no se ve y el rojo sobre una
							roja tampoco.
						-->
						<span class="estado">{p.en_sitio ? 'En la oficina' : 'Fuera'}</span>
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
						{:else if p.reingreso}
							<!-- Salió y volvió: la salida que se ve sería la de
							     una visita anterior, así que se muestra cuándo
							     entró en la que sigue. -->
							<div class="hora salida">
								<span class="rot">Volvió</span>
								<span class="hhmm">{hhmm(p.reingreso)}</span>
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

		<!--
			La nota que pidió el usuario, y que además es necesaria: estos horarios
			NO salen de un checador. Los deduce la red —el network_scanner ve que
			aparece o desaparece una MAC conocida—, así que son una aproximación
			y no un registro de asistencia. Sin este aviso alguien puede tomar el
			color de una tarjeta como que es un dato verificado, y en una complaint
			de asistencia eso importa.
		-->
		<p class="nota">
			<i class="nota-ic">ℹ</i>
			<span>
				Los horarios se calculan solos a partir de la red de la oficina
				(cuando un equipo o celular conocido se conecta), por lo que pueden
				variar algunos minutos y no siempre detectan todas las entradas ni
				todas las salidas.
				<b>Es información orientativa, no un registro oficial de asistencia.</b>
			</span>
		</p>
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

	/*
		TODA la tarjeta va verde o roja, no una barrita de color en un canto: a 3
		metros la barrita de 5 px es un detalle, y la pregunta de una pantalla de
		asistencia es "¿quién sigue aquí?", que se contesta con el color entero.
	*/
	.tarjeta {
		background: rgba(148, 163, 184, 0.05);
		border: 1px solid rgba(148, 163, 184, 0.14);
		border-radius: 14px;
		padding: 16px 20px 14px;
		display: flex;
		flex-direction: column;
		gap: 11px;
		min-height: 250px;
		backdrop-filter: blur(6px);
		animation: entrarStagger 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
	}
	/* Verde = sigue dentro · rojo = ya salió. */
	.tarjeta.en-sitio {
		background: linear-gradient(160deg, rgba(34, 197, 94, 0.30) 0%, rgba(22, 163, 74, 0.16) 100%);
		border: 1px solid rgba(74, 222, 128, 0.55);
		box-shadow: inset 0 0 40px rgba(34, 197, 94, 0.14);
	}
	.tarjeta.fuera {
		background: linear-gradient(160deg, rgba(239, 68, 68, 0.28) 0%, rgba(185, 28, 28, 0.14) 100%);
		border: 1px solid rgba(248, 113, 113, 0.5);
		box-shadow: inset 0 0 40px rgba(239, 68, 68, 0.12);
	}

	.quien { display: flex; align-items: center; gap: 11px; min-width: 0; }
	.estado {
		margin-left: auto;
		align-self: flex-start;
		flex-shrink: 0;
		font-size: 12px;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.14em;
		color: rgba(255, 255, 255, 0.72);
	}
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
		font-size: 13px;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.12em;
		opacity: 0.9;
	}
	.hhmm {
		font-size: 36px;
		font-weight: 900;
		line-height: 1;
		font-variant-numeric: tabular-nums;
	}

	/* Verde = llegó. */
	.entrada { background: rgba(2, 6, 23, 0.34); border: 1px solid rgba(255, 255, 255, 0.1); }
	.entrada .rot { color: rgba(255, 255, 255, 0.62); }
	.entrada .hhmm { color: #fff; }

	/* Rojo = se fue. */
	.salida { background: rgba(2, 6, 23, 0.34); border: 1px solid rgba(255, 255, 255, 0.1); }
	.salida .rot { color: rgba(255, 255, 255, 0.62); }
	.salida .hhmm { color: #fff; }

	/* Todavía no hay salida: rayitas, no una hora inventada. */
	.esperando { background: rgba(148, 163, 184, 0.08); border: 1px solid rgba(148, 163, 184, 0.16); }
	.esperando .rot { color: #64748b; }
	.esperando .hhmm { color: #64748b; font-size: 30px; }

	/* La nota va al pie de la pantalla, pequeña y apagada: es una aclaración,
	   no un dato. Con el mismo cuidado que el aviso de que la pantalla no está
	   rota: se nota si lo buscas, no se nota si estás leyendo. */
	.nota {
		margin: 0;
		flex-shrink: 0;
		display: flex;
		align-items: flex-start;
		gap: 10px;
		max-width: 1500px;
		margin-inline: auto;
		padding: 10px 18px;
		border-radius: 12px;
		background: rgba(148, 163, 184, 0.06);
		border: 1px solid rgba(148, 163, 184, 0.12);
		font-size: 19px;
		font-weight: 600;
		line-height: 1.4;
		color: #7c8ba1;
	}
	.nota-ic {
		font-style: normal;
		font-size: 20px;
		line-height: 1.3;
		color: #64748b;
		flex-shrink: 0;
	}
	.nota b { color: #a7b3c6; font-weight: 800; }

	.eventos {
		margin-top: auto;
		font-size: 12.5px;
		font-weight: 700;
		color: #475569;
		text-align: right;
	}
</style>
