<!--
	Widget de cumpleaños y aniversario — visible en TODAS las pantallas.

	Antes el cumple de alguien sólo se veía en dos momentos: en su pantalla de
	celebraciones (que toca una vez cada vuelta de 12 pantallas) y en el aviso a
	pantalla completa del día. Entre una cosa y otra pasaban horas sin que nadie
	supiera que ese día alguien cumple años, y ése es justo el dato que nadie
	se acuerda de mirar.

	Ahora es un widget en la esquina: siempre que haya alguien, en todas las
	pantallas, sin tomar la pantalla ni parar la rotación.

	Diseño — por qué está ARRIBA a la izquierda y es chico:
	  · abajo está el ticker de alertas y el pie; a la derecha el reloj grande
	    del header baja hasta media pantalla en algunas pantallas. La esquina
	    superior izquierda es el único hueco que no se usa en las 12 pantallas.
	  · NO lleva borde grueso ni parpadeo de alerta: no es una alarma, es un
	    recordatorio. Por eso el brillo late despacio y el confeti NO se repite
	    aquí (ya lo lanza el aviso de pantalla completa).
	  · Si hay varias personas, va pasando una cada 15 s en vez de apilar
	    tarjetas: cinco nombres juntos taparían media pantalla.
-->
<script lang="ts">
	import { avatarSrc } from '$lib/kiosk/api';
	import type { Cumpleanero, Aniversariero, Snapshot } from '$lib/kiosk/types';

	interface Props { datos: Snapshot }
	let { datos }: Props = $props();

	const ROTAR_MS = 15_000;

	interface Aviso {
		clave: string;
		icono: string;
		titulo: string;
		nombre: string;
		detalle: string;
		avatar: string | null;
		clase: 'cumple' | 'aniversario';
	}

	/**
	 * Los de hoy, cumpleaños primero. Se arman aquí y no en el template para que
	 * la rotación sea sobre una lista ya ordenada y no sobre dos.
	 */
	const lista = $derived.by<Aviso[]>(() => {
		const out: Aviso[] = [];
		for (const c of (datos.cumpleanos?.hoy ?? []) as Cumpleanero[]) {
			out.push({
				clave: `cumple:${c.Nombre}`,
				icono: '🎂',
				titulo: '¡Feliz cumpleaños!',
				nombre: c.Nombre,
				detalle: c.edad ? `${c.edad} años` : 'Hoy es su día',
				avatar: c.foto ?? c.avatar ?? null,
				clase: 'cumple'
			});
		}
		for (const a of (datos.aniversarios?.hoy ?? []) as Aniversariero[]) {
			out.push({
				clave: `aniversario:${a.Nombre}`,
				icono: '💍',
				titulo: '¡Feliz aniversario!',
				nombre: a.Nombre,
				detalle: a.anos ? `${a.anos} años en ECCSA` : 'Hoy cumple años en ECCSA',
				avatar: a.foto ?? a.avatar ?? null,
				clase: 'aniversario'
			});
		}
		return out;
	});

	let indice = $state(0);
	let visible = $state(false);

	// Pasa de una persona a otra mientras haya más de una. El `{#key}` del
	// markup hace que cada una entre con su animación.
	$effect(() => {
		const n = lista.length;
		if (n <= 1) {
			indice = 0;
			return;
		}
		indice = 0;
		const t = setInterval(() => {
			indice = (indice + 1) % n;
		}, ROTAR_MS);
		return () => clearInterval(t);
	});

	const actual = $derived(lista[indice] ?? null);

	// Entra y sale con un fundido corto, no de golpe.
	$effect(() => {
		if (!actual) {
			visible = false;
			return;
		}
		visible = false;
		const t = setTimeout(() => (visible = true), 60);
		return () => clearTimeout(t);
	});
</script>

