path = r"C:\OpenCodeProyects\ECCSAWebApps\Dashboard\src\lib\components\pantallas\Metricas.svelte"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Add cotizaciones data reference after the metricas const
content = content.replace(
    "\tconst m = $derived(datos.metricas);",
    "\tconst m = $derived(datos.metricas);\n\tconst cl = $derived(datos.cotizaciones_lista);"
)

# Add cotizaciones section before the closing </div> of the screen
# Find the last </div> before </style> or end
old = "</div>\n\n<style>"
new = """\t<!-- Cotizaciones Lista Para Facturar -->
\t<div class="cotizaciones-lista">
\t\t<div class="cot-titulo">📋 Cotizaciones Lista Para Facturar</div>
\t\t<div class="cot-kpis">
\t\t\t<div class="cot-kpi">
\t\t\t\t<span class="cot-val">{cl.total}</span>
\t\t\t\t<span class="cot-lab">Total</span>
\t\t\t</div>
\t\t\t<div class="cot-kpi verde">
\t\t\t\t<span class="cot-val">{cl.verdes}</span>
\t\t\t\t<span class="cot-lab">< 7 días</span>
\t\t\t</div>
\t\t\t<div class="cot-kpi amarillo">
\t\t\t\t<span class="cot-val">{cl.amarillos}</span>
\t\t\t\t<span class="cot-lab">7-14 días</span>
\t\t\t</div>
\t\t\t<div class="cot-kpi rojo">
\t\t\t\t<span class="cot-val">{cl.rojos}</span>
\t\t\t\t<span class="cot-lab">> 14 días</span>
\t\t\t</div>
\t\t</div>
\t\t{#if cl.mas_antiguas && cl.mas_antiguas.length > 0}
\t\t\t<div class="cot-lista">
\t\t\t\t{#each cl.mas_antiguas as c, i}
\t\t\t\t\t<div class="cot-item">
\t\t\t\t\t\t<span class="cot-folio">CM{String(c.Folio).padStart(5, '0')}</span>
\t\t\t\t\t\t<span class="cot-cliente">{c.Cliente || c.IdCliente}</span>
\t\t\t\t\t\t<span class="cot-dias" class:rojo={(c.DiasTranscurridos ?? 0) > 14} class:amarillo={7 <= (c.DiasTranscurridos ?? 0) && (c.DiasTranscurridos ?? 0) <= 14}>
\t\t\t\t\t\t\t{c.DiasTranscurridos ?? 0}d
\t\t\t\t\t\t</span>
\t\t\t\t\t\t<span class="cot-autor">{c.Autor}</span>
\t\t\t\t\t</div>
\t\t\t\t{/each}
\t\t\t</div>
\t\t{/if}
\t\t{#if cl.por_autor && Object.keys(cl.por_autor).length > 0}
\t\t\t<div class="cot-autores">
\t\t\t\t{#each Object.entries(cl.por_autor) as [autor, count]}
\t\t\t\t\t<span class="cot-autor-chip">{autor}: {count}</span>
\t\t\t\t{/each}
\t\t\t</div>
\t\t{/if}
\t</div>

</div>

<style>"""
assert old in content, "old not found"
content = content.replace(old, new, 1)

# Add CSS for cotizaciones section before the last closing brace of style
old_css = "\t.empty { text-align: center; color: var(--color-text-muted); padding: 3rem 1rem; font-size: 0.9rem; }"
new_css = old_css + """
	.cotizaciones-lista { margin-top: 1rem; padding: 0.75rem; background: rgba(255, 107, 0, 0.05); border: 1px solid rgba(255, 107, 0, 0.15); border-radius: 12px; }
	.cot-titulo { font-size: 0.9rem; font-weight: 700; color: var(--color-primary-light); margin-bottom: 0.5rem; }
	.cot-kpis { display: flex; gap: 0.75rem; margin-bottom: 0.5rem; flex-wrap: wrap; }
	.cot-kpi { text-align: center; padding: 0.4rem 0.75rem; border-radius: 8px; background: rgba(255, 255, 255, 0.04); min-width: 60px; }
	.cot-kpi.verde { border: 1px solid rgba(34, 197, 94, 0.3); }
	.cot-kpi.amarillo { border: 1px solid rgba(245, 158, 11, 0.3); }
	.cot-kpi.rojo { border: 1px solid rgba(239, 68, 68, 0.3); }
	.cot-val { display: block; font-size: 1.3rem; font-weight: 800; color: var(--color-text); line-height: 1; }
	.cot-lab { display: block; font-size: 0.6rem; color: var(--color-text-muted); margin-top: 2px; text-transform: uppercase; }
	.cot-lista { display: flex; flex-direction: column; gap: 0.3rem; }
	.cot-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.3rem 0.5rem; border-radius: 6px; background: rgba(255, 255, 255, 0.03); font-size: 0.8rem; }
	.cot-folio { font-weight: 800; font-size: 0.85rem; color: #FFAE00; min-width: 60px; }
	.cot-cliente { flex: 1; color: #e2e8f0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.cot-dias { font-size: 0.75rem; font-weight: 700; padding: 0.1rem 0.4rem; border-radius: 4px; background: rgba(34, 197, 94, 0.15); color: #4ade80; }
	.cot-dias.amarillo { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }
	.cot-dias.rojo { background: rgba(239, 68, 68, 0.15); color: #f87171; }
	.cot-autor { font-size: 0.7rem; color: var(--color-text-muted); }
	.cot-autores { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.5rem; }
	.cot-autor-chip { font-size: 0.7rem; padding: 0.2rem 0.5rem; border-radius: 999px; background: rgba(255, 107, 0, 0.1); color: var(--color-primary-light); border: 1px solid rgba(255, 107, 0, 0.2); }"""
content = content.replace(old_css, new_css, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Done")
