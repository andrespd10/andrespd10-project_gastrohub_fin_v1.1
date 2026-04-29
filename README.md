# GastroHub - Sistema POS para Restaurantes

**GastroHub** es un sistema integral de Punto de Venta (POS) para restaurantes, diseñado para optimizar la operación entre meseros, cocina y administración.

## Arquitectura del Sistema

GastroHub usa una arquitectura en capas bien definida:

- **FastAPI** como servidor API.
- **SQLAlchemy** para acceso a datos con ORM sobre MySQL.
- **Pydantic v2** para validación y serialización.
- **Middleware** global de rate limiting y manejo de errores.

##  Instalación Paso a Paso

### 1. Clonar el repositorio

git clone https://github.com/andrespd10/andrespd10-project_gastrohub_fin_v1.1.git

# Entras a la carpeta que acabas de clonar y abres el visual studio code parado en esa ruta

cd andrespd10-project_gastrohub_fin

### 2. Crear y activar entorno virtual
```bash
python -m venv .venv

.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```
> **Importante**: Usa `bcrypt==4.0.1` para garantizar compatibilidad con el hashing de contraseñas.

### 4. Configurar `.env`

Crea un archivo `.env` en la raíz del proyecto llamado: .env

A continuacion pega este codigo en el archivo .env y si necesitas cambiar db_user o db_host o el db_port haces esos cambios manuales asi como tambien si deseas cambiar el nombre si no lo dejas por defecto y solo cambias las credenciales a continuaciion copia todo este codigo y lo pegas en el archivo .env

# Principio del archivo .env

# GastroHub configuration

# Credenciales de la base de datos

DB_USER=root
DB_PASSWORD="tus credenciales"
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=gastrohub_project_db

DATABASE_URL=mysql+pymysql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

SECRET_KEY=8f3kjsd89f7sd98f7sdf98sdf7sdf9sdf87sdf
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
RESET_TOKEN_EXPIRE_MINUTES=15
    
ALLOWED_HOSTS=http://localhost:4200,http://127.0.0.1:4200,http://localhost,http://127.0.0.1



DEBUG=True

# Nueva variable para el motor de límites
RATE_LIMIT_STORAGE_URL=memory://
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_LOGIN=25

# --- RECAPTCHA ---
RECAPTCHA_SECRET_KEY=6LeetK0sAAAAAERMv3B2h32JAppKqmGfKTAaW0j4
RECAPTCHA_VERIFY_URL=https://www.google.com/recaptcha/api/siteverify



# Configuración de Gmail Real
MAIL_USERNAME=criollofleider@gmail.com
MAIL_PASSWORD=jwfn ieqs pzfd wiib
MAIL_FROM=criollofleider@gmail.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
MAIL_ENABLED=True

# frontend
FRONTEND_URL=http://localhost:4200

# Fin del archivo .env


### 5. Iniciar bases de datos y semilla
Asegúrate de que el servicio MySQL (Workbench) esté activo. Luego:
bash
# Crea la base de datos si no existe (desde MySQL client o Workbench)

CREATE DATABASE gastrohub_db;

# Configura el .env con las credenciales de tu Base de Datos

# Ejecuta la app para crear las tablas, esto lo haces en la terminal dentro del proyecto en visual studio code con:

uvicorn app.main:app --reload --port 3000

"Al ejecutar la app por primera vez, SQLAlchemy creará las tablas automáticamente. Luego, detén el servidor (Ctrl + C) y ejecuta el script para cargar los datos iniciales (la semilla de datos):"

# Ejecutar semilla de base de datos

A continuacion corres la semilla las bases de datos que esta en la carpeta (scrip/seed.py) para insertar usuarios, mesas y productos a la BD para las respectivas pruebas esto lo haces en la terminal con el comando:

python scripts/seed.py

Ahora si vuelve a correr el servidor de nuevo con uvicorn app.main:app --reload --port 3000

## Host de Desarrollo

- API local: `http://127.0.0.1:3000`

## 👥 Credenciales de Prueba (demo)

**Nota**: No hay registro público. Los usuarios deben ser creados por un ADMIN existente.

