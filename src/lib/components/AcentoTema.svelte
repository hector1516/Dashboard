<!--
	🌙 Adornos del tema del mes, en TODAS las pantallas.

	Por qué existe aparte de la capa de fondo (`Fondo.svelte` → `temas.py`):
	el fondo tiene que dejar ver la foto de Bing —si no, lo único que se ve es
	un lavado de color— y un lavado nunca dice "es el mes de septiembre". Lo que
	lo dice son las formas: un banderín, una calavera, un árbol. Este componente
	pone esas formas en las esquinas, fuera de las zonas de texto.

	Decisiones de diseño, y por qué:

	· Va en la ESQUINA INFERIOR IZQUIERDA, no en la superior. La superior
	  izquierda la ocupa el widget de cumpleaños (`WidgetCumple`, z-index 40), la
	  derecha el clima, y abajo está el pie. Abajo-izquierda es lo único que
	  queda libre en las doce pantallas, y es donde la mirada no está.
	· `pointer-events: none`: es decoración, si se puede hacer clic encima de un
	  adorno es un bug.
	· Opacidad baja (0.5) y tamaño mediano: se ven desde el otro lado de la
	  oficina sin competir con los datos. Si un adorno se lee mejor que el
	  número de una tarjeta, es un adorno demasiado grande.
	· Sólo los MESES con motivo propio lleva adornos. En mayo, por ejemplo, no
	  hay nada que poner: la semana santa no es de mayo y forzar un adorno sería
	  inventar una fiesta que no es. Mejor un mes sin adorno que uno con la
	  fecha corrida.
	· Se apaga con `?sinanim=1`, igual que el resto del cromo de verificación.
-->
<script lang="ts">
	interface Props {
		/** El tema del mes, ya resuelto (con `?tema=N` forzado si viene). */
		tema?: { mes: number; nombre: string; icono: string; tinte: string } | null;
		/** Sin animaciones: para capturas de verificación. */
		sinAnim?: boolean;
	}
	let { tema = null, sinAnim = false }: Props = $props();

	/*
		Adornos por mes. Los que no aparecen aquí (mayo, y cualquier mes que se
		agregue después sin decidir qué adorno lleva) se quedan sin adorno a
		propósito: ver la foto limpia es mejor que un emoji fuera de lugar.
	*/
	const ADORNOS: Record<number, string[]> = {
		1: ['👑', '🎁', '✨'], // Reyes Magos
		2: ['💘', '🌹', '💕'], // San Valentín
		3: ['🌷', '🌱', '🦋'], // primavera
		4: ['🎈', '🧸', '🎨'], // Día del Niño
		6: ['☀️', '🌴', '🍹'], // verano
		7: ['🏖️', '🌊', '🍉'], // playa
		8: ['🌵', '🔥', '💦'], // el mes más caluroso
		9: ['🇲🇽', '🎊', '🎉'], // Independencia
		10: ['🎃', '💀', '🌽'], // Halloween y Día de Muertos
		11: ['🍂', '🎺', '🇲🇽'], // Revolución y otoño
		12: ['🎄', '🔔', '❄️'] // Navidad
	};

	const adornos = $derived(tema ? (ADORNOS[tema.mes] ?? []) : []);
</script>

{#if adornos.length}
	<div class="acentos" class:sinAnim aria-hidden="true" style="--tinte:{tema?.tinte ?? '#ffffff'}">
		{#each adornos as a, i (i)}
			<span class="adorno" style="--i:{i}">{a}</span>
		{/each}
	</div>
{/if}

<style>
	.acentos {
		position: absolute;
		left: 22px;
		bottom: 74px;
		z-index: 20;
		pointer-events: none;
		display: flex;
		gap: 10px;
		align-items: baseline;
		font-size: calc(30px * var(--k-escala, 1));
		opacity: 0.5;
		filter: drop-shadow(0 2px 6px rgb(0 0 0 / 0.45));
	}

	/*
		Deriva lenta y desfasada por adorno: un vaivén suave, sinTimeouts ni
		animaciones que sincronizar. Con `?sinanim=1` se queda quieto, que es lo
		que necesitan las capturas.
	*/
	.adorno {
		animation: vaiven calc(7s + var(--i) * 1.3s) ease-in-out infinite alternate;
	}
	.acentos.sinAnim .adorno { animation: none; }

	@keyframes vaiven {
		from { transform: translateY(0) rotate(-3deg); }
		to   { transform: translateY(-7px) rotate(3deg); }
	}

	@media (prefers-reduced-motion: reduce) {
		.adorno { animation: none; }
	}
</style>