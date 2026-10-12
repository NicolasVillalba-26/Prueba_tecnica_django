# Gestión de empresas

Aplicación web en Django para administrar empresas, categorías, contactos,
direcciones, departamentos y ciudades. Incluye autenticación, permisos
granulares, auditoría de empresas, búsquedas, filtros y paginación.

## Tecnologías

- Python 3.13 y Django 5.2 LTS.
- PostgreSQL 17 en Docker Compose.
- `django-environ` para la configuración por entorno.
- `psycopg` como controlador de PostgreSQL.
- AdminLTE 4, Bootstrap 5 y Bootstrap Icons, servidos localmente.

## Estructura

```text
config/          Configuración, URLs, autenticación y utilidades compartidas
empresas/        Dominio de empresas, categorías, contactos y direcciones
ubicaciones/     Dominio de departamentos y ciudades
templates/       Interfaz HTML y componentes reutilizables
static/          CSS, JavaScript y recursos frontend de terceros
compose.yaml     Servicio PostgreSQL y volumen persistente
manage.py        Utilidad de administración de Django
requirements.txt Dependencias Python fijadas
.env.example     Ejemplo público de variables de entorno
```

## Funcionalidades

- CRUD de empresas, categorías, contactos, direcciones, departamentos y ciudades.
- Búsqueda de empresas por razón social, RUC o correo electrónico.
- Filtros por condición comercial y categoría.
- Paginación que conserva los parámetros de búsqueda y filtros.
- Validación de RUC, correo, condición comercial y unicidad geográfica.
- Protección de relaciones mediante `CASCADE`, `PROTECT` y `SET_NULL`.
- Registro automático de creación y modificación de empresas.
- Autenticación y autorización mediante usuarios, grupos y permisos de Django.

## Modelos y relaciones

```text
Empresa       N --- N Categoria
Empresa       1 --- N Contacto
Contacto      1 --- N Direccion
Ciudad        1 --- N Direccion
Departamento  1 --- N Ciudad
```

## Requisitos

- Python 3.13.
- Docker Desktop con Docker Compose.
- Git.

## Instalación

```powershell
git clone https://github.com/NicolasVillalba-26/Prueba_tecnica_django.git
Set-Location Prueba_tecnica_django
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite `.env` y defina una clave secreta, los hosts permitidos y las
credenciales de PostgreSQL. El archivo contiene secretos y está excluido de
Git. Puede generar una clave de Django con:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Base de datos

Inicie PostgreSQL y aplique las migraciones:

```powershell
docker compose up -d
docker compose ps
python manage.py check
python manage.py migrate
```

El volumen `datos_postgres` conserva la información al recrear el contenedor.
No ejecute `docker compose down -v` si necesita mantener los datos.

## Ejecución

Cree un usuario administrador la primera vez:

```powershell
python manage.py createsuperuser
```

Inicie la aplicación:

```powershell
python manage.py runserver
```

Abra `http://127.0.0.1:8000/`. La administración de usuarios, grupos y
permisos está disponible en `http://127.0.0.1:8000/admin/`.

## Variables de entorno

Las opciones disponibles están documentadas en `.env.example`. Para
producción configure al menos:

- `DJANGO_SECRET_KEY` con una clave privada robusta.
- `DJANGO_DEBUG=False`.
- `DJANGO_ALLOWED_HOSTS` con los dominios reales.
- Redirección HTTPS, cookies seguras y HSTS únicamente cuando HTTPS esté
  correctamente configurado.
- Credenciales PostgreSQL distintas a los valores de ejemplo.

Antes de desplegar, recolecte los archivos estáticos:

```powershell
python manage.py collectstatic --noinput
```

La infraestructura de producción debe proporcionar el servidor de
aplicaciones, HTTPS y el servicio de archivos estáticos.

## Limitaciones conocidas

- El RUC se valida por formato y unicidad, pero no se calcula matemáticamente
  su dígito verificador.
- No se incluye una API REST; la interfaz se renderiza en el servidor.
- La configuración incluida está orientada al desarrollo local y requiere un
  servidor de aplicaciones y un proxy inverso para producción.

Las atribuciones de los recursos frontend se detallan en
[`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md).
