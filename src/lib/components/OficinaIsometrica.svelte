<!-- OficinaIsometrica.svelte - Vista de la oficina real con efectos climáticos -->
<script lang="ts">
	interface Props {
		codigo_clima: number;
		es_dia: boolean;
		temperatura: number | null;
		descripcion: string;
		icono: string;
	}

	let { codigo_clima, es_dia, temperatura, descripcion, icono }: Props = $props();

	// Determinar tipo de clima para las animaciones
	const esLluvioso = $derived(codigo_clima >= 51 && codigo_clima <= 99);
	const esTormenta = $derived(codigo_clima >= 95 && codigo_clima <= 99);
	const esNublado = $derived(codigo_clima === 3 || (codigo_clima >= 45 && codigo_clima <= 48));
	const esDespejado = $derived(codigo_clima <= 2);
	const esNiebla = $derived(codigo_clima >= 45 && codigo_clima <= 48);
	const esNieve = $derived(codigo_clima >= 71 && codigo_clima <= 77);

	// Clase de clima para CSS
	const climaClass = $derived(
		esTormenta ? 'tormenta' :
		esLluvioso ? 'lluvia' :
		esNieve ? 'nieve' :
		esNiebla ? 'niebla' :
		esNublado ? 'nublado' :
		esDespejado ? (es_dia ? 'soleado-dia' : 'soleado-noche') :
		'nublado'
	);
</script>