| Rol      | Email                | Password     |
|----------|----------------------|--------------|
| Admin    | admin@gastrohub.com  | admin12345   |
| Mesero   | mesero@gastrohub.com | mesero12345  |
| Cocinero | cocina@gastrohub.com | cocina12345  |

## Documentación de la API

- Swagger UI: `http://127.0.0.1:3000/docs`
- ReDoc: `http://127.0.0.1:3000/redoc`

## Endpoints Principales

### Auth (`/auth`)
- `POST /auth/login` - Login y token de acceso
- `POST /auth/request-password-reset` - Solicitar token de recuperación (RESET)
- `POST /auth/reset-password` - Confirmar cambio de contraseña
- `POST /auth/request-otp` - Generar OTP (simulado)
- `POST /auth/verify-otp` - Verificar OTP y obtener token

### Usuarios (`/usuarios`)
- `GET /usuarios` - Listar
- `GET /usuarios/{usuario_id}` - Detallar
- `POST /usuarios` - Crear
- `PUT /usuarios/{usuario_id}` - Actualizar
- `DELETE /usuarios/{usuario_id}` - Eliminar

### Productos (`/productos`)
- `GET /productos` - Listar
- `GET /productos/{producto_id}` - Detallar
- `POST /productos` - Crear
- `PUT /productos/{producto_id}` - Actualizar
- `DELETE /productos/{producto_id}` - Eliminar

### Mesas (`/mesas`)
- `GET /mesas` - Listar todas
- `GET /mesas/disponibles` - Listar disponibles
- `GET /mesas/{mesa_id}` - Detallar
- `POST /mesas` - Crear
- `DELETE /mesas/{mesa_id}` - Eliminar

### Pedidos (`/pedidos`)
- `GET /pedidos` - Listar
- `GET /pedidos/{pedido_id}` - Detallar
- `POST /pedidos` - Crear
- `POST /pedidos/{pedido_id}/detalles` - Agregar items
- `POST /pedidos/{pedido_id}/cerrar` - Cerrar pedido
- `POST /pedidos/{pedido_id}/pago` - Registrar pago
- `DELETE /pedidos/{pedido_id}` - Eliminar

### Detalles de Pedido (`/detalle-pedido`)
- `GET /detalle-pedido` - Listar
- `GET /detalle-pedido/{detalle_id}` - Detallar
- `PATCH /detalle-pedido/{detalle_id}` - Actualizar cantidad/estado  mesero accede a cantidad pero si es cocinero solo accede a estado
- `DELETE /detalle-pedido/{detalle_id}` - Eliminar

### Pagos (`/pagos`)
- `GET /pagos` - Listar
- `GET /pagos/{pago_id}` - Detallar
- `DELETE /pagos/{pago_id}` - Eliminar

##  Seguridad e Infraestructura

### Rate Limiting
- `POST /auth/login`: límite configurado en `RATE_LIMIT_LOGIN` (por defecto 3 por minuto)
- `POST /usuarios`: 5/min
- `POST /auth/reset-password`: 2/min
- `POST /pagos`: 10/min
- Resto: `RATE_LIMIT_PER_MINUTE` (por defecto 60)

### JWT y RBAC
- `ACCESS_TOKEN` tiene duración en `ACCESS_TOKEN_EXPIRE_MINUTES` (60 minutos)
- `RESET_TOKEN` tiene duración en `RESET_TOKEN_EXPIRE_MINUTES` (15 minutos)
- Roles:
  - `ADMIN`: control total del sistema, gestión de usuarios (puede crear más admins)
  - `MESERO`: operaciones de mesas, pedidos y pagos
  - `COCINA`: gestión de estado de pedidos

**Nota**: Los usuarios solo pueden ser creados por administradores existentes. No hay registro público.

## Desarrollo local con MySQL

- MySQL + Workbench (confirmar que el servicio esté activo y la DB creada)
- Cadena de conexión en `.env` en formato `mysql+pymysql://user:pass@host:3306/dbname`
- Se usa SQLAlchemy `Base.metadata.create_all(bind=engine)` para crear tablas automáticamente

Muchas gracias por llegar hasta aqui.


**Desarrollado con enfoque técnico y profesional para el proyecto de grado SENA**
