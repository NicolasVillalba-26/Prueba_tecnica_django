# Gestión de empresas

Proyecto de prueba técnica para gestionar empresas, contactos, direcciones, categorías y ubicaciones con Django. Actualmente contiene la estructura base y los modelos geográficos.

## Arquitectura de desarrollo

- Django 5.2 se ejecuta localmente desde Windows y el entorno `.venv`.
- PostgreSQL 17 se ejecuta en Docker Compose.
- Django accede a PostgreSQL por `127.0.0.1` y el puerto definido en `POSTGRES_PORT`.
- El volumen `datos_postgres` conserva la base aunque se recree el contenedor.

## Interfaz

La interfaz utiliza recursos locales de AdminLTE 4.8.1, Bootstrap 5.3.8 y Bootstrap Icons 1.13.1. Los archivos proceden de sus paquetes oficiales de npm y se conservan compilados dentro de `static/vendor/adminlte/`; la aplicación no depende de un CDN para renderizar su estructura principal.

Las plantillas se organizan de la siguiente forma:

- `templates/base.html`: estructura general de AdminLTE.
- `templates/includes/`: barra superior, panel lateral, pie, mensajes y paginación.
- `templates/principal.html`: página inicial protegida.
- `templates/registration/login.html`: acceso mediante sesiones de Django.

Los estilos propios están en `static/css/app.css` y los futuros comportamientos propios se incorporarán en `static/js/app.js`. Los archivos originales de terceros no deben modificarse directamente.

La navegación agrupa el panel principal, la gestión comercial y las ubicaciones. Todas las opciones enlazan a sus CRUD protegidos. El botón de la cabecera utiliza el mecanismo oficial `data-lte-toggle="sidebar"` para plegar el menú en escritorio y móvil.

La API REST está prevista para una etapa posterior.

## Módulos disponibles

La interfaz permite listar, crear, editar y eliminar departamentos, ciudades, categorías, empresas, contactos y direcciones. También incluye:

- Detalle de empresas con categorías, auditoría y contactos.
- Detalle de contactos con sus direcciones.
- Creación protegida de contactos desde una empresa.
- Creación protegida de direcciones desde un contacto.
- Validaciones de unicidad e integridad proporcionadas por Django y PostgreSQL.
- Auditoría automática al crear y modificar empresas.
- Confirmación por POST y CSRF para todas las eliminaciones.

Rutas principales:

```text
/empresas/
/empresas/contactos/
/empresas/direcciones/
/empresas/categorias/
/ubicaciones/departamentos/
/ubicaciones/ciudades/
```

## Requisitos previos

- Python 3.13.
- Docker Desktop con el motor en ejecución.
- Git.

## Preparación del entorno

Desde PowerShell, en la raíz del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite `.env` y sustituya los valores marcados con `REEMPLAZAR_CON_CLAVE_SEGURA`. Puede generar la clave de Django con:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

La contraseña de PostgreSQL definida en `.env` es compartida automáticamente por Docker Compose y Django. Mientras Django se ejecute fuera de Docker, mantenga `POSTGRES_HOST=127.0.0.1`.

El puerto habitual es `5432`. En este equipo la configuración local utiliza `5435` porque los puertos `5432`, `5433` y `5434` ya estaban ocupados. Este ajuste sólo está en el archivo `.env`, que no se versiona.

## PostgreSQL con Docker

Inicie la base y consulte su estado:

```powershell
docker compose up -d
docker compose ps
docker compose logs -f db
```

Para detenerla sin eliminar sus datos:

```powershell
docker compose stop
```

Para volver a iniciarla:

```powershell
docker compose start
```

`docker compose down` elimina el contenedor y la red, pero conserva el volumen. No use `docker compose down -v` si desea mantener los datos.

## Django

Con PostgreSQL saludable, prepare la base e inicie Django:

```powershell
python manage.py check
python manage.py migrate
python manage.py runserver
```

El sitio administrativo estará disponible en `http://127.0.0.1:8000/admin/`.

## Copia de seguridad

El siguiente comando crea un respaldo SQL en la carpeta actual:

```powershell
docker compose exec -T db pg_dump -U usuario_django -d prueba_django > respaldo_prueba_django.sql
```

Los respaldos pueden contener información sensible y no deben publicarse sin revisión.

## Visual Studio Code

Seleccione `.venv\Scripts\python.exe` mediante **Python: Select Interpreter**.

## Estado actual

Los seis modelos disponen de CRUD web protegido y administración mediante Django Admin. La API REST y las funciones avanzadas de búsqueda y filtrado continúan pendientes.

## Pruebas

Con PostgreSQL iniciado, ejecute:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```
