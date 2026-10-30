<!-- OficinaIsometrica.svelte - Vista de la oficina real con efectos climáticos avanzados -->
<script lang="ts">
	interface Props {
		codigo_clima: number;
		es_dia: boolean;
		temperatura: number | null;
		descripcion: string;
		icono: string;
	}

	let { codigo_clima, es_dia, temperatura, descripcion, icono }: Props = $props();

	// Determinar tipo de clima
	const esLluvioso = $derived(codigo_clima >= 51 && codigo_clima <= 99);
	const esTormenta = $derived(codigo_clima >= 95 && codigo_clima <= 99);
	const esNublado = $derived(codigo_clima === 3 || (codigo_clima >= 45 && codigo_clima <= 48));
	const esDespejado = $derived(codigo_clima <= 2);
	const esNiebla = $derived(codigo_clima >= 45 && codigo_clima <= 48);
	const esNieve = $derived(codigo_clima >= 71 && codigo_clima <= 77);
	const esLlovizna = $derived(codigo_clima >= 51 && codigo_clima <= 55);
	const esCaluroso = $derived((temperatura ?? 0) > 30);
	const esFrio = $derived((temperatura ?? 0) < 18);
	const esVentoso = $derived((codigo_clima >= 30 && codigo_clima <= 48) || esTormenta);

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
	<!-- Imagen real de la oficina -->
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
			<filter id="blur">
				<feGaussianBlur stdDeviation="2" />
			</filter>
			<linearGradient id="rainbowGrad" x1="0" y1="0" x2="1" y2="0">
				<stop offset="0%" stop-color="rgba(255,0,0,0.3)" />
				<stop offset="16%" stop-color="rgba(255,165,0,0.3)" />
				<stop offset="33%" stop-color="rgba(255,255,0,0.3)" />
				<stop offset="50%" stop-color="rgba(0,255,0,0.3)" />
				<stop offset="66%" stop-color="rgba(0,0,255,0.3)" />
				<stop offset="83%" stop-color="rgba(75,0,130,0.3)" />
				<stop offset="100%" stop-color="rgba(238,130,238,0.3)" />
			</linearGradient>
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
				<!-- Reflejo del sol en ventanas -->
				<ellipse cx="350" cy="180" rx="15" ry="8" fill="rgba(255,235,59,0.15)" class="sun-reflection">
					<animate attributeName="opacity" values="0.1;0.25;0.1" dur="4s" repeatCount="indefinite" />
				</ellipse>
			</g>
		{/if}

		<!-- Luna + estrellas (despejado noche) -->
		{#if esDespejado && !es_dia}
			<g class="moon-group">
				<circle cx="500" cy="60" r="22" fill="#f5f5f5" filter="url(#glow)" class="moon" />
				{#each Array(20) as _, i}
					<circle cx={30 + (i * 29) % 570} cy={15 + (i * 17) % 70} r={1 + (i % 2)} fill="white" class="star" style="animation-delay: {i * 0.15}s" />
				{/each}
				<!-- Luces de ventanas (parpadeando) -->
				{#each Array(6) as _, i}
					<rect x={310 + (i % 3) * 35} y={100 + Math.floor(i / 3) * 50} width="20" height="15" fill="rgba(255,220,100,0.6)" rx="1" class="window-light">
						<animate attributeName="opacity" values="0.4;0.8;0.4" dur="{2 + i * 0.5}s" repeatCount="indefinite" begin="{i * 0.3}s" />
					</rect>
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
				{#each Array(60) as _, i}
					<line
						x1={20 + (i * 9.7) % 580}
						y1={-40 + (i * 11.3) % 130}
						x2={15 + (i * 9.7) % 580}
						y2={-20 + (i * 11.3) % 130}
						stroke="rgba(173,216,230,0.7)"
						stroke-width="1.5"
						class="raindrop"
						style="animation-delay: {(i * 0.02) % 0.6}s; animation-duration: {0.4 + (i % 5) * 0.08}s"
					/>
				{/each}
			</g>
			<!-- Charcos en el suelo -->
			<g class="puddles">
				{#each Array(4) as _, i}
					<ellipse cx={150 + i * 120} cy={350 + (i % 2) * 20} rx={20 + i * 5} ry={6 + i * 2} fill="rgba(100,150,200,0.3)" class="puddle">
						<animate attributeName="rx" values="{20 + i * 5};{25 + i * 5};{20 + i * 5}" dur="{3 + i}s" repeatCount="indefinite" />
						<animate attributeName="opacity" values="0.2;0.4;0.2" dur="{3 + i}s" repeatCount="indefinite" />
					</ellipse>
				{/each}
			</g>
			<!-- Goteo desde el techo -->
			<g class="dripping">
				{#each Array(5) as _, i}
					<circle cx={280 + i * 30} cy={140 + (i % 2) * 10} r="2" fill="rgba(173,216,230,0.8)" class="drip">
						<animate attributeName="cy" values="{140 + (i % 2) * 10};{200 + (i % 2) * 10}" dur="{1.5 + i * 0.3}s" repeatCount="indefinite" />
						<animate attributeName="opacity" values="0;1;0" dur="{1.5 + i * 0.3}s" repeatCount="indefinite" />
					</circle>
				{/each}
			</g>
		{/if}

		<!-- Nieve -->
		{#if esNieve}
			<g class="snow">
				{#each Array(50) as _, i}
					<circle
						cx={15 + (i * 11.7) % 585}
						cy={-10 + (i * 7.3) % 50}
						r={2 + (i % 3)}
						fill="white"
						opacity="0.9"
						class="snowflake"
						style="animation-delay: {(i * 0.06) % 2}s; animation-duration: {2.5 + (i % 4) * 0.4}s"
					/>
				{/each}
			</g>
			<!-- Nieve acumulada en el techo -->
			<g class="snow-accumulation">
				<ellipse cx="300" cy="130" rx="60" ry="8" fill="rgba(255,255,255,0.6)" class="snow-roof">
					<animate attributeName="ry" values="6;10;6" dur="8s" repeatCount="indefinite" />
				</ellipse>
			</g>
		{/if}

		<!-- Relámpagos (tormenta) -->
		{#if esTormenta}
			<g class="lightning">
				<polygon points="280,20 295,70 275,70 300,130 280,80 300,80" fill="#ffeb3b" opacity="0" class="lightning-bolt" />
				<!-- Flash que ilumina toda la escena -->
				<rect x="0" y="0" width="600" height="420" fill="white" opacity="0" class="lightning-flash">
					<animate attributeName="opacity" values="0;0;0.15;0;0;0;0.1;0" dur="4s" repeatCount="indefinite" />
				</rect>
			</g>
		{/if}

		<!-- Niebla -->
		{#if esNiebla}
			<g class="fog">
				<rect x="0" y="200" width="600" height="220" fill="rgba(200,200,220,0.3)" class="fog-layer" />
				<rect x="0" y="260" width="600" height="160" fill="rgba(180,180,200,0.25)" class="fog-layer2" />
				<rect x="0" y="300" width="600" height="120" fill="rgba(160,160,180,0.2)" class="fog-layer3" />
			</g>
		{/if}

		<!-- Viento (partículas de hojas/polvo) -->
		{#if esVentoso}
			<g class="wind">
				{#each Array(12) as _, i}
					<circle cx={-20 + (i * 50) % 620} cy={100 + (i * 37) % 200} r={1.5 + (i % 2)} fill="rgba(200,180,120,0.6)" class="wind-particle">
						<animate attributeName="cx" values="{(i * 50) % 620};{620 + (i * 50) % 620}" dur="{3 + i * 0.5}s" repeatCount="indefinite" begin="{i * 0.3}s" />
						<animate attributeName="cy" values="{100 + (i * 37) % 200};{80 + (i * 37) % 200}" dur="{3 + i * 0.5}s" repeatCount="indefinite" begin="{i * 0.3}s" />
						<animate attributeName="opacity" values="0;0.6;0" dur="{3 + i * 0.5}s" repeatCount="indefinite" begin="{i * 0.3}s" />
					</circle>
				{/each}
				<!-- Líneas de viento -->
				{#each Array(5) as _, i}
					<line x1={100 + i * 100} y1={80 + i * 30} x2={160 + i * 100} y2={75 + i * 30} stroke="rgba(255,255,255,0.3)" stroke-width="1" class="wind-line">
						<animate attributeName="x1" values="{100 + i * 100};{160 + i * 100}" dur="{2 + i * 0.3}s" repeatCount="indefinite" begin="{i * 0.5}s" />
						<animate attributeName="x2" values="{160 + i * 100};{220 + i * 100}" dur="{2 + i * 0.3}s" repeatCount="indefinite" begin="{i * 0.5}s" />
						<animate attributeName="opacity" values="0;0.5;0" dur="{2 + i * 0.3}s" repeatCount="indefinite" begin="{i * 0.5}s" />
					</line>
				{/each}
			</g>
		{/if}

		<!-- Calor (ondas de calor) -->
		{#if esCaluroso && es_dia}
			<g class="heat">
				{#each Array(4) as _, i}
					<line x1={200 + i * 80} y1={300} x2={200 + i * 80} y2={280} stroke="rgba(255,100,0,0.15)" stroke-width="2" class="heat-wave">
						<animate attributeName="y1" values="300;295;300" dur="{2 + i * 0.3}s" repeatCount="indefinite" begin="{i * 0.5}s" />
						<animate attributeName="y2" values="280;275;280" dur="{2 + i * 0.3}s" repeatCount="indefinite" begin="{i * 0.5}s" />
						<animate attributeName="opacity" values="0.1;0.25;0.1" dur="{2 + i * 0.3}s" repeatCount="indefinite" begin="{i * 0.5}s" />
					</line>
				{/each}
			</g>
		{/if}

		<!-- Frío (vapor/aliento) -->
		{#if esFrio}
			<g class="cold">
				{#each Array(3) as _, i}
					<circle cx={320 + i * 25} cy={180} r="3" fill="rgba(255,255,255,0.4)" class="breath">
						<animate attributeName="cy" values="180;150" dur="{2 + i * 0.5}s" repeatCount="indefinite" begin="{i * 0.8}s" />
						<animate attributeName="r" values="2;6" dur="{2 + i * 0.5}s" repeatCount="indefinite" begin="{i * 0.8}s" />
						<animate attributeName="opacity" values="0.5;0" dur="{2 + i * 0.5}s" repeatCount="indefinite" begin="{i * 0.8}s" />
					</circle>
				{/each}
			</g>
		{/if}

		<!-- Arcoíris (después de lluvia, si está despejando) -->
		{#if esLluvioso && es_dia && codigo_clima <= 65}
			<g class="rainbow">
				<path d="M 100,300 Q 300,100 500,300" fill="none" stroke="url(#rainbowGrad)" stroke-width="8" opacity="0.4" class="rainbow-arc">
					<animate attributeName="opacity" values="0;0.4;0" dur="6s" repeatCount="indefinite" />
				</path>
			</g>
		{/if}

		<!-- Pájaros volando -->
		{#if esDespejado && es_dia}
			<g class="birds">
				{#each Array(3) as _, i}
					<g class="bird" style="animation-delay: {i * 2}s">
						<path d="M 0,0 Q 3,-3 6,0 Q 3,2 0,0" fill="none" stroke="rgba(50,50,50,0.6)" stroke-width="1.5" class="bird-shape">
							<animate attributeName="d" values="M 0,0 Q 3,-3 6,0 Q 3,2 0,0; M 0,0 Q 3,3 6,0 Q 3,-2 0,0; M 0,0 Q 3,-3 6,0 Q 3,2 0,0" dur="0.6s" repeatCount="indefinite" />
						</path>
						<animateTransform attributeName="transform" type="translate" values="{100 + i * 150},80;{700 + i * 150},60" dur="{8 + i * 2}s" repeatCount="indefinite" begin="{i * 3}s" />
					</g>
				{/each}
			</g>
		{/if}

		<!-- Humo de chimenea (siempre, más visible en frío) -->
		<g class="smoke">
			{#each Array(3) as _, i}
				<circle cx="320" cy="90" r="4" fill="rgba(200,200,200,0.3)" class="smoke-puff">
					<animate attributeName="cy" values="90;50" dur="{3 + i * 0.5}s" repeatCount="indefinite" begin="{i * 1}s" />
					<animate attributeName="cx" values="320;{315 + i * 5}" dur="{3 + i * 0.5}s" repeatCount="indefinite" begin="{i * 1}s" />
					<animate attributeName="r" values="3;8" dur="{3 + i * 0.5}s" repeatCount="indefinite" begin="{i * 1}s" />
					<animate attributeName="opacity" values="0.4;0" dur="{3 + i * 0.5}s" repeatCount="indefinite" begin="{i * 1}s" />
				</circle>
			{/each}
		</g>

		<!-- Sombra de la oficina (se mueve con el sol) -->
		{#if esDespejado && es_dia}
			<ellipse cx="350" cy="360" rx="80" ry="20" fill="rgba(0,0,0,0.15)" class="building-shadow">
				<animate attributeName="cx" values="340;360;340" dur="10s" repeatCount="indefinite" />
				<animate attributeName="rx" values="75;85;75" dur="10s" repeatCount="indefinite" />
			</ellipse>
		{/if}
	</svg>


		<!-- Animales -->
		<!-- Mariposas (soleado día) -->
		{#if esDespejado && es_dia}
			<g class="butterflies">
				{#each Array(4) as _, i}
					<g class="butterfly" style="animation-delay: {i * 1.5}s">
						<path d="M 0,0 Q 2,-2 4,0 Q 2,1 0,0" fill="rgba(255,100,150,0.7)" class="wing-left">
							<animate attributeName="d" values="M 0,0 Q 2,-2 4,0 Q 2,1 0,0; M 0,0 Q 2,2 4,0 Q 2,-1 0,0; M 0,0 Q 2,-2 4,0 Q 2,1 0,0" dur="0.4s" repeatCount="indefinite" />
						</path>
						<path d="M 0,0 Q -2,-2 -4,0 Q -2,1 0,0" fill="rgba(255,100,150,0.7)" class="wing-right">
							<animate attributeName="d" values="M 0,0 Q -2,-2 -4,0 Q -2,1 0,0; M 0,0 Q -2,2 -4,0 Q -2,-1 0,0; M 0,0 Q -2,-2 -4,0 Q -2,1 0,0" dur="0.4s" repeatCount="indefinite" />
						</path>
						<animateTransform attributeName="transform" type="translate" values="{150 + i * 100},120;{250 + i * 100},100;{350 + i * 100},130;{450 + i * 100},110" dur="{6 + i * 2}s" repeatCount="indefinite" begin="{i * 2}s" />
					</g>
				{/each}
			</g>
		{/if}

		<!-- Abejas (soleado día) -->
		{#if esDespejado && es_dia}
			<g class="bees">
				{#each Array(3) as _, i}
					<g class="bee" style="animation-delay: {i * 1}s">
						<ellipse cx="0" cy="0" rx="2" ry="1.5" fill="#ffeb3b" />
						<ellipse cx="0" cy="0" rx="1" ry="0.8" fill="#333" />
						<circle cx="-1" cy="-1" r="1" fill="rgba(255,255,255,0.6)" class="bee-wing">
							<animate attributeName="r" values="1;0.5;1" dur="0.15s" repeatCount="indefinite" />
						</circle>
						<circle cx="1" cy="-1" r="1" fill="rgba(255,255,255,0.6)" class="bee-wing">
							<animate attributeName="r" values="0.5;1;0.5" dur="0.15s" repeatCount="indefinite" />
						</circle>
						<animateTransform attributeName="transform" type="translate" values="{200 + i * 120},150;{280 + i * 120},130;{360 + i * 120},160;{440 + i * 120},140" dur="{5 + i * 1.5}s" repeatCount="indefinite" begin="{i * 2.5}s" />
					</g>
				{/each}
			</g>
		{/if}

		<!-- Lagartijas en la pared (soleado día) -->
		{#if esDespejado && es_dia}
			<g class="lizards">
				{#each Array(2) as _, i}
					<g class="lizard">
						<ellipse cx="0" cy="0" rx="4" ry="1.5" fill="#66bb6a" />
						<circle cx="3" cy="0" r="1.5" fill="#4caf50" />
						<line x1="-4" y1="0" x2="-8" y2="0" stroke="#66bb6a" stroke-width="1" />
						<animateTransform attributeName="transform" type="translate" values="{330 + i * 40},160;{335 + i * 40},155;{330 + i * 40},160" dur="{4 + i}s" repeatCount="indefinite" begin="{i * 1.5}s" />
					</g>
				{/each}
			</g>
		{/if}

		<!-- Perro en el jardín (siempre de día) -->
		{#if es_dia}
			<g class="dog">
				<ellipse cx="0" cy="0" rx="6" ry="3" fill="#8d6e63" />
				<circle cx="5" cy="-1" r="2.5" fill="#8d6e63" />
				<circle cx="4" cy="-2" r="0.8" fill="#333" />
				<line x1="-6" y1="0" x2="-9" y2="-3" stroke="#8d6e63" stroke-width="1.5" stroke-linecap="round" />
				<animateTransform attributeName="transform" type="translate" values="120,320;130,315;120,320" dur="6s" repeatCount="indefinite" />
				<animate attributeName="opacity" values="1;0.9;1" dur="6s" repeatCount="indefinite" />
			</g>
		{/if}

		<!-- Gato en el techo (siempre) -->
		<g class="cat">
			<ellipse cx="0" cy="0" rx="4" ry="2" fill="#78909c" />
			<circle cx="3" cy="-1" r="1.8" fill="#78909c" />
			<polygon points="2,-2 1,-4 3,-3" fill="#78909c" />
			<polygon points="4,-2 5,-4 3,-3" fill="#78909c" />
			<circle cx="2.5" cy="-1.5" r="0.5" fill="#ffeb3b" />
			<circle cx="3.5" cy="-1.5" r="0.5" fill="#ffeb3b" />
			<line x1="-4" y1="0" x2="-7" y2="-2" stroke="#78909c" stroke-width="1" />
			<animateTransform attributeName="transform" type="translate" values="380,125;385,120;380,125" dur="5s" repeatCount="indefinite" />
		</g>

		<!-- Ardilla en árbol (soleado) -->
		{#if esDespejado && es_dia}
			<g class="squirrel">
				<ellipse cx="0" cy="0" rx="3" ry="2" fill="#8d6e63" />
				<circle cx="2.5" cy="-1" r="1.5" fill="#8d6e63" />
				<path d="M -3,0 Q -5,-4 -3,-6" stroke="#8d6e63" stroke-width="1.5" fill="none" />
				<animateTransform attributeName="transform" type="translate" values="135,270;140,265;135,270" dur="4s" repeatCount="indefinite" />
			</g>
		{/if}

		<!-- Conejo en el jardín (soleado día) -->
		{#if esDespejado && es_dia}
			<g class="rabbit">
				<ellipse cx="0" cy="0" rx="3" ry="2" fill="#bdbdbd" />
				<circle cx="2.5" cy="-1" r="1.5" fill="#bdbdbd" />
				<ellipse cx="2" cy="-3" rx="0.8" ry="2" fill="#bdbdbd" />
				<ellipse cx="3" cy="-3" rx="0.8" ry="2" fill="#bdbdbd" />
				<animateTransform attributeName="transform" type="translate" values="460,330;470,325;460,330" dur="7s" repeatCount="indefinite" />
			</g>
		{/if}

		<!-- Búho en la noche -->
		{#if !es_dia}
			<g class="owl">
				<ellipse cx="0" cy="0" rx="4" ry="3.5" fill="#5d4037" />
				<circle cx="0" cy="-1" r="2" fill="#ffeb3b" opacity="0.8" />
				<circle cx="0" cy="-1" r="1" fill="#333" />
				<polygon points="-2,-3 0,-5 2,-3" fill="#5d4037" />
				<animate attributeName="opacity" values="0.6;1;0.6" dur="3s" repeatCount="indefinite" />
				<animateTransform attributeName="transform" type="translate" values="480,80;485,75;480,80" dur="5s" repeatCount="indefinite" />
			</g>
		{/if}

		<!-- Murciélagos en la noche -->
		{#if !es_dia}
			<g class="bats">
				{#each Array(3) as _, i}
					<g class="bat">
						<path d="M 0,0 Q 3,-2 6,0 Q 3,1 0,0" fill="rgba(80,80,80,0.7)" class="bat-wing">
							<animate attributeName="d" values="M 0,0 Q 3,-2 6,0 Q 3,1 0,0; M 0,0 Q 3,2 6,0 Q 3,-1 0,0; M 0,0 Q 3,-2 6,0 Q 3,1 0,0" dur="0.3s" repeatCount="indefinite" />
						</path>
						<animateTransform attributeName="transform" type="translate" values="{100 + i * 180},50;{200 + i * 180},40;{300 + i * 180},55" dur="{6 + i * 2}s" repeatCount="indefinite" begin="{i * 2}s" />
					</g>
				{/each}
			</g>
		{/if}

		<!-- Luciérnagas en la noche -->
		{#if !es_dia}
			<g class="fireflies">
				{#each Array(8) as _, i}
					<circle cx={100 + (i * 67) % 450} cy={200 + (i * 43) % 150} r="1.5" fill="#ffeb3b" class="firefly">
						<animate attributeName="opacity" values="0;1;0" dur="{1.5 + (i % 3) * 0.5}s" repeatCount="indefinite" begin="{i * 0.4}s" />
						<animate attributeName="cx" values="{100 + (i * 67) % 450};{120 + (i * 67) % 450}" dur="{3 + (i % 2)}s" repeatCount="indefinite" begin="{i * 0.4}s" />
						<animate attributeName="cy" values="{200 + (i * 43) % 150};{180 + (i * 43) % 150}" dur="{3 + (i % 2)}s" repeatCount="indefinite" begin="{i * 0.4}s" />
					</circle>
				{/each}
			</g>
		{/if}

		<!-- Ranas en lluvia -->
		{#if esLluvioso}
			<g class="frogs">
				{#each Array(2) as _, i}
					<g class="frog">
						<ellipse cx="0" cy="0" rx="3" ry="2" fill="#4caf50" />
						<circle cx="2" cy="-1" r="1" fill="#ffeb3b" />
						<circle cx="-2" cy="-1" r="1" fill="#ffeb3b" />
						<animateTransform attributeName="transform" type="translate" values="{200 + i * 200},340;{210 + i * 200},335;{200 + i * 200},340" dur="{3 + i}s" repeatCount="indefinite" />
					</g>
				{/each}
			</g>
		{/if}

		<!-- Caracoles en lluvia -->
		{#if esLluvioso}
			<g class="snails">
				{#each Array(2) as _, i}
					<g class="snail">
						<ellipse cx="0" cy="0" rx="2" ry="1.5" fill="#8d6e63" />
						<circle cx="0" cy="-1" r="2" fill="#a1887f" />
						<animateTransform attributeName="transform" type="translate" values="{150 + i * 250},350;{155 + i * 250},348;{150 + i * 250},350" dur="{5 + i}s" repeatCount="indefinite" />
					</g>
				{/each}
			</g>
		{/if}

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
		min-height: 400px;
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
		max-width: 95%;
		max-height: 95%;
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
	.sun { animation: pulse-sun 3s ease-in-out infinite; }
	@keyframes pulse-sun { 0%, 100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.05); opacity: 0.9; } }

	/* Luna */
	.moon { animation: pulse-moon 4s ease-in-out infinite; }
	@keyframes pulse-moon { 0%, 100% { opacity: 0.9; } 50% { opacity: 1; } }

	/* Estrellas */
	.star { animation: twinkle 2s ease-in-out infinite; }
	@keyframes twinkle { 0%, 100% { opacity: 0.3; } 50% { opacity: 1; } }

	/* Nubes */
	.cloud { animation: drift 20s linear infinite; }
	.cloud2 { animation-duration: 25s; animation-direction: reverse; }
	@keyframes drift { 0% { transform: translateX(-20px); } 50% { transform: translateX(20px); } 100% { transform: translateX(-20px); } }

	/* Lluvia */
	.raindrop { animation: rain-fall linear infinite; }
	@keyframes rain-fall { 0% { transform: translateY(-50px); opacity: 0; } 10% { opacity: 1; } 90% { opacity: 1; } 100% { transform: translateY(420px); opacity: 0; } }

	/* Charcos */
	.puddle { animation: puddle-pulse 3s ease-in-out infinite; }
	@keyframes puddle-pulse { 0%, 100% { opacity: 0.2; } 50% { opacity: 0.4; } }

	/* Goteo */
	.drip { animation: drip-fall linear infinite; }
	@keyframes drip-fall { 0% { transform: translateY(0); opacity: 0; } 10% { opacity: 1; } 90% { opacity: 1; } 100% { transform: translateY(60px); opacity: 0; } }

	/* Nieve */
	.snowflake { animation: snow-fall linear infinite; }
	@keyframes snow-fall { 0% { transform: translateY(-20px) translateX(0); opacity: 0; } 10% { opacity: 0.9; } 90% { opacity: 0.9; } 100% { transform: translateY(420px) translateX(20px); opacity: 0; } }

	/* Relámpago */
	.lightning-bolt { animation: flash 4s steps(1) infinite; }
	.lightning-flash { animation: flash 4s steps(1) infinite; }
	@keyframes flash { 0%, 94%, 100% { opacity: 0; } 95% { opacity: 1; } 96% { opacity: 0; } 97% { opacity: 0.8; } 98% { opacity: 0; } }

	/* Niebla */
	.fog-layer { animation: fog-move 10s ease-in-out infinite; }
	.fog-layer2 { animation: fog-move 15s ease-in-out infinite reverse; }
	.fog-layer3 { animation: fog-move 20s ease-in-out infinite; }
	@keyframes fog-move { 0%, 100% { transform: translateX(0); opacity: 0.3; } 50% { transform: translateX(30px); opacity: 0.5; } }

	/* Rayos de sol */
	.sunray { animation: ray-pulse 2s ease-in-out infinite; transform-origin: 500px 60px; }
	@keyframes ray-pulse { 0%, 100% { opacity: 0.2; } 50% { opacity: 0.5; } }

	/* Viento */
	.wind-particle { animation: wind-blow linear infinite; }
	@keyframes wind-blow { 0% { transform: translateX(0); opacity: 0; } 10% { opacity: 0.6; } 90% { opacity: 0.6; } 100% { transform: translateX(620px); opacity: 0; } }
	.wind-line { animation: wind-line-blow linear infinite; }
	@keyframes wind-line-blow { 0% { transform: translateX(0); opacity: 0; } 10% { opacity: 0.5; } 90% { opacity: 0.5; } 100% { transform: translateX(120px); opacity: 0; } }

	/* Calor */
	.heat-wave { animation: heat-shimmer 2s ease-in-out infinite; }
	@keyframes heat-shimmer { 0%, 100% { transform: translateY(0); opacity: 0.1; } 50% { transform: translateY(-5px); opacity: 0.25; } }

	/* Frío (vapor) */
	.breath { animation: breath-rise 2s ease-out infinite; }
	@keyframes breath-rise { 0% { transform: translateY(0) scale(1); opacity: 0.5; } 100% { transform: translateY(-30px) scale(2); opacity: 0; } }

	/* Arcoíris */
	.rainbow-arc { animation: rainbow-fade 6s ease-in-out infinite; }
	@keyframes rainbow-fade { 0%, 100% { opacity: 0; } 50% { opacity: 0.4; } }

	/* Pájaros */
	.bird { animation: bird-fly 8s linear infinite; }
	.bird-shape { animation: bird-flap 0.6s ease-in-out infinite; }
	@keyframes bird-flap { 0%, 100% { d: path("M 0,0 Q 3,-3 6,0 Q 3,2 0,0"); } 50% { d: path("M 0,0 Q 3,3 6,0 Q 3,-2 0,0"); } }

	/* Humo */
	.smoke-puff { animation: smoke-rise 3s ease-out infinite; }
	@keyframes smoke-rise { 0% { transform: translateY(0) scale(1); opacity: 0.4; } 100% { transform: translateY(-40px) scale(2); opacity: 0; } }

	/* Sombra del edificio */
	.building-shadow { animation: shadow-move 10s ease-in-out infinite; }
	@keyframes shadow-move { 0%, 100% { transform: translateX(-10px); } 50% { transform: translateX(10px); } }

	/* Reflejo del sol */
	.sun-reflection { animation: reflection-pulse 4s ease-in-out infinite; }
	@keyframes reflection-pulse { 0%, 100% { opacity: 0.1; } 50% { opacity: 0.25; } }

	/* Luces de ventanas */
	.window-light { animation: window-flicker 3s ease-in-out infinite; }
	@keyframes window-flicker { 0%, 100% { opacity: 0.4; } 50% { opacity: 0.8; } }

	/* Nieve acumulada */
	.snow-roof { animation: snow-accumulate 8s ease-in-out infinite; }
	@keyframes snow-accumulate { 0%, 100% { ry: 6; } 50% { ry: 10; } }

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
