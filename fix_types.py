path = r"C:\OpenCodeProyects\ECCSAWebApps\Dashboard\src\lib\kiosk\types.ts"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Add interface before Snapshot
old = "export interface Snapshot {"
new = """export interface CotizacionLista {
	total: number;
	verdes: number;
	amarillos: number;
	rojos: number;
	por_autor: Record<string, number>;
	mas_antiguas: { Folio: number; IdCliente: string; Cliente: string; Contacto: string; Descripcion: string; Autor: string; Fecha: string; FechaLista: string; DiasTranscurridos: number }[];
	mas_antigua_dias: number;
}

export interface Snapshot {"""
assert old in content, "old not found"
content = content.replace(old, new, 1)

# Add to Snapshot interface
old2 = "\tmetricas: {"
new2 = "\tcotizaciones_lista: CotizacionLista;\n\n\tmetricas: {"
assert old2 in content, "old2 not found"
content = content.replace(old2, new2, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Done")
