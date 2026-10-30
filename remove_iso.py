path = r"C:\OpenCodeProyects\ECCSAWebApps\Dashboard\src\routes\+page.svelte"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Remove imports
content = content.replace("import AsistenciaIso from '$lib/components/AsistenciaIso.svelte';\n", "")
content = content.replace("import LegendsIso from '$lib/components/LegendsIso.svelte';\n", "")
content = content.replace("import PanelControlIso from '$lib/components/PanelControlIso.svelte';\n", "")
content = content.replace("import KilometrosIso from '$lib/components/KilometrosIso.svelte';\n", "")

# Remove screen entries
content = content.replace("\t{ id: 'asistencia_iso', icono: 'door', label: 'Checador de Asistencia' },\n", "")
content = content.replace("\t{ id: 'legends_iso', icono: 'trophy', label: 'Maquina de Legends' },\n", "")
content = content.replace("\t{ id: 'panel_iso', icono: 'panel', label: 'Panel de Control' },\n", "")
content = content.replace("\t{ id: 'km_iso', icono: 'car', label: 'Odometro Mecanico' },\n", "")

# Remove rendering cases
content = content.replace("\t{:else if pantalla.id === 'asistencia_iso'}<AsistenciaIso {datos} />\n", "")
content = content.replace("\t{:else if pantalla.id === 'legends_iso'}<LegendsIso {datos} />\n", "")
content = content.replace("\t{:else if pantalla.id === 'panel_iso'}<PanelControlIso {datos} />\n", "")
content = content.replace("\t{:else if pantalla.id === 'km_iso'}<KilometrosIso {datos} />\n", "")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Done")
