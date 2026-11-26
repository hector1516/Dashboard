<script lang="ts">
	import { mascotState } from '$lib/kiosk/mascot';
	import { pauseWalking, resumeWalking } from '$lib/kiosk/voltWalker';
	import { tocar } from '$lib/kiosk/audio';
	import { voltAviso } from '$lib/kiosk/voltAviso';
	import { onMount, onDestroy } from 'svelte';
	import { fade } from 'svelte/transition';
	import { browser } from '$app/environment';

	/**
	 * El globo de Volt aparece SÓLO cuando tiene algo que notificar:
	 *
	 *   1. Aviso nuevo del vigilante (lo mismo que se mandó por Telegram).
	 *   2. No hay internet (lo detecta el servidor: clima y fondos son la
	 *      señal; el kiosco no llama a internet para averiguarlo).
	 *   3. Volvió el internet.
	 *   4. Un aviso corto de otro módulo (entrada/salida de la oficina,
	 *      ticket nuevo) que llega por `voltAviso`.
	 *
	 * No hay charla aleatoria ni comentarios de pantalla: si no hay nada que
	 * decir, no se muestra. Cuando sale, se queda ~11 s, se va con un fundido
	 * y no vuelve hasta la siguiente notificación.
	 *
	 * Lo que ya se dijo no se repite al recargar: el último id visto vive en
	 * localStorage. La primera vez que arranca no escupe 8 avisos viejos.
	 */
	interface Aviso {
		id: number;
		texto: string;
		nivel: string;
		tipo?: string;
		fecha?: string | null;
	}

	const CLAVE_ULTIMO = 'volt:ultimoAviso';
	/** Dentro de la ventana pedida (10–12 s) con algo de aire entre avisos. */
	const MS_VISIBLE = 10_500;
	const MS_VISIBLE_VARIA = 1_500;
	const SIN_INTERNET =
		'Sin internet por aquí. Lo de la oficina sigue andando; el clima y los fondos se quedan como estaban. Te aviso en cuanto vuelva.';
	const VOLVIO = '¡Volvió el internet! Ya puedo traer el clima y los fondos otra vez.';

	let texto = $state('');
	let reaccion = $state('⚡');
	let visible = $state(false);
	/** null = todavía no se sabe; el primer sondeo no avisa de "volvió". */
	let sinInternet: boolean | null = null;

	let ocultar: ReturnType<typeof setTimeout> | undefined;
	let carga: ReturnType<typeof setInterval> | undefined;
	let ultimoAviso = 0;
	/**
	 * La voz de Volt sólo suena cuando aparece una notificación y, aun así,
	 * como máximo una vez por minuto. Todo pasa por `tocar()`, que respeta el
	 * mute y el silencio nocturno.
	 */
	const MS_ENTRE_VOCES = 60_000;
	let ultimaVoz = 0;

	function tonoVolt() {
		const ahora = Date.now();
		if (ahora - ultimaVoz < MS_ENTRE_VOCES) return;
		ultimaVoz = ahora;
		tocar('volt');
	}

	function guardarUltimo() {
		if (browser) localStorage.setItem(CLAVE_ULTIMO, String(ultimoAviso));
	}

	function mostrar(t: string, r: string) {
		texto = t;
		reaccion = r;
		visible = true;
		pauseWalking();
		mascotState.set('speaking');
		tonoVolt();
		clearTimeout(ocultar);
		ocultar = setTimeout(ocultarGlobo, MS_VISIBLE + Math.random() * MS_VISIBLE_VARIA);
	}

	function ocultarGlobo() {
		visible = false;
		mascotState.set('idle');
		resumeWalking();
	}

	async function cargar() {
		try {
			const r = await fetch('/api/dashboard/volt', { cache: 'no-store' });
			if (!r.ok) return;
			const d: any = await r.json();

			// El servidor manda si hay salida a internet (clima + fondos). El
			// navegador solo puede decir si la TV perdió la red local.
			const antes = sinInternet;
			const ahora = !!d.sin_internet || (typeof navigator !== 'undefined' && navigator.onLine === false);
			sinInternet = ahora;

			const lista: Aviso[] = (d.avisos || []).slice().sort((a: Aviso, b: Aviso) => a.id - b.id);
			let nuevo: Aviso | null = null;
			if (lista.length) {
				if (!ultimoAviso) {
					// Primer arranque del kiosco: la historia no se cuenta.
					ultimoAviso = lista[lista.length - 1].id;
					guardarUltimo();
				} else {
					const frescos = lista.filter((a) => a.id > ultimoAviso);
					if (frescos.length) {
						// Si llegaron varios, el que importa es el último: el
						// resto ya es historia y no se repite en cadena.
						nuevo = frescos[frescos.length - 1];
						ultimoAviso = nuevo.id;
						guardarUltimo();
					}
				}
			}

			if (nuevo) {
				mostrar(nuevo.texto, nuevo.nivel === 'rojo' ? '⚠️' : '👀');
			} else if (antes === true && !ahora) {
				mostrar(VOLVIO, '🌐');
			} else if (ahora && antes !== true) {
				mostrar(SIN_INTERNET, '📡');
			}
		} catch {
			// Sin red local no se inventa nada: el globo se queda como está.
		}
	}

	onMount(() => {
		if (browser) ultimoAviso = Number(localStorage.getItem(CLAVE_ULTIMO) || 0) || 0;
		cargar();
		carga = setInterval(cargar, 60000);

		// Avisos cortos que otros módulos dejan para Volt. Se consume uno y el
		// buzón vuelve a null: al recargar la pantalla no se repite el último.
		const dejarDeEscuchar = voltAviso.subscribe((v) => {
			if (!v) return;
			mostrar(v.texto, v.reaccion ?? '💬');
			voltAviso.set(null);
		});

		const alCambiarRed = () => cargar();
		window.addEventListener('online', alCambiarRed);
		window.addEventListener('offline', alCambiarRed);

		return () => {
			dejarDeEscuchar();
			window.removeEventListener('online', alCambiarRed);
			window.removeEventListener('offline', alCambiarRed);
		};
	});

	onDestroy(() => {
		clearTimeout(ocultar);
		clearInterval(carga);
		if (visible) {
			mascotState.set('idle');
			resumeWalking();
		}
	});
