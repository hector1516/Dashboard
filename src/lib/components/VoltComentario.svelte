<script lang="ts">
	import { mascotState } from '$lib/kiosk/mascot';
	import { getVoltComentario, getVoltComentarioPantalla } from '$lib/kiosk/voltComentarios';
	import { pauseWalking, resumeWalking } from '$lib/kiosk/voltWalker';
	import { currentScreen } from '$lib/kiosk/currentScreen';
	import { tocar } from '$lib/kiosk/audio';
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';

	/**
	 * El globo de Volt NO se esconde: cambia lo que dice, pero se queda en su
	 * esquina. El orden de prioridad es el que importa:
	 *
	 *   1. Aviso nuevo del vigilante (lo mismo que se mandó por Telegram).
	 *   2. No hay internet (lo detecta el servidor: clima y fondos son la
	 *      señal; el kiosco no llama a internet para averiguarlo).
	 *   3. Charla normal de la pantalla o del momento del día.
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
	const SIN_INTERNET =
		'Sin internet por aquí. Lo de la oficina sigue andando; el clima y los fondos se quedan como estaban. Te aviso en cuanto vuelva.';
	const VOLVIO = '¡Volvió el internet! Ya puedo traer el clima y los fondos otra vez.';

	let texto = $state('Hola, soy Volt. Aquí ando, por si me necesitas.');
	let reaccion = $state('💬');
	let sinInternet = $state(false);
	let pendientes = $state<Aviso[]>([]);
	let volvio = false;

	let timer: ReturnType<typeof setTimeout>;
	let carga: ReturnType<typeof setInterval>;
	let ultimoAviso = 0;

	const REACCIONES = ['💬', '🤔', '😊', '⚡', '🤖', '💡', '🎯', '👀', '🔥', '✨', '🎉', '☕'];

	function hablar(t: string, r: string) {
		texto = t;
		reaccion = r;
		pauseWalking();
		mascotState.set('speaking');
		// Volt habla: dos notas amables. `tocar()` ya respeta el mute y el
		// silencio de 22:00 a 07:00, así que aquí no se comprueba nada más.
		tocar('volt');
		setTimeout(() => {
			mascotState.set('idle');
			resumeWalking();
		}, 3500);
	}

	function siguiente() {
		if (volvio) {
			volvio = false;
			hablar(VOLVIO, '🌐');
		} else if (sinInternet) {
			hablar(SIN_INTERNET, '📡');
		} else if (pendientes.length) {
			const aviso = pendientes[0];
			pendientes = pendientes.slice(1);
			ultimoAviso = Math.max(ultimoAviso, aviso.id);
			if (browser) localStorage.setItem(CLAVE_ULTIMO, String(ultimoAviso));
			hablar(aviso.texto, aviso.nivel === 'rojo' ? '⚠️' : '👀');
		} else {
			const screen = $currentScreen;
			let t: string;
			if (Math.random() < 0.5 && screen) {
				t = getVoltComentarioPantalla(screen);
			} else {
				const tipos = ['idle', 'entrada', 'salida', 'usuario_nuevo', 'usuario_inactivo'];
				t = getVoltComentario(tipos[Math.floor(Math.random() * tipos.length)]);
			}
			hablar(t, REACCIONES[Math.floor(Math.random() * REACCIONES.length)]);
		}
		timer = setTimeout(siguiente, sinInternet ? 22000 : 11000 + Math.random() * 8000);
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
			if (!ahora && antes) volvio = true;
			sinInternet = ahora;

			const lista: Aviso[] = (d.avisos || []).slice().sort((a: Aviso, b: Aviso) => a.id - b.id);
			if (!ultimoAviso && lista.length) {
				// Primer arranque del kiosco: la historia no se cuenta.
				ultimoAviso = lista[lista.length - 1].id;
				if (browser) localStorage.setItem(CLAVE_ULTIMO, String(ultimoAviso));
			}
			const ya = new Set(pendientes.map((a) => a.id));
			for (const a of lista) {
				if (a.id > ultimoAviso && !ya.has(a.id)) {
					pendientes.push(a);
					ya.add(a.id);
				}
			}
			pendientes.sort((a, b) => a.id - b.id);
			// Un aviso del vigilante pesa más que la charla: sale ya.
			if (pendientes.length && !sinInternet) {
				clearTimeout(timer);
				timer = setTimeout(siguiente, 1200);
			}
		} catch {
			// Sin red local no se inventa nada: el último texto se queda.
		}
	}

	onMount(() => {
		if (browser) ultimoAviso = Number(localStorage.getItem(CLAVE_ULTIMO) || 0) || 0;
		cargar();
		carga = setInterval(cargar, 60000);
		timer = setTimeout(siguiente, 4000);

		const alCambiarRed = () => cargar();
		window.addEventListener('online', alCambiarRed);
		window.addEventListener('offline', alCambiarRed);

		return () => {
			window.removeEventListener('online', alCambiarRed);
			window.removeEventListener('offline', alCambiarRed);
		};
	});

	onDestroy(() => {
		clearTimeout(timer);
		clearInterval(carga);
	});
</script>

<!-- Siempre visible: el texto cambia con un fundido corto, pero el globo no
     se va a ningún lado. -->
<div class="volt-comentario">
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
