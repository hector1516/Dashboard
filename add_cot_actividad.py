path = r"C:\OpenCodeProyects\ECCSAWebApps\Dashboard\src\lib\components\pantallas\Actividad.svelte"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Add cotizaciones data reference
content = content.replace(
    "\tconst k = $derived(datos.kilometros);",
    "\tconst k = $derived(datos.kilometros);\n\tconst cl = $derived(datos.cotizaciones_lista);"
)

# Add a cotizaciones section after the km section (before closing of grid-principal)
old = """		<!-- Kilómetros -->
		<div class="seccion">
			<div class="bloque-titulo">🚗 Kilómetros</div>"""
new = """		<!-- Cotizaciones Lista Para Facturar -->
		<div class="seccion cot-seccion">
			<div class="bloque-titulo">📋 Cotizaciones Lista Para Facturar</div>
			<div class="cot-kpis">
				<div class="cot-kpi">
					<span class="cot-val">{cl.total}</span>
					<span class="cot-lab">Total</span>
				</div>
				<div class="cot-kpi verde">
					<span class="cot-val">{cl.verdes}</span>
					<span class="cot-lab">&lt; 7d</span>
				</div>
				<div class="cot-kpi amarillo">
					<span class="cot-val">{cl.amarillos}</span>
					<span class="cot-lab">7-14d</span>
				</div>
				<div class="cot-kpi rojo">
					<span class="cot-val">{cl.rojos}</span>
					<span class="cot-lab">&gt;14d</span>
				</div>
			</div>
			{#if cl.mas_antiguas && cl.mas_antiguas.length > 0}
				<div class="cot-lista">
					{#each cl.mas_antiguas as c, i}
						<div class="cot-item">
							<span class="cot-folio">CM{String(c.Folio).padStart(5, '0')}</span>
							<span class="cot-cliente">{c.Cliente || c.IdCliente}</span>
							<span class="cot-dias" class:rojo={(c.DiasTranscurridos ?? 0) > 14} class:amarillo={7 <= (c.DiasTranscurridos ?? 0) && (c.DiasTranscurridos ?? 0) <= 14}>
								{c.DiasTranscurridos ?? 0}d
							</span>
						</div>
					{/each}
				</div>
			{/if}
			{#if cl.por_autor && Object.keys(cl.por_autor).length > 0}
				<div class="cot-autores">
					{#each Object.entries(cl.por_autor) as [autor, count]}
						<span class="cot-chip">{autor}: {count}</span>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Kilómetros -->
		<div class="seccion">
			<div class="bloque-titulo">🚗 Kilómetros</div>"""
assert old in content, "old not found"
content = content.replace(old, new, 1)

# Add CSS for cotizaciones section
old_css = "\t.vacio { color: var(--color-text-muted); font-size: 0.85rem; text-align: center; padding: 1.5rem; }"
new_css = old_css + """
	.cot-seccion { }
	.cot-kpis { display: flex; gap: 0.5rem; margin-bottom: 0.5rem; flex-wrap: wrap; }
	.cot-kpi { text-align: center; padding: 0.35rem 0.6rem; border-radius: 8px; background: rgba(255, 255, 255, 0.04); min-width: 50px; }
	.cot-kpi.verde { border: 1px solid rgba(34, 197, 94, 0.3); }
	.cot-kpi.amarillo { border: 1px solid rgba(245, 158, 11, 0.3); }
	.cot-kpi.rojo { border: 1px solid rgba(239, 68, 68, 0.3); }
	.cot-val { display: block; font-size: 1.2rem; font-weight: 800; color: var(--color-text); line-height: 1; }
	.cot-lab { display: block; font-size: 0.6rem; color: var(--color-text-muted); margin-top: 2px; text-transform: uppercase; }
	.cot-lista { display: flex; flex-direction: column; gap: 0.3rem; margin-top: 0.4rem; }
	.cot-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.3rem 0.5rem; border-radius: 6px; background: rgba(255, 255, 255, 0.03); font-size: 0.8rem; }
	.cot-folio { font-weight: 800; font-size: 0.8rem; color: #FFAE00; min-width: 55px; }
	.cot-cliente { flex: 1; color: #e2e8f0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.75rem; }
	.cot-dias { font-size: 0.7rem; font-weight: 700; padding: 0.1rem 0.35rem; border-radius: 4px; background: rgba(34, 197, 94, 0.15); color: #4ade80; }
	.cot-dias.amarillo { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }
	.cot-dias.rojo { background: rgba(239, 68, 68, 0.15); color: #f87171; }
	.cot-autores { display: flex; flex-wrap: wrap; gap: 0.3rem; margin-top: 0.4rem; }
	.cot-chip { font-size: 0.65rem; padding: 0.15rem 0.4rem; border-radius: 999px; background: rgba(255, 107, 0, 0.1); color: var(--color-primary-light); border: 1px solid rgba(255, 107, 0, 0.2); }"""
content = content.replace(old_css, new_css, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Done")
