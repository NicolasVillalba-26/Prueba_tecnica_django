# Gestión de empresas

Aplicación web desarrollada como prueba técnica para gestionar empresas, sus
contactos, direcciones, categorías y ubicaciones geográficas. El proyecto
demuestra modelado relacional, consultas mediante Django ORM, autenticación,
autorización granular, validaciones, auditoría y una interfaz administrativa
basada en AdminLTE.

## Tecnologías

- Python 3.13.
- Django 5.2 LTS.
- PostgreSQL 17.
- Docker Compose para la base de datos.
- `django-environ` para variables de entorno.
- `psycopg` como controlador de PostgreSQL.
- Bootstrap 5.3.8, AdminLTE 4.8.1 y Bootstrap Icons 1.13.1.

Django se ejecuta localmente desde Windows y PostgreSQL se ejecuta en un
contenedor Docker. Los recursos principales de la interfaz están versionados
localmente, por lo que no dependen de un CDN.

## Estructura principal

```text
config/                 Configuración, URLs, autenticación y pruebas globales
empresas/               Modelos, formularios, vistas y pruebas comerciales
ubicaciones/            Departamentos, ciudades y sus pruebas
static/                  CSS, JavaScript y recursos de terceros
templates/               Plantillas generales y de cada módulo
compose.yaml             Servicio PostgreSQL y volumen persistente
manage.py                Utilidad de administración de Django
requirements.txt         Dependencias Python con versiones fijadas
.env.example             Ejemplo público de configuración
```

## Modelos y relaciones

- `Empresa`: información fiscal y comercial, estado y datos de auditoría.
- `Categoria`: clasificación de empresas.
- `Contacto`: persona asociada a una empresa.
- `Direccion`: dirección postal de un contacto.
- `Ciudad`: ciudad perteneciente a un departamento.
- `Departamento`: división administrativa que agrupa ciudades.

Relaciones relevantes:

```text
Empresa       N --- N Categoria
Empresa       1 --- N Contacto
Contacto      1 --- N Direccion
Ciudad        1 --- N Direccion
Departamento  1 --- N Ciudad
```

La eliminación de una empresa elimina sus contactos y las direcciones
dependientes. La eliminación de un contacto elimina sus direcciones. Una
ciudad utilizada por direcciones y un departamento que contiene ciudades
están protegidos contra eliminación. Eliminar una categoría solamente elimina
sus asociaciones con empresas.

## Funcionalidades

La aplicación dispone de CRUD web para empresas, categorías, contactos,
direcciones, departamentos y ciudades. También incluye:

- Detalle de empresas con categorías, contactos y auditoría.
- Detalle de contactos con sus direcciones.
- Creación de contactos directamente desde una empresa.
- Creación de direcciones directamente desde un contacto.
- Búsqueda de empresas por razón social, RUC o correo electrónico.
- Filtro de empresas por condición: clientes, proveedoras o ambas.
- Filtro de empresas por categoría.
- Combinación simultánea de búsqueda y filtros.
- Paginación con conservación de parámetros GET y orden estable.
- Mensajes comprensibles para validaciones y eliminaciones protegidas.

Rutas principales:

```text
/
/empresas/
/empresas/categorias/
/empresas/contactos/
/empresas/direcciones/
/ubicaciones/departamentos/
/ubicaciones/ciudades/
/admin/
```

## Autenticación y autorización

El sistema utiliza usuarios, sesiones, grupos y permisos nativos de Django.
Las páginas privadas requieren autenticación y cada operación CRUD exige su
permiso correspondiente:

- `view_*`: consultar listados y detalles.
- `add_*`: crear registros.
- `change_*`: modificar registros.
- `delete_*`: eliminar registros.

La autorización se comprueba en el servidor mediante
`PermissionRequiredMixin`. Los menús y botones también se adaptan a los
permisos del usuario, pero ocultar un control visual no sustituye la protección
de la ruta. Los accesos no autorizados reciben una respuesta HTTP 403. El
cierre de sesión se realiza exclusivamente mediante POST con protección CSRF.

### Usuarios y grupos

Un superusuario puede administrar usuarios, grupos y permisos desde
`http://127.0.0.1:8000/admin/`. Para crear perfiles reutilizables, cree un
grupo en Django Admin, asigne sus permisos y agregue los usuarios
correspondientes. También es posible otorgar permisos directamente a un
usuario.

## Validaciones e integridad

Las reglas principales se validan en formularios y modelos y, cuando
corresponde, también mediante restricciones de PostgreSQL:

- RUC obligatorio, con formato `números-dígito` y valor único.
- Correo electrónico con formato válido.
- Cada empresa debe ser cliente, proveedora o ambas.
- Nombre de departamento único.
- Nombre de categoría único.
- Ciudad única por departamento, ignorando mayúsculas y espacios exteriores.
- Integridad referencial mediante `CASCADE`, `PROTECT` y `SET_NULL`.
- Opciones controladas para el tipo de dirección.

La validación actual del RUC comprueba su formato y unicidad, pero no verifica
matemáticamente el dígito verificador. No se incorporó un algoritmo sin una
especificación técnica oficial completa y verificable.

Django no ejecuta automáticamente `full_clean()` al guardar objetos mediante
`save()` u `objects.create()`. Los flujos web y Django Admin sí utilizan los
formularios y validadores definidos; las reglas críticas de condición
comercial y ciudad única cuentan además con restricciones de base de datos.

## Auditoría de empresas

