<!-- SabiasQue.svelte - Pantalla de tutoriales "Sabias que...?"
     Muestra infografias de tutoriales que cambian aleatoriamente
     cada vez que se accede a la pantalla. -->
<script lang="ts">
	import { onMount } from 'svelte';

	// Lista de imagenes disponibles (agregar mas conforme se generen)
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
		// Agregar mas imagenes aqui conforme se generen:
		// '/sabias_que/sq_14_metricas_dashboard.png',
		// '/sabias_que/sq_15_nota_rapida.png',
		// etc...
	];

	let imagenActual = $state('');
	let cargando = $state(true);
	let error = $state(false);

	function seleccionarAleatoria() {
		const idx = Math.floor(Math.random() * IMAGENES.length);
		imagenActual = IMAGENES[idx];
	}

	onMount(() => {
		seleccionarAleatoria();
		cargando = false;
	});
</script>

<div class="screen sabias-que">
	{#if cargando}
		<div class="cargando">Cargando tutorial...</div>
	{:else if error}
		<div class="vacio">Sin tutoriales disponibles</div>
	{:else}
		<div class="imagen-container">
			<img src={imagenActual} alt="Sabias que..." class="tutorial-img" />
		</div>
	{/if}
</div>

<style>
	.screen { height: 100%; display: flex; flex-direction: column; }
	.cargando { display: flex; align-items: center; justify-content: center; height: 100%; color: var(--color-text-muted); font-size: 1.5rem; }
	.vacio { display: flex; align-items: center; justify-content: center; height: 100%; color: var(--color-text-muted); font-size: 1.2rem; }

	.imagen-container {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 1rem;
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
</style>