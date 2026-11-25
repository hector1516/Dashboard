"""Comprueba que las imágenes de Dashboard no se vayan de peso.

- **Falla** si una imagen de `sabias_que/` o `images/` pasa de MAX_KB o si queda
  un `.png` en esas carpetas.
- Mientras exista `SabiasQue.svelte` (la pantalla se retiró en la 2.0, el
  archivo no), también falla si su lista apunta a un archivo que no existe.

Uso:  python scripts/check_assets.py     (sale con 1 si falla)
"""
import io
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.path.join(RAIZ, "static")
SABIASQUE = os.path.join(RAIZ, "src", "lib", "components", "pantallas", "SabiasQue.svelte")

MAX_KB = 200
RASTER = (".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif")
CONTROLADAS = ("sabias_que", "images")


def rutas_de_sabiasque():
    """Rutas que lista la pantalla retirada. Sin el archivo no hay lista."""
    if not os.path.isfile(SABIASQUE):
        return None
    texto = io.open(SABIASQUE, encoding="utf-8").read()
    return re.findall(r"'(/sabias_que/[^']+)'", texto)


def main():
    problemas = []

    for carpeta in CONTROLADAS:
        d = os.path.join(STATIC, carpeta)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            ruta = os.path.join(d, f)
            if not f.lower().endswith(RASTER):
                continue
            kb = os.path.getsize(ruta) / 1024
            if kb > MAX_KB:
                problemas.append(f"{carpeta}/{f}: {kb:.0f} KB (máximo {MAX_KB} KB)")
            if carpeta == "sabias_que" and f.lower().endswith(".png"):
                problemas.append(f"{carpeta}/{f}: quedó el PNG original")

    rutas = rutas_de_sabiasque()
    if rutas is not None:
        if not rutas:
            problemas.append("no pude leer la lista de imágenes de SabiasQue.svelte")
        for ruta in rutas:
            if not os.path.isfile(os.path.join(STATIC, ruta.lstrip("/"))):
                problemas.append(f"SabiasQue.svelte apunta a {ruta}, que no existe")

    for p in problemas:
        print(f"[PESO ] {p}")
    print(f"\n{len(problemas)} problemas" if problemas else "\nAssets OK")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