</script>

<!-- Sólo existe en el DOM mientras hay una notificación. Al ocultarse no
     queda nada montado: no hay globo fijo ni texto de relleno. -->
{#if visible}
	<div
		class="volt-comentario"
		role="status"
		aria-live="polite"
		transition:fade={{ duration: 240 }}
	>
		<div class="comentario-avatar">
			<span class="avatar-icon">🤖</span>
		</div>
		<div class="comentario-bubble">
			{#key texto}
				<span class="comentario-reaccion">{reaccion}</span>
				<span class="comentario-texto">{texto}</span>
			{/key}
		</div>
		<div class="comentario-flecha"></div>
	</div>
{/if}

<style>
	/* El globo vive ENCIMA de la placa de Volt, pegado a la esquina: no sigue a
	   nadie y no puede caer sobre el centro de la pantalla. */
	.volt-comentario {
		position: fixed;
		right: 18px;
		bottom: 142px;
		z-index: 401;
		max-width: 380px;
		pointer-events: none;
		animation: entraComentario 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 4px;
	}

	.comentario-avatar {
		width: 40px;
		height: 40px;
		border-radius: 50%;
		/* Rojo ECCSA muy suave: el avatar pertenece al globo, no compite. */
		background: rgba(228, 0, 43, 0.1);
		border: 1px solid rgba(228, 0, 43, 0.18);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.4rem;
		box-shadow: 0 4px 12px rgba(18, 20, 26, 0.1);
	}

	/* Cristal como las celdas del bento: blanco translúcido, no un bloque
	   oscuro. El texto es tinta con algo de transparencia para que se lea
	   «encima» de la tarjeta y no pintado sobre ella. */
	.comentario-bubble {
		background: rgba(255, 255, 255, 0.72);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		border: 1px solid rgba(18, 20, 26, 0.08);
		border-radius: 18px;
		padding: 14px 20px;
		color: #12141a;
		font-size: 20px;
		box-shadow: 0 10px 30px rgba(18, 20, 26, 0.1);
		display: flex;
		align-items: flex-start;
		gap: 8px;
		max-width: 380px;
	}

	.comentario-reaccion {
		font-size: 1.3rem;
		flex-shrink: 0;
		line-height: 1.2;
		animation: fundido 0.35s ease both;
	}

	.comentario-texto {
		line-height: 1.35;
		opacity: 0.85;
		animation: fundido 0.35s ease both;
	}

	@keyframes fundido {
		from { opacity: 0; }
		to { opacity: 1; }
	}

	.comentario-flecha {
		width: 0;
		height: 0;
		border-left: 9px solid transparent;
		border-right: 9px solid transparent;
		border-top: 9px solid rgba(255, 255, 255, 0.72);
		margin-top: -1px;
	}

	@keyframes entraComentario {
		from { opacity: 0; transform: translateY(10px) scale(0.94); }
		to { opacity: 1; transform: none; }
	}
</style>
