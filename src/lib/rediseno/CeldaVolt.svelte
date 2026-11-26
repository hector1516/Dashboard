<script lang="ts">
	// La celda que llena el hueco inferior derecho de la retícula: The Penguin
	// (Pebble, el pingüino 3D de Wobnimo) y sus últimas tres notificaciones,
	// cada una con su hora.
	//
	// El personaje vive DENTRO de la celda, no en un dock fijo: se va con la
	// pantalla y no tapa la retícula. Si el import o el montaje fallan, queda
	// el 🐧 de respaldo.
	//
	// El historial lo llena `voltAviso.ts`: presencia, tickets, avisos del
	// vigilante y «sin internet». Aquí sólo se pinta, sin peticiones propias.
	//
	// Animaciones: Wobnimo acepta exactamente `idle`, `happy`, `sad`,
	// `speaking` y `sleeping`. La base es `happy` en Equipo (cumples y
	// aniversarios) e `idle` en el resto; un aviso nuevo lo pone `happy` 3 s y
	// de vez en cuando se duerme solo (nunca en Equipo ni recién avisado).
	// `?sinanim=1` lo deja clavado en la base, para capturas.
	import { onMount } from 'svelte';
	import Celda from './Celda.svelte';
	import { voltHistorial, type AvisoVolt } from '$lib/kiosk/voltAviso';
	import { currentScreen } from '$lib/kiosk/currentScreen';

	interface Props {
		/**
		 * Área de la retícula. El hueco normal es 3/4/4/5; en Equipo el hueco
		 * es de dos columnas (3/3/4/5) y se pasa ese valor para no dejar un
		 * segundo recuadro vacío.
		 */
		area?: string;
		/** Orden de la animación de caída. Va al final de la retícula. */
		i?: number;
	}
	let { area = '3/4/4/5', i = 9 }: Props = $props();

	let avisos = $state<AvisoVolt[]>([]);
	/** Caja donde Wobnimo crea su `<canvas>`. */
	let escena: HTMLDivElement | null = $state(null);
	/** El personaje 3D ya está montado: se esconde el 🐧 de respaldo. */
	let montado = $state(false);

	/** Instancia de Wobnimo (`mount()`): setState y dispose. */
	type Mascota = { setState?: (estado: string) => void; dispose?: () => void };
	let mascota: Mascota | null = null;

	/** ¿La pantalla visible es Equipo? Ahí celebra sin parar. */
	let fiesta = false;
	/** `?sinanim=1`: ni avisos ni siestas; se queda en el estado base. */
	let sinAnim = false;

	/** Vuelve a la base cuando termina la celebración de un aviso. */
	let regreso: ReturnType<typeof setTimeout> | null = null;
	/** Fin de una siesta; su presencia bloquea otras animaciones. */
	let siesta: ReturnType<typeof setTimeout> | null = null;
	/** Reloj que decide de vez en cuando si toca dormir. */
	let revisor: ReturnType<typeof setInterval> | null = null;
	/** Momento del último aviso: no se duerme si acaba de sonar. */
	let ultimoAviso = 0;

	/** Lo último que se vio en el historial: una fila nueva dispara `happy`. */
	let visto: string | null = null;

	/**
	 * Gesto festivo. La compilación que trae Wobnimo valida contra su lista
	 * pública y esa lista no incluye `happy`, aunque el personaje sí lo dibuja
	 * (y `pebble.js` le da movimiento). Se intenta `happy`; si lo rechaza se
	 * usa `celebrating`, que es su gesto festivo real.
	 */
	let festejo: 'happy' | 'celebrating' = 'happy';

	/** `happy` es lo único que puede necesitar respaldo en esta compilación. */
	function poner(estado: 'happy' | 'idle' | 'sleeping') {
		if (!mascota?.setState) return;
		const real = estado === 'happy' ? festejo : estado;
		try {
			mascota.setState(real);
		} catch {
			if (estado !== 'happy') return;
			festejo = 'celebrating';
			mascota.setState(festejo);
		}
	}

	/** Estado en reposo: `happy` en Equipo, `idle` en cualquier otra. */
	function estadoBase(): 'happy' | 'idle' {
		return fiesta ? 'happy' : 'idle';
	}

	/** Vuelve a la base, salvo que haya un aviso o una siesta en curso. */
	function alBase() {
		if (!mascota?.setState) return;
		if (regreso || siesta) return;
		poner(estadoBase());
	}

	function celebrar() {
		if (sinAnim || !mascota?.setState) return;
		ultimoAviso = Date.now();
		// Un aviso despierta al personaje.
		if (siesta) {
			clearTimeout(siesta);
			siesta = null;
		}
		poner('happy');
		if (regreso) clearTimeout(regreso);
		regreso = setTimeout(() => {
			regreso = null;
			alBase();
		}, 3000);
	}

	/** Cada ~30 s: 40 % de probabilidad de echarse una siesta de 6–10 s. */
	function quizaDormir() {
		if (sinAnim || fiesta || !mascota?.setState) return;
		if (regreso || siesta) return;
		if (Date.now() - ultimoAviso < 10_000) return;
		if (Math.random() > 0.4) return;
		poner('sleeping');
		const ms = 6000 + Math.random() * 4000;
		siesta = setTimeout(() => {
			siesta = null;
			alBase();
		}, ms);
	}

	async function montarPersonaje() {
		if (!escena) return;
		// Se sirve del propio contenedor (`static/vendor`), no de un CDN: la
		// regla del kiosco es no depender de internet. El `@vite-ignore` deja
		// la URL literal para que Vite no intente empaquetarla.
		const base = '/vendor/wobnimo';
		try {
			const [wobnimo, penguinModule] = await Promise.all([
				import(/* @vite-ignore */ `${base}/wobnimo.js`),
				// Pebble es el pingüino de Wobnimo: es The Penguin.
				import(/* @vite-ignore */ `${base}/characters/pebble.js`)
			]);
			if (!escena || !wobnimo?.mount || !penguinModule?.pebble) return;
			const instancia = wobnimo.mount(escena, penguinModule.pebble) as Mascota;
			// La celda pudo desmontarse mientras cargaba el módulo.
			if (!escena?.isConnected) {
				instancia.dispose?.();
				return;
			}
			mascota = instancia;
			poner(estadoBase());
			montado = true;
		} catch (e) {
			// Sin personaje 3D la celda no queda vacía: sigue el 🐧.
			console.error('The Penguin 3D no cargó; queda el 🐧 de respaldo', e);
		}
	}

	onMount(() => {
		sinAnim = new URLSearchParams(window.location.search).get('sinanim') === '1';

		const soltar = voltHistorial.subscribe((v) => {
			avisos = v;
			const frente = v[0];
			const marca = frente ? `${frente.hora}·${frente.texto}` : '';
			// La primera foto es lo que ya había al entrar: no se celebra. A
			// partir de ahí, cualquier fila nueva (o el primero que llega a una
			// lista vacía) pone al personaje contento.
			if (visto === null) {
				visto = marca;
				return;
			}
			if (marca && marca !== visto) celebrar();
			visto = marca;
		});

		// Al entrar a Equipo celebra de inmediato (la base ya es `happy`); al
		// salir, vuelve a `idle` y se le permite dormir otra vez.
		const soltarPantalla = currentScreen.subscribe((id) => {
			const antes = fiesta;
			fiesta = id === 'equipo';
			if (fiesta && !antes) {
				if (regreso) {
					clearTimeout(regreso);
					regreso = null;
				}
				if (siesta) {
					clearTimeout(siesta);
					siesta = null;
				}
			}
			alBase();
		});

		revisor = setInterval(quizaDormir, 30_000);
		void montarPersonaje();

		return () => {
			soltar();
			soltarPantalla();
			if (revisor) clearInterval(revisor);
			if (regreso) clearTimeout(regreso);
			if (siesta) clearTimeout(siesta);
			mascota?.dispose?.();
			mascota = null;
		};
	});
