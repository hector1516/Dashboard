<script lang="ts">
	interface Props { valor: number; formato: (n: number) => string; duracion?: number }
	let { valor, formato, duracion = 600 }: Props = $props();
	// Arranca mostrando el valor final y el efecto lo rebobina a 0 para contar:
	// así la primera pintura no deja la cifra en blanco. La captura inicial es
	// intencional (el aviso de Svelte es por eso).
	// svelte-ignore state_referenced_locally
	let mostrado = $state(valor);
	$effect(() => {
		if (typeof window === 'undefined') return;
		// `?sinanim=1` es el interruptor de capturas: el número tiene que salir
		// en su valor final y no a medio contar.
		const sinAnim = new URLSearchParams(window.location.search).get('sinanim') === '1';
		if (sinAnim || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
			mostrado = valor;
			return;
		}
		const t0 = performance.now();
		let raf = 0;
		const paso = (t: number) => {
			// El timestamp del frame puede quedar antes de `t0` por un pelo:
			// sin el tope en 0, la primera pintura salía negativa («$-27,952»).
			const k = Math.max(0, Math.min(1, (t - t0) / duracion));
			mostrado = valor * (1 - Math.pow(1 - k, 3));
			if (k < 1) raf = requestAnimationFrame(paso);
		};
		raf = requestAnimationFrame(paso);
		return () => cancelAnimationFrame(raf);
	});
</script>

<!-- `data-numero`: el barrido de `contarNumeros` salta este span porque ya
     cuenta solo; animarlo otra vez lo haría bailar dos veces. -->
<span class="num" data-numero style="font-variant-numeric:tabular-nums">{formato(Math.round(mostrado))}</span>