Cada empresa registra fecha y usuario de creación, además de fecha y usuario
de última modificación. Estos campos no se exponen como editables en los
formularios. Las vistas y Django Admin asignan automáticamente al usuario
autenticado. Si se elimina ese usuario, la empresa se conserva y la referencia
de auditoría pasa a ser nula.

## Requisitos previos

- Python 3.13 instalado.
- Docker Desktop con el motor en ejecución.
- Git.

## Instalación

Clone el repositorio y acceda a su directorio:

```powershell
git clone https://github.com/NicolasVillalba-26/Prueba_tecnica_django.git
Set-Location Prueba_tecnica_django
```

Cree y active el entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Variables de entorno

Copie el archivo de ejemplo:

```powershell
Copy-Item .env.example .env
```

Configure en `.env`:

```dotenv
DJANGO_SECRET_KEY=REEMPLAZAR_CON_UNA_CLAVE_ALEATORIA
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_SECURE_SSL_REDIRECT=False
DJANGO_SESSION_COOKIE_SECURE=False
DJANGO_CSRF_COOKIE_SECURE=False
DJANGO_SECURE_HSTS_SECONDS=0
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=False
DJANGO_SECURE_HSTS_PRELOAD=False

POSTGRES_DB=prueba_django
POSTGRES_USER=usuario_django
POSTGRES_PASSWORD=REEMPLAZAR_CON_UNA_CLAVE_SEGURA
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

Genere una clave de Django con:

```powershell
python -c `
  "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

El archivo `.env` contiene secretos y está excluido de Git. No publique
credenciales reales. Django y Docker Compose comparten las variables de
PostgreSQL. Mientras Django se ejecute fuera de Docker,
`POSTGRES_HOST=127.0.0.1` debe mantenerse.

Si el puerto 5432 está ocupado, seleccione otro puerto libre en
`POSTGRES_PORT`; Docker lo publicará hacia el puerto 5432 del contenedor.

## PostgreSQL mediante Docker

Inicie PostgreSQL y compruebe su estado:

```powershell
docker compose up -d
docker compose ps
```

Para consultar los registros del servicio:

```powershell
docker compose logs -f db
```

Para detenerlo sin eliminar los datos:

```powershell
docker compose stop
```

El volumen `datos_postgres` conserva la base de datos aunque se recree el
contenedor. `docker compose down` conserva el volumen; no utilice
`docker compose down -v` si necesita mantener los datos.

## Preparación y ejecución de Django

Con PostgreSQL iniciado y el entorno virtual activo, aplique las migraciones:

```powershell
python manage.py check
python manage.py migrate
```

Cree un superusuario para acceder a Django Admin:

```powershell
python manage.py createsuperuser
```

El comando solicitará el nombre de usuario, correo y contraseña de forma
interactiva. No almacene esas credenciales en el repositorio.

Inicie el servidor:

```powershell
python manage.py runserver
```

Abra `http://127.0.0.1:8000/` e inicie sesión con un usuario autorizado.

## Configuración para producción

En un despliegue servido exclusivamente mediante HTTPS, configure como mínimo:

```dotenv
DJANGO_SECRET_KEY=CLAVE_ALEATORIA_EXTENSA_Y_PRIVADA
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=app.ejemplo.com
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True
DJANGO_SECURE_HSTS_PRELOAD=True
```

No active HSTS hasta confirmar que el dominio y sus subdominios funcionan
siempre mediante HTTPS. La precarga de HSTS requiere además cumplir los
requisitos del navegador correspondiente y debe evaluarse antes de habilitarse.

Los archivos estáticos recolectados se almacenan en `staticfiles/`, directorio
excluido de Git. Para prepararlos durante el despliegue ejecute:

```powershell
python manage.py collectstatic --noinput
```

Estas opciones preparan la configuración de Django, pero el servidor HTTPS, el
proxy inverso y el servicio de archivos estáticos deben ser proporcionados por
la infraestructura de producción.

## Pruebas automatizadas

Con PostgreSQL iniciado, ejecute:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

La suite actual contiene 209 pruebas que cubren modelos, formularios, RUC,
condición comercial, ciudades duplicadas, auditoría, eliminaciones,
autenticación, permisos, búsquedas, filtros y paginación.

## Copia de seguridad

Este comando crea un respaldo SQL en el directorio actual:

```powershell
docker compose exec -T db pg_dump -U usuario_django -d prueba_django > respaldo_prueba_django.sql
```

Los respaldos pueden contener información sensible y no deben publicarse sin
revisión.

## Limitaciones conocidas

- El dígito verificador del RUC no se valida matemáticamente.
- La configuración actual está orientada al desarrollo local. Antes de un
  despliegue deben configurarse HTTPS, cookies seguras, HSTS, hosts permitidos,
  una clave secreta robusta y la gestión de archivos estáticos.
- No se incluye API REST; la aplicación expone una interfaz web renderizada
  por Django.
- Las colisiones de unicidad por solicitudes exactamente simultáneas son
  rechazadas por PostgreSQL, aunque todavía no tienen un tratamiento específico
  adicional al manejo normal de validaciones.

## Recursos frontend

Los archivos compilados de AdminLTE, Bootstrap y Bootstrap Icons se conservan
en `static/vendor/adminlte/`. Los estilos propios están en
`static/css/app.css` y el JavaScript propio en `static/js/app.js`. Los archivos
de terceros no deben modificarse directamente. Sus versiones, atribuciones y
licencias se detallan en [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md).
