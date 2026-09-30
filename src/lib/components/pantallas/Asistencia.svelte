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

	/*
		Todos los que tengan registro HOY, sin filtrar. Cada tarjeta lleva las
		dos horas:
		  · LLEGÓ = la entrada MÁS TEMPRANA del día (la primera vez que se
		    detectó su equipo en la red). Es la hora de llegada de verdad, no
		    la última: con un celular que entra y sale seis veces, la última
		    entrada no dice cuándo llegó.
		  · SE FUE = su última salida, y SÓLO si ya no está aquí. Si sigue en
		    la oficina la salida todavía no pasó y ponerla sería inventar un
		    dato; por eso la fila simplemente no se pinta.
		El color de la tarjeta dice en cuál de los dos casos está cada quien:
		verde = sigue aquí, rojo = ya se fue.
	*/
	const conRegistro = $derived(personas.filter((p) => p.entrada));

	/**
	 * Cuadrados que quepan TODOS, calculados, no un grid que se desborda.
	 *
	 * Con 4 personas en un `auto-fit` de 3 columnas quedan dos tarjetas
	 * chiquitas y un hueco enorme; con 25 nadie cabe. Aquí se elige el número
	 * de columnas a partir de cuántas hay (una rejilla casi cuadrada) y de ahí
	 * el lado del cuadro para que quepan en el escenario: alto y ancho dividen
	 * entre filas y columnas, y se toma el menor.
	 */
	const LADO_MAX = 360;
	const AREA_W = 1780;   // 1920 menos los paddings laterales
	const AREA_H = 640;    // lo que sobra entre el título y la nota del pie
	const rejilla = $derived.by(() => {
		const n = conRegistro.length;
		if (!n) return { cols: 1, filas: 1, lado: 0, visibles: 0 };
		// Máximo 24 en pantalla: más de eso ya no es una pantalla, es una tabla.
		const visibles = Math.min(n, 24);
		let cols = Math.ceil(Math.sqrt(visibles));
		cols = Math.max(1, Math.min(6, cols, visibles));
		const filas = Math.ceil(visibles / cols);
		const lado = Math.min(
			Math.floor((AREA_W - (cols - 1) * 14) / cols),
			Math.floor((AREA_H - (filas - 1) * 14) / filas),
			LADO_MAX
		);
		return { cols, filas, lado, visibles };
	});
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

	{#if !conRegistro.length}
		<div class="vacio">
			Todavía nadie ha registrado movimientos hoy
			<span class="vacio-sub">
				Aquí aparece cada persona en cuanto su equipo o celular conocido se
				conecta a la red de la oficina
			</span>
		</div>
	{:else}
		<!--
			Rejilla de CUADRADOS con el lado calculado: se eligen las columnas a
			partir de cuántas personas hay y de ahí el lado, para que todas quepan
			a la vez sin scrolls ni huecos raros.
		-->
		<div
			class="rejilla"
			style="--cols:{rejilla.cols};--filas:{rejilla.filas};--lado:{rejilla.lado}px"
		>
			{#each conRegistro.slice(0, rejilla.visibles) as p (p.id_usuario)}
				<article class="tarjeta" class:en-sitio={p.en_sitio} class:fuera={!p.en_sitio}>
					<div class="avatar">
						{#if p.avatar}
							<img src={avatarSrc(p.avatar)} alt="" />
						{:else}
							<div class="ph">{iniciales(p.nombre)}</div>
						{/if}
					</div>
					<div class="nombre">{p.nombre}</div>

					<div class="horas">
						<div class="hora llegada">
							<span class="rot">Llegó</span>
							<span class="hhmm">{hhmm(p.entrada)}</span>
						</div>
						<!--
							La salida sólo si ya se fue. Si sigue en la oficina esa
							hora todavía no existe, y rayitas o "—" se leen igual que
							un dato: mejor la fila no está.
						-->
						{#if !p.en_sitio && p.salida}
							<div class="hora ida">
								<span class="rot">Se fue</span>
								<span class="hhmm">{hhmm(p.salida)}</span>
							</div>
						{/if}
					</div>
				</article>
			{/each}

			{#if conRegistro.length > rejilla.visibles}
				<div class="sobran" style="--lado:{rejilla.lado}px">
					+{conRegistro.length - rejilla.visibles}
					<span>más</span>
				</div>
			{/if}
		</div>
	{/if}

	<!--
		La aclaración va FUERA del `{#if}` de arriba a propósito: tiene que leerse
		también cuando todavía no sale nadie, porque es justo cuando alguien
		mira la pantalla vacía y necesita saber por qué.
	-->
	<p class="nota">
		<i class="nota-ic">ℹ</i>
		<span>
			Los horarios se calculan solos a partir de la red de la oficina (cuando
			un equipo o celular conocido se conecta), por lo que pueden variar
			algunos minutos y no siempre detectan todas las entradas ni todas las
			salidas.
			<b>Es información orientativa, no un registro oficial de asistencia.</b>
		</span>
	</p>
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
	/*
		Cuadrados con el lado ya calculado en el script (--lado). Se usa
		`grid-template` explícito en vez de `auto-fit` porque el lado depende de
		cuántas personas hay: con `auto-fit` el navegador decide y o quedan
		tarjetas minúsculas con huecos, o se desbordan.
	*/
	.rejilla {
		flex: 1;
		min-height: 0;
		display: grid;
		grid-template-columns: repeat(var(--cols, 4), var(--lado, 280px));
		grid-template-rows: repeat(var(--filas, 2), var(--lado, 280px));
		gap: 14px;
		justify-content: center;
		align-content: center;
	}

	/*
		Una tarjeta = una persona con registro hoy. El color entero dice si
		sigue aquí o ya se fue, que es lo que se lee a 3 metros; las dos horas
		van adentro, la de llegada siempre y la de salida sólo si ya se fue.
	*/
	.tarjeta {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 3px;
		padding: calc(var(--lado) * 0.05);
		text-align: center;
		overflow: hidden;
		border-radius: 18px;
		animation: entrarStagger 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
	}
	.tarjeta.en-sitio {
		background: linear-gradient(160deg, rgba(34, 197, 94, 0.3) 0%, rgba(22, 163, 74, 0.15) 100%);
		border: 1px solid rgba(74, 222, 128, 0.55);
		box-shadow: inset 0 0 40px rgba(34, 197, 94, 0.14);
	}
	.tarjeta.fuera {
		background: linear-gradient(160deg, rgba(239, 68, 68, 0.3) 0%, rgba(185, 28, 28, 0.15) 100%);
		border: 1px solid rgba(248, 113, 113, 0.5);
		box-shadow: inset 0 0 40px rgba(239, 68, 68, 0.12);
	}

	/*
		TODO el interior se mide contra `--lado`, no con px fijos. Con 9 personas
		el cuadrado sale de 204 px y con 2 de 360: si el texto fuera fijo, en el
		caso chico los nombres se cortaban ("Priscila …") y la tarjeta de dos
		horas se desbordaba por arriba. Los `max()` son el piso de legibilidad
		para cuando hay muchas personas.
	*/
	.avatar {
		width: calc(var(--lado) * 0.22);
		aspect-ratio: 1;
		margin-bottom: 3px;
		border-radius: 50%;
		overflow: hidden;
		background: rgba(0, 0, 0, 0.3);
		display: grid;
		place-items: center;
	}
	.avatar img { width: 100%; height: 100%; object-fit: cover; }
	.ph { font-size: calc(var(--lado) * 0.1); font-weight: 800; color: rgba(255,255,255,0.75); }

	.nombre {
		font-size: max(20px, calc(var(--lado) * 0.105));
		line-height: 1.12;
		font-weight: 800;
		color: #fff;
		/* Hasta DOS líneas: "Priscila Urbina" no cabe en una línea de 204 px y
		   recortarla a "Priscila …" en una pantalla de pasillo es peor que
		   partiarla. A la tercera línea se corta. */
		max-width: 100%;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
		text-shadow: 0 2px 14px rgba(0, 0, 0, 0.5);
	}
	/* Las dos horas, apiladas y del ancho del cuadro. La etiqueta pequeña a la
	   izquierda y la hora grande a la derecha: en un cuadrado de 360 px, poner
	   la hora centrada con la etiqueta encima se come la mitad del alto. */
	.horas {
		display: flex;
		flex-direction: column;
		gap: 3px;
		width: 100%;
		margin-top: 3px;
	}
	.hora {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 6px;
		padding: 2px 8px;
		border-radius: 8px;
		background: rgba(2, 6, 23, 0.34);
		border: 1px solid rgba(255, 255, 255, 0.1);
	}
	.rot {
		font-size: max(10px, calc(var(--lado) * 0.048));
		font-weight: 800;
		letter-spacing: 0.16em;
		text-indent: 0.16em;
		text-transform: uppercase;
		color: rgba(255, 255, 255, 0.6);
		flex-shrink: 0;
	}
	.hhmm {
		font-size: max(28px, calc(var(--lado) * 0.15));
		font-weight: 900;
		line-height: 1.05;
		color: #fff;
		font-variant-numeric: tabular-nums;
	}
	/* La hora de salida se tiñe para que con el rótulo al lado no haga falta
	   leer: verde = sigue aquí, rojo = ya salió. */
	.llegada .hhmm { color: #86efac; }
	.ida .hhmm { color: #fca5a5; }

	/* "+N más": pasa de la lista a la tabla cuando ya no caben. */
	.sobran {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2px;
		font-size: max(30px, calc(var(--lado) * 0.16));
		font-weight: 900;
		color: #94a3b8;
		border: 1px dashed rgba(148, 163, 184, 0.35);
		border-radius: 18px;
	}
	.sobran span {
		font-size: max(10px, calc(var(--lado) * 0.05));
		font-weight: 700;
		letter-spacing: 0.2em;
		text-transform: uppercase;
		color: #64748b;
	}

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
