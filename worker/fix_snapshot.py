path = r"C:\OpenCodeProyects\ECCSAWebApps\Dashboard\worker\snapshotter.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Add to bloques
old1 = '''        bloques = {
            "reportes": D.reportes(sunday, hoy_s),'''
new1 = '''        bloques = {
            "cotizaciones_lista": D.cotizaciones_lista_facturar(),
            "reportes": D.reportes(sunday, hoy_s),'''
assert old1 in content, "old1 not found"
content = content.replace(old1, new1, 1)

# Add to snapshot output
old2 = '''        "reportes": bloques["reportes"],'''
new2 = '''        "cotizaciones_lista": bloques["cotizaciones_lista"],
        "reportes": bloques["reportes"],'''
assert old2 in content, "old2 not found"
content = content.replace(old2, new2, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Done")
