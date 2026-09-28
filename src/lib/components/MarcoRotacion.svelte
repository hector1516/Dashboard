<!--
	Marco de rotación: la línea del contorno que se va comiendo con el tiempo
	que le queda a la pantalla.

	Por qué está en SVG y no con 4 bordes CSS: para que la línea se retraiga
	REALMENTE sobre el contorno (dasharray) en vez de encogerse hacia adentro.
	Un borde que se adelgaza se lee como un cambio de grosor; una línea que
	desaparece por el recorrido del marco se lee como un reloj.

	Va dentro de `.escenario` (no del viewport) para que escale con el factor
	--k-escala igual que todo lo demás: si se pegara al viewport, en una TV con
	letterbox quedaría desalineado del contenido.

	Se oculta —a propósito— cuando:
	  · la pantalla está fija por URL (`?pantalla=…`): no hay cambio que avisar,
	  · hay una toma de pantalla de alerta: la alerta manda, no el reloj,
	  · está la marca de salida de las 18:30,
	  · `?sinanim=1`: las capturas salen limpias, sin cromo de verificación.
-->
<script lang="ts">
	interface Props {
		/** En recuadro fijo de 1920×1080; el marco se dibuja justo dentro. */
		lado?: number;
		/** Duración de una pantalla, en ms. */
		duracionMs: number;
		/** Segundos que faltan (para el número). */
		restante: number;
		/** Cambia en cada giro: reinicia la animación (va dentro de {#key}). */
		token: number | string;
	}

	let { lado = 1920, duracionMs, restante, token }: Props = $props();

	const MARGEN = 7;                    // px de aire entre el marco y el borde
	const ALTO = 1080;
	const w = $derived(lado - MARGEN * 2);
	const h = $derived(ALTO - MARGEN * 2);
	// Perímetro del rectángulo: lo que mide la línea completa.
	const perimetro = $derived(2 * (w + h));
	const seg = $derived(Math.max(0, Math.ceil(restante)));
</script>

<div class="marco" aria-hidden="true">
	<svg viewBox="0 0 {lado} {ALTO}" width={lado} height={ALTO}>
		<!-- Pista: la línea completa, apenas visible. Es la que "se consume". -->
		<rect
			class="pista"
			x={MARGEN} y={MARGEN} width={w} height={h}
			rx="10"
		/>
		<!--
			Consumo: `stroke-dasharray` con el perímetro completo y un hueco igual
			de largo, y se anima `stroke-dashoffset` de 0 al perímetro. Al avanzar
			el tiempo, el hueco se come la línea desde el punto donde arranca el
			trazado (arriba a la izquierda) y se retira en sentido contrario a las
			manecillas, como una serpentina que se desenrolla.
		-->
		{#key token}
			<rect
				class="linea"
				x={MARGEN} y={MARGEN} width={w} height={h}
				rx="10"
				style="--perimetro:{perimetro};--duracion:{duracionMs}ms;stroke-dasharray:{perimetro} {perimetro}"
			/>
		{/key}
	</svg>

	<!-- El número: en una TV a 3 metros la línea sola no dice cuántos segundos. -->
	<div class="cuenta">
		<span class="gir">{seg}</span>
		<span class="s">s</span>
		<span class="rot">para cambiar</span>
	</div>
</div>

<style>
	.marco {
		position: absolute;
		inset: 0;
		/* Por encima del contenido y por debajo de la capa de salida (que vive
		   fuera de .escenario, con z-index 900). */
		z-index: 60;
		pointer-events: none;
	}

	svg { display: block; }

	.pista {
		fill: none;
		stroke: rgba(255, 255, 255, 0.055);
		stroke-width: 3;
	}

	.linea {
		fill: none;
		stroke: var(--color-primary, #ff6b00);
		stroke-width: 4;
		stroke-linecap: round;
		/* El brillo se desvanece con la línea: cuando queda 10% no debe
		   seguir pareciendo una alarma. */
		animation-name: consumir;
		animation-duration: var(--duracion, 45s);
		animation-timing-function: linear;
		animation-fill-mode: forwards;
		filter: drop-shadow(0 0 6px rgba(255, 107, 0, 0.55));
	}

	@keyframes consumir {
		from { stroke-dashoffset: 0; }
		to   { stroke-dashoffset: calc(var(--perimetro) * -1); }
	}

	.cuenta {
		position: absolute;
		right: 26px;
		bottom: 40px;
		display: flex;
		align-items: baseline;
		gap: 5px;
		padding: 5px 13px 6px;
		border-radius: 999px;
		background: rgba(2, 6, 23, 0.72);
		border: 1px solid rgba(255, 255, 255, 0.07);
		backdrop-filter: blur(4px);
	}
	.gir {
		font-size: 24px;
		font-weight: 900;
		color: var(--color-primary, #ff6b00);
		font-variant-numeric: tabular-nums;
		line-height: 1;
	}
	.s { font-size: 14px; font-weight: 800; color: var(--color-primary, #ff6b00); }
	.rot {
		font-size: 12px;
		font-weight: 700;
		color: #64748b;
		letter-spacing: 0.04em;
		margin-left: 3px;
	}
</style>