<div class="isometric-scene {climaClass}">
	<!-- Imagen real de la oficina (isométrica con transparencia) -->
	<div class="office-image-container">
		<img src="/images/oficina-eccsa.png" alt="Oficina ECCSA" class="office-image" />
	</div>

	<!-- Efectos climáticos superpuestos -->
	<svg viewBox="0 0 600 420" xmlns="http://www.w3.org/2000/svg" class="weather-overlay">
		<defs>
			<filter id="glow">
				<feGaussianBlur stdDeviation="3" result="coloredBlur" />
				<feMerge>
					<feMergeNode in="coloredBlur" />
					<feMergeNode in="SourceGraphic" />
				</feMerge>
			</filter>
		</defs>

		<!-- Sol (soleado día) -->
		{#if esDespejado && es_dia}
			<g class="sun-group">
				<circle cx="500" cy="60" r="30" fill="#ffeb3b" filter="url(#glow)" class="sun" />
				{#each Array(8) as _, i}
					<line
						x1="500" y1="60"
						x2={500 + Math.cos(i * 45 * Math.PI / 180) * 70}
						y2={60 + Math.sin(i * 45 * Math.PI / 180) * 70}
						stroke="rgba(255,235,59,0.4)"
						stroke-width="3"
						class="sunray"
						style="animation-delay: {i * 0.1}s"
					/>
				{/each}
			</g>
		{/if}

		<!-- Luna + estrellas (despejado noche) -->
		{#if esDespejado && !es_dia}
			<g class="moon-group">
				<circle cx="500" cy="60" r="22" fill="#f5f5f5" filter="url(#glow)" class="moon" />
				{#each Array(15) as _, i}
					<circle cx={50 + (i * 37) % 550} cy={20 + (i * 23) % 80} r="1.5" fill="white" class="star" style="animation-delay: {i * 0.2}s" />
				{/each}
			</g>
		{/if}

		<!-- Nubes (nublado/lluvia) -->
		{#if esNublado || esLluvioso || esTormenta}
			<g class="clouds">
				<g class="cloud cloud1">
					<ellipse cx="120" cy="60" rx="55" ry="22" fill="rgba(255,255,255,0.7)" />
					<ellipse cx="170" cy="50" rx="45" ry="28" fill="rgba(255,255,255,0.8)" />
					<ellipse cx="90" cy="55" rx="40" ry="20" fill="rgba(255,255,255,0.6)" />
				</g>
				<g class="cloud cloud2">
					<ellipse cx="420" cy="70" rx="50" ry="20" fill="rgba(255,255,255,0.6)" />
					<ellipse cx="460" cy="60" rx="40" ry="25" fill="rgba(255,255,255,0.7)" />
				</g>
				{#if esTormenta}
					<g class="cloud cloud3">
						<ellipse cx="280" cy="45" rx="65" ry="28" fill="rgba(80,80,100,0.8)" />
						<ellipse cx="330" cy="40" rx="55" ry="32" fill="rgba(60,60,80,0.9)" />
					</g>
				{/if}
			</g>
		{/if}

		<!-- Lluvia -->
		{#if esLluvioso || esTormenta}
			<g class="rain">
				{#each Array(50) as _, i}
					<line
						x1={30 + (i * 11) % 570}
						y1={-30 + (i * 13) % 120}
						x2={25 + (i * 11) % 570}
						y2={-10 + (i * 13) % 120}
						stroke="rgba(173,216,230,0.7)"
						stroke-width="1.5"
						class="raindrop"
						style="animation-delay: {(i * 0.03) % 0.8}s; animation-duration: {0.5 + (i % 4) * 0.1}s"
					/>
				{/each}
			</g>
		{/if}

		<!-- Nieve -->
		{#if esNieve}
			<g class="snow">
				{#each Array(40) as _, i}
					<circle
						cx={20 + (i * 15) % 580}
						cy={-10 + (i * 9) % 60}
						r={2 + (i % 3)}
						fill="white"
						opacity="0.9"
						class="snowflake"
						style="animation-delay: {(i * 0.08) % 1.5}s; animation-duration: {2 + (i % 3) * 0.5}s"
					/>
				{/each}
			</g>
		{/if}

		<!-- Relámpagos (tormenta) -->
		{#if esTormenta}
			<g class="lightning">
				<polygon points="280,20 295,70 275,70 300,130 280,80 300,80" fill="#ffeb3b" opacity="0" class="lightning-bolt" />
			</g>
		{/if}

		<!-- Niebla -->
		{#if esNiebla}
			<g class="fog">
				<rect x="0" y="260" width="600" height="160" fill="rgba(200,200,220,0.35)" class="fog-layer" />
				<rect x="0" y="290" width="600" height="130" fill="rgba(180,180,200,0.25)" class="fog-layer2" />
			</g>
		{/if}
	</svg>

	<!-- Indicador de clima -->
	<div class="weather-badge">
		<span class="weather-icon">{icono}</span>
		<span class="weather-desc">{descripcion}</span>
		{#if temperatura !== null}
			<span class="weather-temp">{temperatura}°C</span>
		{/if}
	</div>
</div>

<style>
	.isometric-scene {
		position: relative;
		width: 100%;
		height: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		overflow: hidden;
		border-radius: 16px;
	}

	.office-image-container {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1;
	}

	.office-image {
		max-width: 85%;
		max-height: 85%;
		object-fit: contain;
		filter: drop-shadow(0 8px 24px rgba(0, 0, 0, 0.4));
		transition: filter 1s ease, opacity 1s ease;
	}

	/* Efectos de clima sobre la imagen */
	.soleado-dia .office-image {
		filter: drop-shadow(0 8px 24px rgba(255, 200, 50, 0.3)) brightness(1.05);
	}
	.soleado-noche .office-image {
		filter: drop-shadow(0 8px 24px rgba(100, 100, 200, 0.3)) brightness(0.85);
	}
	.nublado .office-image {
		filter: drop-shadow(0 8px 24px rgba(100, 100, 100, 0.3)) brightness(0.9);
	}
	.lluvia .office-image {
		filter: drop-shadow(0 8px 24px rgba(50, 80, 120, 0.4)) brightness(0.85) saturate(0.9);
	}
	.tormenta .office-image {
		filter: drop-shadow(0 8px 24px rgba(30, 30, 50, 0.5)) brightness(0.75) saturate(0.8);
	}
	.niebla .office-image {
		filter: drop-shadow(0 8px 24px rgba(150, 150, 170, 0.4)) brightness(0.9) blur(0.5px);
	}
	.nieve .office-image {
		filter: drop-shadow(0 8px 24px rgba(180, 200, 220, 0.4)) brightness(1.0) saturate(0.85);
	}

	.weather-overlay {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		z-index: 2;
		pointer-events: none;
	}

	/* Fondo del contenedor según clima */
	.isometric-scene {
		background: linear-gradient(180deg, #87CEEB 0%, #E0F7FA 100%);
		transition: background 2s ease;
	}
	.soleado-noche { background: linear-gradient(180deg, #0d1b2a 0%, #1b2838 100%); }
	.nublado { background: linear-gradient(180deg, #78909c 0%, #90a4ae 100%); }
	.lluvia { background: linear-gradient(180deg, #546e7a 0%, #607d8b 100%); }
	.tormenta { background: linear-gradient(180deg, #37474f 0%, #455a64 100%); }
	.niebla { background: linear-gradient(180deg, #90a4ae 0%, #b0bec5 100%); }
	.nieve { background: linear-gradient(180deg, #b0bec5 0%, #cfd8dc 100%); }

	/* Sol */
	.sun {
		animation: pulse-sun 3s ease-in-out infinite;
	}
	@keyframes pulse-sun {
		0%, 100% { transform: scale(1); opacity: 1; }
		50% { transform: scale(1.05); opacity: 0.9; }
	}

	/* Luna */
	.moon {
		animation: pulse-moon 4s ease-in-out infinite;
	}
	@keyframes pulse-moon {
		0%, 100% { opacity: 0.9; }
		50% { opacity: 1; }
	}

	/* Estrellas */
	.star {
		animation: twinkle 2s ease-in-out infinite;
	}
	@keyframes twinkle {
		0%, 100% { opacity: 0.3; }
		50% { opacity: 1; }
	}

	/* Nubes */
	.cloud {
		animation: drift 20s linear infinite;
	}
	.cloud2 { animation-duration: 25s; animation-direction: reverse; }
	@keyframes drift {
		0% { transform: translateX(-20px); }
		50% { transform: translateX(20px); }
		100% { transform: translateX(-20px); }
	}

	/* Lluvia */
	.raindrop {
		animation: rain-fall linear infinite;
	}
	@keyframes rain-fall {
		0% { transform: translateY(-50px); opacity: 0; }
		10% { opacity: 1; }
		90% { opacity: 1; }
		100% { transform: translateY(420px); opacity: 0; }
	}

	/* Nieve */
	.snowflake {
		animation: snow-fall linear infinite;
	}
	@keyframes snow-fall {
		0% { transform: translateY(-20px) translateX(0); opacity: 0; }
		10% { opacity: 0.9; }
		90% { opacity: 0.9; }
		100% { transform: translateY(420px) translateX(20px); opacity: 0; }
	}

	/* Relámpago */
	.lightning-bolt {
		animation: flash 4s steps(1) infinite;
	}
	@keyframes flash {
		0%, 94%, 100% { opacity: 0; }
		95% { opacity: 1; }
		96% { opacity: 0; }
		97% { opacity: 0.8; }
		98% { opacity: 0; }
	}

	/* Niebla */
	.fog-layer {
		animation: fog-move 10s ease-in-out infinite;
	}
	.fog-layer2 {
		animation: fog-move 15s ease-in-out infinite reverse;
	}
	@keyframes fog-move {
		0%, 100% { transform: translateX(0); opacity: 0.35; }
		50% { transform: translateX(30px); opacity: 0.5; }
	}

	/* Rayos de sol */
	.sunray {
		animation: ray-pulse 2s ease-in-out infinite;
		transform-origin: 500px 60px;
	}
	@keyframes ray-pulse {
		0%, 100% { opacity: 0.2; }
		50% { opacity: 0.5; }
	}

	/* Weather badge */
	.weather-badge {
		position: absolute;
		bottom: 12px;
		left: 50%;
		transform: translateX(-50%);
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 8px 20px;
		background: rgba(0, 0, 0, 0.5);
		backdrop-filter: blur(8px);
		border-radius: 20px;
		color: white;
		font-size: 14px;
		font-weight: 600;
		z-index: 3;
	}

	.weather-icon { font-size: 24px; }
	.weather-temp { font-size: 18px; font-weight: 800; color: #ff6b00; }
</style>
