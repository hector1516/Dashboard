path = r"C:\OpenCodeProyects\ECCSAWebApps\Dashboard\src\lib\components\pantallas\Metricas.svelte"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    '<span class="cot-lab">< 7 días</span>',
    '<span class="cot-lab">&lt; 7 días</span>'
)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Done")