{#if actual}
	<div class="widget {actual.clase}" class:visible aria-hidden="true">
		{#key actual.clave}
			<div class="caja">
				<div class="glow" aria-hidden="true"></div>
				<div class="avatar">
					{#if actual.avatar}
						<img src={avatarSrc(actual.avatar)} alt="" />
					{:else}
						<span class="ic">{actual.icono}</span>
					{/if}
				</div>
				<div class="txt">
					<div class="titulo">
						<span class="ic-mini">{actual.icono}</span>{actual.titulo}
					</div>
					<div class="nombre">{actual.nombre}</div>
				</div>
				<div class="detalle">{actual.detalle}</div>
			</div>
		{/key}
	</div>
{/if}

<style>
	/*
		Fijo dentro del escenario: escala con --k-escala como todo lo demás y
		queda en la misma esquina en cualquier TV. z-index 40: por encima del
		contenido de las pantallas, por debajo del aviso a pantalla completa
		(55) y del ticker de alertas (30, abajo y sin choque).
	*/
	.widget {
		position: absolute;
		top: 66px;
		left: 16px;
		z-index: 40;
		pointer-events: none;
		opacity: 0;
		transform: translateY(-10px) scale(0.97);
		transition: opacity 0.45s ease, transform 0.45s cubic-bezier(0.16, 1, 0.3, 1);
	}
	.widget.visible { opacity: 1; transform: none; }

	.caja {
		position: relative;
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 9px 16px 9px 10px;
		border-radius: 999px;
		overflow: hidden;
		background: rgba(2, 6, 23, 0.72);
		backdrop-filter: blur(6px);
		animation: entra 0.55s cubic-bezier(0.16, 1, 0.3, 1) both;
	}
	@keyframes entra {
		from { opacity: 0; transform: translateX(-18px) scale(0.94); }
		to   { opacity: 1; transform: none; }
	}

	/* Cumple: naranja de la marca. Aniversario: violeta, para que se distingan
	   de un vistazo si las dos cosas caen el mismo día. */
	.cumple .caja { border: 1px solid rgba(255, 174, 0, 0.55); }
	.aniversario .caja { border: 1px solid rgba(167, 139, 250, 0.55); }

	/* El brillo late suave: llama la atención sin parpadear como alarma. */
	.glow {
		position: absolute;
		inset: -60% -20%;
		pointer-events: none;
		animation: latido 4.5s ease-in-out infinite;
	}
	.cumple .glow {
		background: radial-gradient(circle at 20% 50%, rgba(255, 174, 0, 0.22) 0%, rgba(255, 174, 0, 0) 60%);
	}
	.aniversario .glow {
		background: radial-gradient(circle at 20% 50%, rgba(167, 139, 250, 0.22) 0%, rgba(167, 139, 250, 0) 60%);
	}
	@keyframes latido {
		0%, 100% { opacity: 0.35; }
		50%      { opacity: 0.9; }
	}

	.avatar {
		position: relative;
		width: 52px;
		height: 52px;
		flex-shrink: 0;
		border-radius: 50%;
		overflow: hidden;
		background: rgba(255, 255, 255, 0.08);
		display: grid;
		place-items: center;
	}
	.avatar img { width: 100%; height: 100%; object-fit: cover; }
	.ic { font-size: 26px; }

	.txt { position: relative; line-height: 1.15; }
	.titulo {
		display: flex;
		align-items: center;
		gap: 5px;
		font-size: 12.5px;
		font-weight: 800;
		letter-spacing: 0.12em;
		text-transform: uppercase;
	}
	.cumple .titulo { color: #fbbf24; }
	.aniversario .titulo { color: #c4b5fd; }
	.ic-mini { font-size: 13px; }

	.nombre {
		font-size: 24px;
		font-weight: 800;
		color: #fff;
		white-space: nowrap;
		max-width: 320px;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.detalle {
		position: relative;
		font-size: 15px;
		font-weight: 700;
		color: #94a3b8;
		padding-left: 12px;
		border-left: 1px solid rgba(255, 255, 255, 0.15);
		white-space: nowrap;
	}
	.cumple .detalle { color: #fcd34d; }
	.aniversario .detalle { color: #ddd6fe; }
</style>
