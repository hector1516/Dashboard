<!--
	Cuenta de rotación: los segundos que le quedan a la pantalla actual.

	Se probó con una línea de color rodeando la pantalla que se iba comiendo
	(mejor que un borde que se adelgaza, porque una línea que desaparece sobre
	el marco sí se lee como reloj) y se quitó: en un pasillo con varias TVs,
	el marco naranja competía con la pantalla y distraía de los datos. Queda
	sólo el número, chico y discreto, abajo a la derecha donde el ojo ya está
	acostumbrado (el pie de la página tiene ahí el "datos al día").

	Es lo mínimo que resuelve la duda real frente a un muro de pantallas: "¿se
	cayó la TV o nomás está esperando el turno?". Ese número lo contesta sin
	gritar.
-->
<script lang="ts">
	interface Props {
		/** Segundos que le quedan a la pantalla actual. */
		restante: number;
	}
	let { restante }: Props = $props();
</script>

<div class="rot" aria-hidden="true">
	<span class="seg">{Math.max(0, Math.ceil(restante))}</span>
	<span class="s">s</span>
</div>

<style>
	.rot {
		position: absolute;
		right: 22px;
		bottom: 38px;
		z-index: 60;
		pointer-events: none;
		display: flex;
		align-items: baseline;
		gap: 1px;
		/* Sin caja, sin borde, sin color: sólo el número, en gris apagado y a
	   media opacidad, para que se lea sin robar atención. */
		font-weight: 700;
		opacity: 0.55;
	}
	.seg {
		font-size: 16px;
		color: #94a3b8;
		font-variant-numeric: tabular-nums;
		line-height: 1;
	}
	.s { font-size: 10px; color: #64748b; line-height: 1; }
</style>
