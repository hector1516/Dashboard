# Sabías que… — Tutoriales para el Dashboard

## Concepto

Nueva pantalla del kiosco del Dashboard que muestra infografías tipo tutorial
con tips y trucos de las apps Admon y Field. Cada vez que se accede a la
pantalla, se muestra una imagen aleatoria diferente.

## Objetivo

- Educar a los colaboradores sobre funciones que ahorran tiempo
- Mostrar tips de uso de Admon y Field
- Cambiar la imagen aleatoriamente en cada acceso a la pantalla
- Mantener el estilo visual del Dashboard (escenario 1920×1080)

## Especificaciones de las imágenes

- **Resolución**: 1920×1080 (Full HD, formato 16:9)
- **Estilo**: Anime chibi, ambientado en oficina de ingeniería
- **Formato**: PNG o JPG
- **Contenido**: Pasos concisos y esenciales, sin saturar
- **Cantidad sugerida**: 26 imágenes para variedad

## Estructura de archivos

```
Dashboard/
├── static/
│   └── sabias_que/          ← imágenes aquí
│       ├── sq_01_reporte_servicio.png
│       ├── sq_02_cotizacion.png
│       └── ...
└── src/
    └── lib/
        └── components/
            └── pantallas/
                └── SabiasQue.svelte   ← nueva pantalla
```

## Prompts para generación de imágenes

Ver archivo `prompts.md` en esta misma carpeta.

## Notas de implementación (pendiente)

1. Crear componente `SabiasQue.svelte`
2. Agregar a `PANTALLAS` en `+page.svelte`
3. Cargar imágenes desde `/static/sabias_que/`
4. Lógica de selección aleatoria al entrar a la pantalla
5. Agregar al snapshot o servir estáticamente
6. Duración de pantalla: 45s (igual que las demás)
