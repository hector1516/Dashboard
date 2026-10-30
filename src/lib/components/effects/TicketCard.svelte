<!--
	Ticket Card — silueta de ticket perforado con parallax sutil.

	Uso: <TicketCard folio="TKT-001" vehiculo="Nissan NP300" usuario="Juan" />
-->
<script lang="ts">
	interface Props {
		folio: string;
		vehiculo?: string;
		usuario?: string;
		cliente?: string;
		descripcion?: string;
		fecha?: string;
		reciente?: boolean;
		fecha_vale?: string | null;
		estatus_vale?: string | null;
		monto_vale?: number | null;
		imagen_url?: string | null;
	}
	let {
		folio,
		vehiculo = '',
		usuario = '',
		cliente = '',
		descripcion = '',
		fecha = '',
		reciente = false,
		fecha_vale = null,
		estatus_vale = null,
		monto_vale = null,
		imagen_url = null
	}: Props = $props();

	let mouseX = $state(0);
	let mouseY = $state(0);
	let hovering = $state(false);

	function handleMouseMove(e: MouseEvent) {
		const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
		mouseX = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
		mouseY = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
	}
</script>

<div
	class="ticket"
	class:reciente
	onmouseenter={() => (hovering = true)}
	onmouseleave={() => (hovering = false)}
	onmousemove={handleMouseMove}
	style="--mx: {mouseX}; --my: {mouseY}"
>
	<!-- Perforaciones laterales -->
	<div class="perf perf-left"></div>
	<div class="perf perf-right"></div>

	{#if imagen_url}
		<div class="ticket-img">
			<img src={imagen_url} alt="Ticket {folio}" loading="lazy" />
		</div>
	{/if}

	<div class="contenido">
		<div class="folio">{folio}</div>
		<div class="vehiculo">{vehiculo}</div>
		<div class="usuario">👤 {usuario}</div>
		{#if cliente}
			<div class="cliente">{cliente}</div>
		{/if}
		{#if descripcion}
			<div class="desc">{descripcion}</div>
		{/if}
		<div class="fecha">{fecha?.replace('T', ' ')}</div>
		{#if fecha_vale}
			<div class="vale-info">
				<span class="vale-label">🎫 Vale: {fecha_vale?.replace('T', ' ')}</span>
				{#if estatus_vale}
					<span class="vale-estatus" class:cerrado={estatus_vale === 'CERRADO'}>{estatus_vale}</span>
				{/if}
				{#if monto_vale}
					<span class="vale-monto">${monto_vale}</span>
				{/if}
			</div>
		{/if}
	</div>
</div>

<style>
	.ticket {
		position: relative;
		display: flex;
		flex-direction: column;
		justify-content: center;
		gap: 4px;
		padding: 16px 20px;
		border-radius: 12px;
		min-height: 130px;
		background: rgba(245, 158, 11, 0.06);
		border: 1px solid rgba(245, 158, 11, 0.14);
		overflow: hidden;
		transform: perspective(600px) rotateY(calc(var(--mx, 0) * 3deg)) rotateX(calc(var(--my, 0) * -3deg));
		transition: transform 0.15s ease-out, box-shadow 0.2s;
	}

	.ticket.reciente {
		border-color: rgba(255, 174, 0, 0.55);
		box-shadow: 0 0 18px rgba(255, 174, 0, 0.18);
	}

	/* Perforaciones laterales */
	.perf {
		position: absolute;
		top: 50%;
		width: 12px;
		height: 12px;
		border-radius: 50%;
		background: #0f172a;
		transform: translateY(-50%);
		z-index: 1;
	}
	.perf-left { left: -6px; }
	.perf-right { right: -6px; }

	/* Borde perforado */
	.ticket::before {
		content: '';
		position: absolute;
		inset: 4px;
		border: 1px dashed rgba(245, 158, 11, 0.2);
		border-radius: 8px;
		pointer-events: none;
	}

	.ticket-img {
		position: absolute;
		top: 8px;
		right: 8px;
		width: 60px;
		height: 60px;
		border-radius: 6px;
		overflow: hidden;
		z-index: 3;
		border: 1px solid rgba(245, 158, 11, 0.3);
	}
	.ticket-img img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.contenido {
		position: relative;
		z-index: 2;
	}

	.folio { font-weight: 800; color: #ffae00; font-size: 19px; }
	.vehiculo { font-weight: 700; color: #f1f5f9; font-size: 17px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.usuario { font-size: 14px; color: #cbd5e1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.cliente { font-size: 13.5px; color: #94a3b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.desc { font-size: 13px; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.fecha { font-size: 12px; color: #475569; margin-top: 4px; }
	.vale-info {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-top: 4px;
		flex-wrap: wrap;
	}
	.vale-label { font-size: 11.5px; color: #60A5FA; }
	.vale-estatus {
		font-size: 10.5px;
		padding: 0.1rem 0.4rem;
		border-radius: 4px;
		background: rgba(245, 158, 11, 0.15);
		color: #fbbf24;
		font-weight: 600;
	}
	.vale-estatus.cerrado {
		background: rgba(34, 197, 94, 0.15);
		color: #4ade80;
	}
	.vale-monto {
		font-size: 11px;
		color: #94a3b8;
		font-weight: 600;
	}
</style>
