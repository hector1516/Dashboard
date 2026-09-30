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
		Sólo quien YA SE FUE, y sólo su hora de salida. Lo pidió el usuario y
		tiene lógica: la pregunta útil de esta pantalla al final del día es
		"¿a qué hora se fue cada quien?", no "a qué hora llegó" (eso ya lo
		dice el reloj de la entrada) ni "quién sigue aquí" (eso se ve con que
		no esté en la lista).

		`!en_sitio` es la condición: el backend marca en_sitio cuando el ÚLTIMO
		evento del día fue una ENTRADA, así que quien sale y vuelve termina con
		la salida anterior como dato viejo. Filtra aquí y no en el backend para
		que la lista siga siendo la misma para quien la consume de otra parte.
	*/
	const salidos = $derived(
		personas.filter((p) => !p.en_sitio && p.salida)
	);
	const extras = $derived(Math.max(0, personas.length - salidos.length));

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
		const n = salidos.length;
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
		<span class="ic">🕘</span> Salidas de hoy
		{#if a?.total}
			<span class="contador">
				<span class="fuera">{(a.salieron ?? 0).toString().padStart(2, '0')} ya se fueron</span>
				·
				<span class="dentro">🟢 {(a.dentro ?? 0).toString().padStart(2, '0')} todavía aquí</span>
			</span>
		{/if}
	</div>

	{#if !salidos.length}
		<div class="vacio">
			Todavía no sale nadie hoy
			<span class="vacio-sub">
				Aquí aparece cada persona en cuanto su equipo o celular se desconecta
				de la red de la oficina, con la hora
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
			{#each salidos.slice(0, rejilla.visibles) as p (p.id_usuario)}
				<article class="tarjeta">
					<div class="avatar">
						{#if p.avatar}
							<img src={avatarSrc(p.avatar)} alt="" />
						{:else}
							<div class="ph">{iniciales(p.nombre)}</div>
						{/if}
					</div>
					<div class="nombre">{p.nombre}</div>
					<div class="rotulo">Se fue</div>
					<div class="hhmm">{hhmm(p.salida)}</div>
				</article>
			{/each}

			{#if salidos.length > rejilla.visibles}
				<div class="sobran" style="--lado:{rejilla.lado}px">
					+{salidos.length - rejilla.visibles}
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
		Una tarjeta = una persona que ya se fue. Roja (se fue), que es la única
		información que tiene; el rojo es la misma señal de antes, ahora sin la
		competencia del verde porque nadie "sigue aquí" en esta pantalla.
	*/
	.tarjeta {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2px;
		padding: 10px;
		text-align: center;
		overflow: hidden;
		background: linear-gradient(160deg, rgba(239, 68, 68, 0.3) 0%, rgba(185, 28, 28, 0.15) 100%);
		border: 1px solid rgba(248, 113, 113, 0.5);
		border-radius: 18px;
		box-shadow: inset 0 0 40px rgba(239, 68, 68, 0.12);
		animation: entrarStagger 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
	}

	.avatar {
		width: 30%;
		aspect-ratio: 1;
		max-width: 122px;
		margin-bottom: 6px;
		border-radius: 50%;
		overflow: hidden;
		background: rgba(0, 0, 0, 0.3);
		display: grid;
		place-items: center;
	}
	.avatar img { width: 100%; height: 100%; object-fit: cover; }
	.ph { font-size: 34px; font-weight: 800; color: #fca5a5; }

	.nombre {
		font-size: 34px;
		font-weight: 800;
		color: #fff;
		/* Un nombre largo se recorta con puntos suspensivos en vez de romper el
		   cuadrado: la tarjeta es cuadrada sí o sí. */
		max-width: 100%;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		text-shadow: 0 2px 14px rgba(0, 0, 0, 0.5);
	}
	.rotulo {
		font-size: 16px;
		font-weight: 800;
		letter-spacing: 0.24em;
		text-indent: 0.24em;
		text-transform: uppercase;
		color: rgba(255, 255, 255, 0.62);
		margin-top: 2px;
	}
	.hhmm {
		font-size: 72px;
		font-weight: 900;
		line-height: 1;
		color: #fca5a5;
		font-variant-numeric: tabular-nums;
		text-shadow: 0 0 30px rgba(239, 68, 68, 0.45);
	}

	/* "+N más": pasa de la lista a la tabla cuando ya no caben. */
	.sobran {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 2px;
		font-size: 54px;
		font-weight: 900;
		color: #94a3b8;
		border: 1px dashed rgba(148, 163, 184, 0.35);
		border-radius: 18px;
	}
	.sobran span {
		font-size: 15px;
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