</script>

<Celda {area} {i} rotulo="The Penguin · últimas notificaciones">
	<div class="volt">
		<!-- El personaje a la izquierda. `aria-hidden`: es la mascota, no un
		     dato; lo que se lee son los avisos de la derecha. -->
		<div class="escena" aria-hidden="true">
			<div class="personaje" bind:this={escena}></div>
			{#if !montado}
				<!-- Respaldo: si Wobnimo no carga queda el 🐧, no un hueco. -->
				<div class="marca"><span class="pinguino">🐧</span></div>
			{/if}
		</div>

		{#if avisos.length === 0}
			<div class="sin-avisos">
				<b>Sin novedades</b>
				<span>Los avisos de The Penguin aparecerán aquí.</span>
			</div>
		{:else}
			<div class="lista">
				{#each avisos as a, n (a.texto + n)}
					<div class="fila">
						<span class="texto">{a.texto}</span>
						<span class="hora">{a.hora}</span>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</Celda>

<style>
	/* Personaje a la izquierda y avisos a la derecha, en la misma fila. La
	   celda 1×1 mide ~446×289 con 24/28 de relleno: quedan ~208 px de alto,
	   sitio de sobra para 112 px de personaje y tres filas de 20 px. */
	.volt {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: row;
		align-items: flex-start;
		gap: 16px;
	}

	/* La caja del personaje. 112 px, como la placa que tenía en el dock, y
	   nunca se estira ni se encoge: si el contenido aprieta, se recorta la
	   lista (con elipsis), no la letra. */
	.escena {
		position: relative;
		flex: 0 0 112px;
		width: 112px;
		height: 112px;
		border-radius: 24px;
		background: radial-gradient(circle at 50% 38%, #eef2fb 0%, #f7f8fc 62%, rgba(18, 20, 26, 0.03) 100%);
		overflow: hidden;
	}
	.personaje {
		position: absolute;
		inset: 0;
	}
	/* El canvas de Wobnimo ya llena la caja; sin interacción: la TV no tiene
	   ratón y el personaje no debe robar clics. */
	.personaje :global(canvas) {
		pointer-events: none;
	}

	/* Respaldo: el pingüino en un círculo naranja de marca, centrado en la
	   misma caja. */
	.marca {
		position: absolute;
		inset: 0;
		margin: auto;
		width: 78px;
		height: 78px;
		border-radius: 50%;
		background: var(--k-rojo);
		color: var(--k-tinta);
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 2px 0 rgba(18, 20, 26, 0.08);
	}
	.pinguino {
		font-size: 40px;
		line-height: 1;
	}

	.lista {
		flex: 1;
		min-width: 0;
		min-height: 0;
		display: flex;
		flex-direction: column;
		justify-content: center;
		gap: 0;
	}
	.fila {
		display: flex;
		align-items: flex-start;
		gap: 10px;
		padding: 5px 0;
		border-bottom: 1px solid rgba(18, 20, 26, 0.08);
	}
	.fila:last-child {
		border-bottom: 0;
	}
	/* 20 px: el mínimo del sistema. Dos líneas como tope y elipsis; la hora
	   no se parte ni se recorta. */
	.texto {
		flex: 1;
		min-width: 0;
		font-size: 20px;
		font-weight: 600;
		line-height: 1.2;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	.hora {
		flex: 0 0 auto;
		font-size: 20px;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
		/* Gris legible sobre blanco: 4.6:1. */
		color: rgba(18, 20, 26, 0.55);
		padding-top: 1px;
	}

	.sin-avisos {
		flex: 1;
		min-width: 0;
		margin: auto 0;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.sin-avisos b {
		font-size: 24px;
		font-weight: 800;
		opacity: 0.45;
	}
	.sin-avisos span {
		font-size: 20px;
		font-weight: 600;
		opacity: 0.4;
	}
</style>
