# Reglas de actualización — dashboard

Cómo se despliega **dashboard**. Mismo proceso que las otras cinco apps: la imagen la
construye la CI **en la nube** y Arcane es el único que administra el contenedor.

## Las tres reglas

1. **Tú haces el código y el push. Nada más.**
2. **La CI construye y publica.** El servidor no compila.
3. **El operador da `Update` en Arcane.** Sin ese paso, la imagen nueva existe pero
   nadie la aplica.

## Cómo actualizar

```
1. Modificas el código
2. git commit + git push origin main
3. CI construye en ubuntu-latest y publica en ghcr.io/hector1516/dashboard
4. Arcane → Projects → dashboard → Updates → Update
```

## Dónde mirar

| | |
|---|---|
| Paquete | `dashboard` |
| Imagen | `ghcr.io/hector1516/dashboard` |
| Repositorio | [hector1516/Dashboard](https://github.com/hector1516/Dashboard) |
| Workflow | `.github/workflows/build-image.yml` |
| Jobs | build |
| Puertos | 8101 → 80 (nginx interno) |
| Salud | GET / (200) |
| ¿Toca el servidor? | No |

## Comprobar que salió bien

Antes de ir a Arcane, mira que los jobs estén en verde:

```
https://github.com/hector1516/Dashboard/actions
```

build-image.yml · build

Arcane: `https://docker.ecc-sa.com.mx` → **Projects → dashboard → Updates**.
Ahí debe aparecer la imagen nueva con un digest distinto. Ahí es donde aplicas.

Si el job `deploy` aparece (cuando existe), el mensaje
`ATENCION: lo administra Arcane: no lo recreo` es **correcto**, no un error: el guard
impide que la CI toque el contenedor.

## Qué NO hacer

- **No** ejecutar `docker run`, `docker rm`, `docker restart` ni `docker cp` sobre el
  contenedor. Arcane es el dueño; si le quitas el contenedor, el Project queda roto.
- **No** correr `/opt/apps/_lib/run_app.sh dashboard` — es el camino legacy y recrea por
  fuera de Arcane.
- **No** hacer `docker compose up -d` con el mismo directorio del Project.
- **No** cambiar el nombre del paquete a `${{ github.repository }}` si el repo y el
  paquete se llaman distinto (ver notas de dashboard).
- **No** compilar en el servidor. Para eso está `ubuntu-latest`.

## Qué pasa si algo sale mal

**El workflow falla.** No toques el contenedor. Lee el log en GitHub Actions; el
servidor sigue con la imagen anterior y Arcane nunca vio nada.

**El contenedor no arranca tras el `Update`.** En Arcane: *Logs*. Para volver atrás,
revierte el commit en GitHub, deja que la CI publique la versión anterior y da
`Update` otra vez.

**Arcane no muestra actualización.** Comprueba en el server que la imagen se puede
bajar:

```bash
docker manifest inspect ghcr.io/hector1516/dashboard:latest && echo OK || echo BLOQUEADO
```

Si sale `BLOQUEADO` o `unauthorized`, el paquete está **privado**. Es la causa más
frecuente. Ver la sección siguiente.

## Paquetes: dos cosas que hay que saber

**El paquete hereda la visibilidad del repo.** Nace privado si el repo es privado.
Cambiar el repo a público *después* no arregla un paquete ya creado.

**`GITHUB_TOKEN` solo publica a paquetes enlazados al repo.** Un paquete creado con
push manual nunca queda enlazado, y el push falla con `write_package denied` aunque
los permisos del YAML estén correctos. La cura: borrar el paquete y dejar que la CI
lo recree.

## Notas de dashboard

El flujo más corto de los seis: un solo job, `build`. No hay gate, no hay
deploy, no hay runner. Push y se publica.

El repo (`Dashboard`) y el paquete (`dashboard`) se diferencian solo por mayúscula;
el `IMAGE_NAME` está escrito a mano para no depender de eso.

---

_estandarizado el 2026-10-08 junto a admon, mailbox, dashboard, colaboradores,
workersadmon y field._
