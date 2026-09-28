# Dashboard ECCSA

**Centro de Operaciones de la oficina.** Pantalla de 1920×1080 en la TV del
pasillo: 10 paneles que rotan solos, con avisos en vivo y sonido, y que
**sigue funcionando cuando se cae la red**.

```
http://dashboard.ecc-sa.com.mx:8101/     ← red interna de la oficina
```

Nació del dashboard que estaba dentro de Field (`field/src/routes/dashboard/`),
que se queda ahí hasta el corte. Esta app es independiente: mismo diseño
(ECCSA-Shell), misma base de datos, cero dependencia de las demás.

## Qué se ve

| | Pantalla | Qué aporta |
|---|---|---|
| ⚡ | **La Oficina Ahora** | el latido: último movimiento, actividad de la hora, quién trabaja en qué |
| ⛽ | **Combustible** | km por vehículo (ventana móvil de 7 días), radar de flota con semáforo, sparkline de 7 días |
| 🏆 | **ECCSA Legends** | ganador con corona y rayos, podio con flechas ↑↓, cuenta regresiva al reinicio |
| 📊 | **Reportes** | últimos reportes, dona firmado/pendiente, ranked por ingeniero |
| 🎫 | **Tickets** | tickets de la semana con su foto, los más recientes resaltados |
| 🎂 | **Cumpleaños** | los de **hoy** primero y en grande; el resto del mes |
| 📈 | **Métricas** | KPIs de la semana + **heatmap hora×día**: a qué hora trabaja la oficina |
| 📸 | **Fotografías** | carrusel a pantalla completa de las fotos de los reportes |
| 🌤️ | **Clima** | Monterrey, con la edad del dato a la vista |
| 📌 | **Notas** | avisos internos (solo lectura; el CRUD vive en otro lado) |

## Lo que la hace distinta

- **Autónoma.** El backend calcula un snapshot cada 2 minutos y lo deja en
  disco. Si la base no responde, la pantalla **no se apaga ni muestra ceros**:
  sigue con el último dato y dice "datos de hace 40 min". Hoy el dashboard de
  Field, con la red caída, se veía como una pantalla vacía — y en un tablero
  un cero se interpreta como "no trabaja nadie".
- **Avisos con sonido.** Km, tickets, reportes firmados y cumpleaños disparan
  avisos en vivo. Un reporte firmado o un cumpleaños **toman la pantalla** unos
  segundos, con confeti y arpegio: es lo único que hace que alguien en el
  pasillo voltee a mirar.
- **Audio sin archivos.** Todo sintetizado con WebAudio: 0 KB que servir y
  nada que pueda romperse sin red. Silencio automático de 22:00 a 07:00 y
  panic-mute con cualquier tecla.
- **Corrección de datos.** El carrusel de fotos del dashboard de Field nunca
  avanzaba (el índice no se incrementaba: la foto se quedaba 20 s congelada).
  Aquí gira de verdad. Y las fotos de tickets que venían corruptas en la base
  (15 bytes basura antes del JPEG) se recuperan en lugar de no mostrarse.

## Puesta en marcha

### 1. La TV (una vez, PowerShell como Administrador)

```powershell
git clone https://github.com/hector1516/Dashboard
cd Dashboard
powershell -ExecutionPolicy Bypass -File deploy\tv\instalar-kiosco.ps1
```

Deja la TV con: entrada en el hosts apuntando al ServerVM, Edge en modo kiosco
a pantalla completa con sonido habilitado, autoinicio al encender y apagado del
monitor entre 23:00 y 07:00.

### 2. El servidor

```bash
docker build -t dashboard:latest .
powershell -ExecutionPolicy Bypass -File deploy\run_container.ps1
```

Contenedor `dashboard` en el puerto **8101**, volumen `dashboard_data` para el
snapshot y los medios. Las credenciales entran por `--env-file`; no hay ninguna
en el repo ni en la imagen.

### 3. Verificar

```bash
curl http://dashboard.ecc-sa.com.mx:8101/healthz
```

## Desarrollo

```bash
npm install
npm run dev            # http://localhost:5173
npm run build
npx svelte-check --tsconfig ./tsconfig.json
```

Sin base de datos no hay nada que ver: la pantalla muestra "sin datos". Para
desarrollar con datos, `KIOSKO_DATA=/tmp/kiosko` + `python worker/snapshotter.py
--una-vez` (ver `AGENTS.md`).

Parámetros útiles: `?pantalla=legends` (una pantalla fija), `?sinanim=1` (sin
animaciones, para capturas), `?debug=1` (geometría de la pantalla en el DOM).

## Documentación

`AGENTS.md` es la referencia técnica: arquitectura, reglas de offline, contrato
de datos, despliegue, y la lista de bugs ya encontrados (para que nadie los
vuelva a pasar).

## Stack

SvelteKit 2 + Svelte 5 (runes) + Tailwind v4 · FastAPI + pymssql · nginx +
supervisor · Docker. Diseño: [ECCSA-Shell](https://github.com/hector1516/ECCSA-Shell).
