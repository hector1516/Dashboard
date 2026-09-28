<!--
	Marca de salida: los últimos 10 segundos antes de las 18:30 y el cartel de
	las 18:30, de lunes a viernes.

	Es la única capa del kiosco que se salta las reglas prudentes de las
	alertas, y a propósito:
	  · no es un aviso, es un reloj: la gente sabe que a las 18:30 se sale, y lo
	    que necesitan es ver la hora sin tener que voltear a buscarla,
	  · es lo más importante del día para quien quiere irse a su casa,
	  · por eso es roja, enorme y no deja pasar nada más: una banda abajo con
	    un "salen en 10 s" sería más elegante e invisible a 3 metros.

	Dos estados:
	  'cuenta' → cuenta regresiva de 10 a 1, con latido (el fondo late como un
	             pulso: es lo que llama la atención sin necesidad de texto).
	  'ya'     → 18:30 en números gigantes, llenando la pantalla.

	No decide la hora ni el momento: eso lo calcula el orquestador (+page.svelte)
	que ya tiene el reloj. Este componente sólo dibuja.
-->
<script lang="ts">
	interface Props {
		/** 'cuenta' = cuenta regresiva · 'ya' = llegó la hora · null = nada. */
		modo: 'cuenta' | 'ya' | null;
		/** Segundos que faltan (sólo en 'cuenta'). */
		segundos: number;
		/** Hora de salida en texto: "18:30". */
		hora: string;
		/** `?sinanim=1`: quita latidos y golpes, deja la composición quieta. */
		sinAnim?: boolean;
	}

	let { modo, segundos, hora, sinAnim = false }: Props = $props();
</script>

{#if modo}
	<!--
		aria-hidden: la pantalla no la lee nadie con lector de pantalla, y en
		la cuenta el texto cambia cada segundo, que sería un spam continuo.
	-->
	<div class="salida" class:m-ya={modo === 'ya'} class:sin-anim={sinAnim} aria-hidden="true">
		<!-- Latido: un pulso rojo que se reinicia cada segundo. Es lo que se
		     nota desde el otro lado de la oficina aunque nadie mire el número.
		     El {#key} está para que el pulso RESTARTE con cada segundo: sin él
		     la animación seguiría su curso y el latido no marcaría el conteo. -->
		{#key modo === 'cuenta' ? segundos : 'fijo'}
			<div class="latido"></div>
		{/key}

		<div class="bloque">
			{#if modo === 'cuenta'}
				<div class="etiqueta">LA SALIDA ES EN</div>
				{#key segundos}
					<div class="cifra cuenta">{segundos}</div>
				{/key}
				<div class="pie">SEGUNDOS</div>
			{:else}
				<div class="etiqueta">HORA DE SALIDA</div>
				<!-- El "18:30" pedido: números tabulares gigantes, del ancho de
				     la pantalla. El `key` fuerza el remount para que el golpe de
				     entrada se vea siempre. -->
				{#key hora}
					<div class="cifra ya">{hora}</div>
				{/key}
				<div class="pie">¡A CASA!</div>
			{/if}
		</div>
	</div>
{/if}

<style>
	/*
		Fuera del .escenario a propósito: es una capa que se come la pantalla
		entera, con su propio z-index por encima del header, las alertas y el
		confeti. El orquestador la monta como hermana de .kiosco.
	*/
	.salida {
		position: fixed;
		inset: 0;
		z-index: 900;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
		/* Rojo profundo con degradado radial: un plano rojo liso en una TV se
		   ve como una avería, no como una alarma. */
		background: radial-gradient(ellipse at 50% 45%, #7f1d1d 0%, #450a0a 45%, #1a0303 100%);
		color: #fff;
		font-family: 'Outfit', system-ui, sans-serif;
	}

	.latido {
		position: absolute;
		inset: -12%;
		background: radial-gradient(circle at 50% 50%, rgba(255, 40, 40, 0.55) 0%, rgba(220, 20, 20, 0) 62%);
		opacity: 0;
		animation: latir 1s ease-out infinite;
		pointer-events: none;
	}
	.salida.m-ya .latido { animation-duration: 2.4s; }
	.salida.sin-anim .latido { animation: none; opacity: 0.18; }

	@keyframes latir {
		0%   { transform: scale(0.82); opacity: 0.9; }
		70%  { transform: scale(1.18); opacity: 0; }
		100% { transform: scale(1.18); opacity: 0; }
	}

	/* Viñeta: oscurece las esquinas y hace que el número sea lo único que
	   brilla. En una TV de 55" el degradado solo se ve plano. */
	.salida::after {
		content: '';
		position: absolute;
		inset: 0;
		background: radial-gradient(ellipse at 50% 50%, rgba(0,0,0,0) 42%, rgba(0,0,0,0.55) 100%);
		pointer-events: none;
	}

	.bloque {
		position: relative;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 8px;
		text-align: center;
	}

	.etiqueta {
		font-size: 62px;
		font-weight: 700;
		letter-spacing: 0.34em;
		/* compensa el letter-spacing, que también empuja el último carácter */
		text-indent: 0.34em;
		color: #fecaca;
		text-transform: uppercase;
		text-shadow: 0 6px 30px rgba(0, 0, 0, 0.55);
	}

	/*
		El número. `tabular-nums` para que NO baile de lado entre el 1 y el 2
		(el conteo se vería tembloroso sin eso).
		El tamaño del "18:30" está calculado para el escenario de 1920 px: ocupa
		unos 1520 px de ancho, o sea la pantalla de lado a lado.
	*/
	.cifra {
		font-weight: 800;
		line-height: 0.86;
		font-variant-numeric: tabular-nums;
		animation: golpe 0.55s cubic-bezier(0.2, 1.4, 0.4, 1);
	}
	.salida.sin-anim .cifra { animation: none; }

	.cuenta {
		font-size: 620px;
		color: #fff5f5;
		text-shadow:
			0 0 40px rgba(255, 60, 60, 0.75),
			0 0 120px rgba(255, 0, 0, 0.55),
			0 18px 50px rgba(0, 0, 0, 0.6);
		filter: drop-shadow(0 0 60px rgba(255, 30, 30, 0.85));
	}

	.ya {
		/* 520 px: el "18:30" mide ~1520 px, o sea ocupa la pantalla de lado a
		   lado como pidió el usuario (con 400 px apenas llegaba a 1080). */
		font-size: 520px;
		letter-spacing: 0.02em;
		background: linear-gradient(180deg, #ffffff 0%, #ffe4e4 55%, #ffb4b4 100%);
		-webkit-background-clip: text;
		background-clip: text;
		/* El degradado sobre el texto necesita su propia sombra: con
		   `color: transparent` se come la del texto. */
		color: transparent;
		filter: drop-shadow(0 0 70px rgba(255, 40, 40, 0.9));
		animation: golpe-grande 1.1s cubic-bezier(0.2, 1.5, 0.35, 1);
	}

	@keyframes golpe {
		0%   { transform: scale(0.62); opacity: 0; }
		55%  { transform: scale(1.1); opacity: 1; }
		100% { transform: scale(1); opacity: 1; }
	}
	@keyframes golpe-grande {
		0%   { transform: scale(0.45); opacity: 0; letter-spacing: 0.3em; }
		60%  { transform: scale(1.04); opacity: 1; }
		100% { transform: scale(1); opacity: 1; }
	}

	.pie {
		font-size: 54px;
		font-weight: 700;
		letter-spacing: 0.5em;
		text-indent: 0.5em;
		color: #fca5a5;
		text-transform: uppercase;
	}
	.m-ya .pie { color: #fecaca; }
</style>
