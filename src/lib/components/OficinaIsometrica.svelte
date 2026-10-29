<!-- OficinaIsometrica.svelte - Vista isométrica de la oficina ECCSA con efectos climáticos -->
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
	const esLlovizna = $derived(codigo_clima >= 51 && codigo_clima <= 55);

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
	<svg viewBox="0 0 600 420" xmlns="http://www.w3.org/2000/svg" class="iso-svg">
		<defs>
			<!-- Gradiente del cielo -->
			<linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
				<stop offset="0%" stop-color="#1a237e" />
				<stop offset="100%" stop-color="#42a5f5" />
			</linearGradient>
			<linearGradient id="skyGradNight" x1="0" y1="0" x2="0" y2="1">
				<stop offset="0%" stop-color="#0d1b2a" />
				<stop offset="100%" stop-color="#1b2838" />
			</linearGradient>
			<linearGradient id="buildingFront" x1="0" y1="0" x2="0" y2="1">
				<stop offset="0%" stop-color="#c62828" />
				<stop offset="100%" stop-color="#b71c1c" />
			</linearGradient>
			<linearGradient id="buildingSide" x1="0" y1="0" x2="1" y2="0">
				<stop offset="0%" stop-color="#8d2a2a" />
				<stop offset="100%" stop-color="#6d1f1f" />
			</linearGradient>
			<linearGradient id="buildingRoof" x1="0" y1="0" x2="1" y2="1">
				<stop offset="0%" stop-color="#4e342e" />
				<stop offset="100%" stop-color="#3e2723" />
			</linearGradient>
			<linearGradient id="groundGrad" x1="0" y1="0" x2="0" y2="1">
				<stop offset="0%" stop-color="#4caf50" />
				<stop offset="100%" stop-color="#2e7d32" />
			</linearGradient>
			<filter id="shadow">
				<feDropShadow dx="2" dy="4" stdDeviation="3" flood-opacity="0.3" />
			</filter>
			<filter id="glow">
				<feGaussianBlur stdDeviation="3" result="coloredBlur" />
				<feMerge>
					<feMergeNode in="coloredBlur" />
					<feMergeNode in="SourceGraphic" />
				</feMerge>
			</filter>
		</defs>

		<!-- Cielo -->
		<rect x="0" y="0" width="600" height="420" class="sky" />

		<!-- Sol / Luna -->
		<g class="sun-moon">
			{#if es_dia && esDespejado}
				<circle cx="500" cy="80" r="35" fill="#ffeb3b" filter="url(#glow)" class="sun" />
			{:else if !es_dia && esDespejado}
				<circle cx="500" cy="80" r="25" fill="#f5f5f5" filter="url(#glow)" class="moon" />
				<!-- Estrellas -->
				{#each Array(12) as _, i}
					<circle cx={100 + (i * 47) % 480} cy={20 + (i * 31) % 60} r="1.5" fill="white" class="star" style="animation-delay: {i * 0.3}s" />
				{/each}
			{/if}
		</g>

		<!-- Nubes -->
		<g class="clouds">
			{#if esNublado || esLluvioso || esTormenta}
				<g class="cloud cloud1">
					<ellipse cx="150" cy="70" rx="60" ry="25" fill="rgba(255,255,255,0.7)" />
					<ellipse cx="200" cy="60" rx="50" ry="30" fill="rgba(255,255,255,0.8)" />
					<ellipse cx="120" cy="65" rx="45" ry="22" fill="rgba(255,255,255,0.6)" />
				</g>
				<g class="cloud cloud2">
					<ellipse cx="450" cy="90" rx="55" ry="22" fill="rgba(255,255,255,0.6)" />
					<ellipse cx="490" cy="80" rx="45" ry="28" fill="rgba(255,255,255,0.7)" />
				</g>
			{/if}
			{#if esTormenta}
				<g class="cloud cloud3">
					<ellipse cx="300" cy="50" rx="70" ry="30" fill="rgba(80,80,100,0.8)" />
					<ellipse cx="350" cy="45" rx="60" ry="35" fill="rgba(60,60,80,0.9)" />
				</g>
			{/if}
		</g>

		<!-- Suelo -->
		<polygon points="100,320 300,220 500,320 300,420" fill="url(#groundGrad)" class="ground" />

		<!-- Casa de ladrillos isométrica (casa grande) -->
		<g class="building" filter="url(#shadow)">
			<!-- Cara lateral (izquierda) - ladrillo -->
			<polygon points="180,280 180,140 290,80 290,220" fill="#a0522d" class="side-face" />
			<!-- Textura de ladrillo lateral -->
			<g class="brick-pattern-side">
				{#each Array(8) as _, row}
					{#each Array(3) as _, col}
						<rect x={185 + col * 32} y={145 + row * 18} width="28" height="12" fill="#8b4513" opacity="0.3" rx="1" />
					{/each}
				{/each}
			</g>
			<!-- Cara frontal - ladrillo -->
			<polygon points="290,220 290,80 400,140 400,280" fill="#b85c38" class="front-face" />
			<!-- Textura de ladrillo frontal -->
			<g class="brick-pattern-front">
				{#each Array(8) as _, row}
					{#each Array(3) as _, col}
						<rect x={295 + col * 32} y={85 + row * 18} width="28" height="12" fill="#8b4513" opacity="0.25" rx="1" />
					{/each}
				{/each}
			</g>
			<!-- Techo (a dos aguas) -->
			<polygon points="180,140 290,80 400,140 290,100" fill="#5d4037" class="roof" />
			<!-- Segundo plano del techo -->
			<polygon points="290,80 400,140 380,120 290,65" fill="#4e342e" class="roof-side" />
		</g>

		<!-- Barandal verde (balcón superior) -->
		<g class="railing">
			<!-- Barandal frontal -->
			<rect x="290" y="120" width="110" height="4" fill="#2e7d32" />
			<!-- Barandal lateral -->
			<polygon points="180,140 290,80 290,84 180,144" fill="#388e3c" />
			<!-- Postes del barandal (frontal) -->
			{#each [0, 1, 2, 3, 4] as i}
				<rect x={292 + i * 22} y="105" width="3" height="18" fill="#2e7d32" />
			{/each}
			<!-- Postes del barandal (lateral) -->
			{#each [0, 1, 2, 3] as i}
				<line x1={195 + i * 25} y1={135 - i * 15} x2={195 + i * 25} y2={120 - i * 15} stroke="#2e7d32" stroke-width="2" />
			{/each}
			<!-- Pasamanos superior frontal -->
			<line x1="290" y1="105" x2="400" y2="105" stroke="#43a047" stroke-width="3" />
			<!-- Pasamanos superior lateral -->
			<line x1="180" y1="125" x2="290" y2="65" stroke="#43a047" stroke-width="3" />
		</g>

		<!-- Balcón / terraza superior -->
		<polygon points="290,120 290,105 400,105 400,120" fill="#6d4c41" class="balcony" />

		<!-- Ventanas (cara frontal) - estilo residencial -->
		<g class="windows-front">
			<!-- Planta baja -->
			<rect x="300" y="200" width="35" height="40" fill={es_dia ? "rgba(255,235,59,0.7)" : "rgba(255,200,50,0.95)"} rx="2" stroke="#5d4037" stroke-width="2" />
			<rect x="355" y="200" width="35" height="40" fill={es_dia ? "rgba(255,235,59,0.7)" : "rgba(255,200,50,0.95)"} rx="2" stroke="#5d4037" stroke-width="2" />
			<!-- Segundo piso -->
			<rect x="300" y="145" width="30" height="35" fill={es_dia ? "rgba(255,235,59,0.6)" : "rgba(255,200,50,0.9)"} rx="2" stroke="#5d4037" stroke-width="2" />
			<rect x="340" y="145" width="30" height="35" fill={es_dia ? "rgba(255,235,59,0.6)" : "rgba(255,200,50,0.9)"} rx="2" stroke="#5d4037" stroke-width="2" />
			<rect x="375" y="145" width="20" height="35" fill={es_dia ? "rgba(255,235,59,0.6)" : "rgba(255,200,50,0.9)"} rx="2" stroke="#5d4037" stroke-width="2" />
		</g>

		<!-- Ventanas (cara lateral) -->
		<g class="windows-side">
			<rect x="200" y="180" width="25" height="30" fill={es_dia ? "rgba(179,188,255,0.5)" : "rgba(200,210,255,0.8)"} rx="2" stroke="#5d4037" stroke-width="1.5" />
			<rect x="235" y="180" width="25" height="30" fill={es_dia ? "rgba(179,188,255,0.5)" : "rgba(200,210,255,0.8)"} rx="2" stroke="#5d4037" stroke-width="1.5" />
			<rect x="200" y="140" width="20" height="25" fill={es_dia ? "rgba(179,188,255,0.4)" : "rgba(200,210,255,0.7)"} rx="2" stroke="#5d4037" stroke-width="1.5" />
		</g>

		<!-- Puerta de entrada (madera) -->
		<polygon
			points="330,240 330,280 360,280 360,240"
			fill="#5d4037"
			class="door"
			stroke="#3e2723"
			stroke-width="1"
		/>
		<!-- Marco de puerta -->
		<rect x="328" y="238" width="34" height="44" fill="none" stroke="#3e2723" stroke-width="2" rx="1" />
		<!-- Manija -->
		<circle cx="355" cy="260" r="2.5" fill="#ffd700" />

		<!-- Letrero ECCSA -->
		<g class="sign" transform="translate(345, 95)">
			<rect x="-35" y="-12" width="70" height="18" rx="3" fill="#ff6b00" />
			<text x="0" y="2" text-anchor="middle" fill="white" font-size="10" font-weight="bold" font-family="sans-serif">ECCSA</text>
		</g>

		<!-- Árboles -->
		<g class="trees">
			<!-- Árbol 1 (izquierda) -->
			<g transform="translate(130, 290)">
				<rect x="-3" y="0" width="6" height="25" fill="#5d4037" />
				<ellipse cx="0" cy="-10" rx="20" ry="18" fill="#4caf50" class="tree-top" />
				<ellipse cx="0" cy="-15" rx="15" ry="14" fill="#66bb6a" class="tree-top" />
			</g>
			<!-- Árbol 2 (derecha) -->
			<g transform="translate(470, 290)">
				<rect x="-3" y="0" width="6" height="25" fill="#5d4037" />
				<ellipse cx="0" cy="-10" rx="20" ry="18" fill="#4caf50" class="tree-top" />
				<ellipse cx="0" cy="-15" rx="15" ry="14" fill="#66bb6a" class="tree-top" />
			</g>
		</g>

		<!-- Estacionamiento -->
		<g class="parking">
			<rect x="320" y="300" width="30" height="18" rx="2" fill="#424242" stroke="#616161" stroke-width="1" />
			<rect x="360" y="305" width="30" height="18" rx="2" fill="#424242" stroke="#616161" stroke-width="1" />
		</g>

		<!-- Efectos climáticos -->
		<!-- Lluvia -->
		{#if esLluvioso || esTormenta}
			<g class="rain">
				{#each Array(40) as _, i}
					<line
						x1={50 + (i * 13) % 550}
						y1={-20 + (i * 7) % 100}
						x2={45 + (i * 13) % 550}
						y2={0 + (i * 7) % 100}
						stroke="rgba(173,216,230,0.6)"
						stroke-width="1.5"
						class="raindrop"
						style="animation-delay: {(i * 0.05) % 1}s; animation-duration: {0.6 + (i % 3) * 0.1}s"
					/>
				{/each}
			</g>
		{/if}

		<!-- Nieve -->
		{#if esNieve}
			<g class="snow">
				{#each Array(30) as _, i}
					<circle
						cx={30 + (i * 19) % 570}
						cy={-10 + (i * 11) % 50}
						r={2 + (i % 3)}
						fill="white"
						opacity="0.8"
						class="snowflake"
						style="animation-delay: {(i * 0.1) % 2}s; animation-duration: {2 + (i % 3) * 0.5}s"
					/>
				{/each}
			</g>
		{/if}

		<!-- Relámpagos (tormenta) -->
		{#if esTormenta}
			<g class="lightning">
				<polygon points="280,30 290,80 270,80 295,140 275,90 295,90" fill="#ffeb3b" opacity="0" class="lightning-bolt" />
			</g>
		{/if}

		<!-- Niebla -->
		{#if esNiebla}
			<g class="fog">
				<rect x="0" y="250" width="600" height="170" fill="rgba(200,200,220,0.4)" class="fog-layer" />
				<rect x="0" y="280" width="600" height="140" fill="rgba(180,180,200,0.3)" class="fog-layer2" />
			</g>
		{/if}

		<!-- Rayos de sol (soleado día) -->
		{#if esDespejado && es_dia}
			<g class="sunrays">
				{#each Array(8) as _, i}
					<line
						x1="500" y1="80"
						x2={500 + Math.cos(i * 45 * Math.PI / 180) * 80}
						y2={80 + Math.sin(i * 45 * Math.PI / 180) * 80}
						stroke="rgba(255,235,59,0.3)"
						stroke-width="3"
						class="sunray"
						style="animation-delay: {i * 0.1}s"
					/>
				{/each}
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
	}

	.iso-svg {
		width: 100%;
		max-width: 600px;
		height: auto;
		filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.3));
	}

	/* Cielo */
	.sky {
		fill: url(#skyGrad);
		transition: fill 2s ease;
	}
	.soleado-noche .sky { fill: url(#skyGradNight); }
	.nublado .sky { fill: #78909c; }
	.lluvia .sky { fill: #546e7a; }
	.tormenta .sky { fill: #37474f; }
	.niebla .sky { fill: #90a4ae; }
	.nieve .sky { fill: #b0bec5; }

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

	/* Ventanas */
	.window {
		transition: fill 1s ease;
	}

	/* Edificio */
	.building {
		transition: filter 1s ease;
	}

	/* Lluvia */
	.raindrop {
		animation: rain-fall linear infinite;
	}
	@keyframes rain-fall {
		0% { transform: translateY(-100px); opacity: 0; }
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
		10% { opacity: 0.8; }
		90% { opacity: 0.8; }
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
		0%, 100% { transform: translateX(0); opacity: 0.4; }
		50% { transform: translateX(30px); opacity: 0.6; }
	}

	/* Rayos de sol */
	.sunray {
		animation: ray-pulse 2s ease-in-out infinite;
		transform-origin: 500px 80px;
	}
	@keyframes ray-pulse {
		0%, 100% { opacity: 0.2; }
		50% { opacity: 0.5; }
	}

	/* Árboles */
	.tree-top {
		transition: fill 1s ease;
	}
	.lluvia .tree-top { fill: #388e3c; }
	.nieve .tree-top { fill: #e8f5e9; }

	/* Weather badge */
	.weather-badge {
		position: absolute;
		bottom: 10px;
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
	}

	.weather-icon { font-size: 24px; }
	.weather-temp { font-size: 18px; font-weight: 800; color: #ff6b00; }
</style>
