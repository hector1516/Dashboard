path = r"C:\OpenCodeProyects\ECCSAWebApps\Dashboard\api\datos.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Add function after the tickets function
old = '''    return {"total_semana": total, "ultimos": ultimos, "por_vehiculo": por_vehiculo}'''

new = '''    return {"total_semana": total, "ultimos": ultimos, "por_vehiculo": por_vehiculo}


def cotizaciones_lista_facturar() -> dict:
    """Cotizaciones en estado 'Lista Para Facturar' (Color=1) con dias transcurridos."""
    conn = get_connection()
    with conn.cursor(as_dict=True) as cur:
        cur.execute("""
            SELECT i.Folio, i.IdCliente, c.Cliente, i.Contacto, i.Descripcion,
                   i.Autor, i.Fecha,
                   h.FechaCambio AS FechaLista,
                   DATEDIFF(day, ISNULL(h.FechaCambio, i.Fecha), GETDATE()) AS DiasTranscurridos
            FROM IndiceMateriales i
            LEFT JOIN clientes c ON i.IdCliente = c.IdCliente
            OUTER APPLY (
                SELECT TOP 1 FechaCambio
                FROM HUB_CotizacionEstatusHistorial
                WHERE Folio = i.Folio AND EstatusNuevo = 1
                ORDER BY FechaCambio DESC
            ) h
            WHERE i.Color = 1
            ORDER BY ISNULL(h.FechaCambio, i.Fecha) ASC
        """)
        rows = cur.fetchall()

        total = len(rows)
        verdes = sum(1 for r in rows if (r.get("DiasTranscurridos") or 0) < 7)
        amarillos = sum(1 for r in rows if 7 <= (r.get("DiasTranscurridos") or 0) <= 14)
        rojos = sum(1 for r in rows if (r.get("DiasTranscurridos") or 0) > 14)

        por_autor = {}
        for r in rows:
            autor = r.get("Autor") or "Sin autor"
            por_autor[autor] = por_autor.get(autor, 0) + 1

        # Top 5 más antiguas
        mas_antiguas = rows[:5]

    return {
        "total": total,
        "verdes": verdes,
        "amarillos": amarillos,
        "rojos": rojos,
        "por_autor": por_autor,
        "mas_antiguas": mas_antiguas,
        "mas_antigua_dias": mas_antiguas[0].get("DiasTranscurridos", 0) if mas_antiguas else 0,
    }'''

assert old in content, "old not found"
content = content.replace(old, new, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Done")
