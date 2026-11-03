<!-- SabiasQue.svelte - Pantalla de tutoriales "Sabias que...?"
     Muestra infografias chibi 1920x1080 en rotacion automatica.
     Mismo contenido, sin agregar imagenes nuevas. -->
<script lang="ts">
	import { onMount } from 'svelte';

	// Las 25 imagenes disponibles en disco (sq_01..sq_25)
	const IMAGENES = [
		'/sabias_que/sq_01_busqueda_rapida.png',
		'/sabias_que/sq_02_crear_cotizacion.png',
		'/sabias_que/sq_03_comparar_cotizaciones.png',
		'/sabias_que/sq_04_reporte_servicio.png',
		'/sabias_que/sq_05_kilometros.png',
		'/sabias_que/sq_06_ticket_oxxogas.png',
		'/sabias_que/sq_07_fotos_reportes.png',
		'/sabias_que/sq_08_editar_reporte.png',
		'/sabias_que/sq_09_ficha_nfc.png',
		'/sabias_que/sq_10_historial_cotizaciones.png',
		'/sabias_que/sq_11_repositorio.png',
		'/sabias_que/sq_12_administrar_usuarios.png',
		'/sabias_que/sq_13_telegram.png',
		'/sabias_que/sq_14_metricas_dashboard.png',
		'/sabias_que/sq_15_nota_rapida.png',
		'/sabias_que/sq_16_enviar_whatsapp.png',
		'/sabias_que/sq_17_historial_cambios.png',
		'/sabias_que/sq_18_filtrar_fecha.png',
		'/sabias_que/sq_19_voz_texto.png',
		'/sabias_que/sq_20_mapa_ubicacion.png',
		'/sabias_que/sq_21_exportar_excel.png',
		'/sabias_que/sq_22_atajos_field.png',
		'/sabias_que/sq_23_estadisticas_uso.png',
		'/sabias_que/sq_24_qr_cotizacion.png',
		'/sabias_que/sq_25_historial_cambios_cotizacion.png',
	];

	let indice = $state(0);
	let imagenActual = $state(IMAGENES[0]);
	let cargando = $state(true);
	let timer: ReturnType<typeof setInterval> | null = null;

	function siguiente() {
		indice = (indice + 1) % IMAGENES.length;
		imagenActual = IMAGENES[indice];
	}

	function irA(i: number) {
		indice = i;
		imagenActual = IMAGENES[i];
	}

	onMount(() => {
		cargando = false;
		timer = setInterval(siguiente, 12000); // 12 s por tutorial
		return () => {
			if (timer) clearInterval(timer);
		};
	});
</script>

<div class="screen sabias-que">
	{#if cargando}
		<div class="cargando">Cargando tutorial...</div>
	{:else}
		<div class="imagen-container">
			{#key imagenActual}
				<img src={imagenActual} alt="Sabias que... tutorial {indice + 1} de {IMAGENES.length}" class="tutorial-img" />
			{/key}
		</div>

		<!-- Indicador de progreso: 25 puntos, el activo en azul ECCSA -->
		<div class="puntos" role="tablist" aria-label="Tutoriales">
			{#each IMAGENES as _, i}
				<button
					class="punto"
					class:activo={i === indice}
					onclick={() => irA(i)}
					aria-label="Tutorial {i + 1}"
					title="Tutorial {i + 1}"
				></button>
			{/each}
		</div>
	{/if}
</div>

<style>
	.screen { height: 100%; display: flex; flex-direction: column; }
	.cargando { display: flex; align-items: center; justify-content: center; height: 100%; color: var(--color-text-muted); font-size: 1.5rem; }

	.imagen-container {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0.5rem;
		overflow: hidden;
	}

	.tutorial-img {
		max-width: 100%;
		max-height: 100%;
		object-fit: contain;
		border-radius: 12px;
		box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
		animation: fadeIn 0.5s ease;
	}

	@keyframes fadeIn {
		from { opacity: 0; transform: scale(0.98); }
		to { opacity: 1; transform: scale(1); }
	}

	.puntos {
		display: flex;
		gap: 6px;
		justify-content: center;
		align-items: center;
		padding: 0.4rem 0 0.2rem;
		flex-shrink: 0;
	}

	.punto {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		border: none;
		background: rgba(255, 255, 255, 0.25);
		cursor: pointer;
		padding: 0;
		transition: background 0.3s ease, transform 0.3s ease;
		flex-shrink: 0;
	}

	.punto:hover { background: rgba(255, 255, 255, 0.5); }

	.punto.activo {
		background: #1E40AF;
		transform: scale(1.4);
	}
</style>