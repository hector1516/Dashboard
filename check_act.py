path = r"C:\OpenCodeProyects\ECCSAWebApps\Dashboard\src\lib\components\pantallas\Actividad.svelte"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()
import re
for m in re.finditer(r"<!-- Kil.*", content):
    print(repr(m.group()[:80]))
