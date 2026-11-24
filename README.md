# API de Gestión de Residuos Reciclables

API REST desarrollada con **FastAPI** y **SQLAlchemy**, conectada a una base de datos **PostgreSQL** alojada en la nube mediante [Neon](https://neon.tech). Permite registrar, consultar, actualizar, filtrar y eliminar registros de residuos reciclables recolectados.

> **Aprendiz:** Samuel Mora Vélez  
> **Programa:** Análisis y Desarrollo de Software (ADSO) — Ficha 3504434  
> **Versión API:** 2.0.0

---

## Tecnologías Utilizadas

| Tecnología | Versión recomendada | Rol en el proyecto |
|---|---|---|
| Python | 3.11+ | Lenguaje base |
| FastAPI | 0.111+ | Framework web ASGI para la API REST |
| SQLAlchemy | 2.0+ | ORM y gestión de conexiones |
| Pydantic | 2.x | Validación y serialización de esquemas |
| psycopg (v3) | 3.x | Driver PostgreSQL para Python |
| python-dotenv | 1.x | Lectura de variables de entorno desde `.env` |
| Uvicorn | 0.29+ | Servidor ASGI para correr la aplicación |
| PostgreSQL / Neon | 16 | Base de datos relacional en la nube |

---

## Estructura de Carpetas

```
api_residuos/
│
├── .env                  # Variables de entorno (credenciales, NO subir a Git)
├── database.py           # Configuración del engine, sesión y función get_db()
├── models.py             # Modelo ORM ResiduoDB → tabla "residuos" en PostgreSQL
├── main.py               # Aplicación FastAPI: esquemas Pydantic y endpoints CRUD
├── requirements.txt      # Dependencias del proyecto
└── README.md             # Este archivo
```

---

## Instalación desde Cero

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/api_residuos.git
cd api_residuos
```

### 2. Crear y activar un entorno virtual

```bash
# Crear el entorno virtual
python -m venv venv

# Activar en Windows (PowerShell)
venv\Scripts\Activate.ps1

# Activar en macOS / Linux
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install fastapi "uvicorn[standard]" sqlalchemy "psycopg[binary]" python-dotenv pydantic
```

O si existe un `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 4. Configurar las variables de entorno

Crea el archivo `.env` en la raíz del proyecto con el siguiente contenido (reemplaza con tus propias credenciales de Neon):

```env
DATABASE_URL="postgresql://usuario:contraseña@host/nombre_bd?sslmode=require&channel_binding=require"
```

> **Importante:** Nunca subas el archivo `.env` a Git. Añádelo a `.gitignore`:
> ```
> .env
> venv/
> __pycache__/
> ```

### 5. Ejecutar la aplicación

```bash
uvicorn main:app --reload
```

La API estará disponible en:
- **Aplicación:** `http://127.0.0.1:8000`
- **Documentación Swagger UI:** `http://127.0.0.1:8000/docs`
- **Esquema OpenAPI (JSON):** `http://127.0.0.1:8000/openapi.json`

---

## Configuración de Variables de Entorno

| Variable | Descripción | Ejemplo |
|---|---|---|
| `DATABASE_URL` | URL completa de conexión a PostgreSQL (Neon u otro proveedor). Incluye usuario, contraseña, host, nombre de base de datos y parámetros SSL. | `postgresql://user:pass@host/db?sslmode=require` |

> La aplicación adaptará automáticamente el prefijo `postgres://` o `postgresql://` al dialecto `postgresql+psycopg://` requerido por SQLAlchemy + psycopg3.

---

## Tabla de Endpoints

| # | Método | Ruta | Descripción | Código Éxito | Código Error |
|---|--------|------|-------------|:---:|:---:|
| 1 | `GET` | `/` | Verificación de estado (health check) | 200 | — |
| 2 | `POST` | `/residuos/` | Registrar un nuevo residuo | 201 | 400, 422 |
| 3 | `GET` | `/residuos/` | Consultar todos los residuos | 200 | — |
| 4 | `GET` | `/residuos/?tipo_material=X` | Filtrar residuos por tipo de material | 200 | — |
| 5 | `GET` | `/residuos/{id}` | Consultar un residuo por ID | 200 | 404 |
| 6 | `PUT` | `/residuos/{id}` | Actualizar parcialmente un residuo | 200 | 404, 422 |
| 7 | `DELETE` | `/residuos/{id}` | Eliminar un residuo por ID | 200 | 404 |

---

## Ejemplos de Uso

### POST /residuos/ — Registrar un residuo

**Body JSON:**
```json
{
  "id": 1,
  "tipo_material": "Plástico",
  "peso_kg": 12.5,
  "fecha_recoleccion": "2026-11-24",
  "lugar": "Centro de Acopio Robledo",
  "responsable": "Samuel Mora Vélez"
}
```

**Respuesta (201 Created):**
```json
{
  "id": 1,
  "tipo_material": "Plástico",
  "peso_kg": 12.5,
  "fecha_recoleccion": "2026-11-24",
  "lugar": "Centro de Acopio Robledo",
  "responsable": "Samuel Mora Vélez"
}
```

---

### GET /residuos/ — Consultar todos los residuos

**Respuesta (200 OK):**
```json
{
  "total": 2,
  "residuos": [
    { "id": 1, "tipo_material": "Plástico", "peso_kg": 12.5, ... },
    { "id": 2, "tipo_material": "Vidrio",   "peso_kg": 8.0,  ... }
  ]
}
```

---

### GET /residuos/?tipo_material=plastico — Filtrar por tipo

**Respuesta (200 OK):**
```json
{
  "total": 1,
  "filtro_aplicado": "plastico",
  "residuos": [
    { "id": 1, "tipo_material": "Plástico", "peso_kg": 12.5, ... }
  ]
}
```

---

### GET /residuos/1 — Consultar por ID

**Respuesta (200 OK):**
```json
{
  "id": 1,
  "tipo_material": "Plástico",
  "peso_kg": 12.5,
  "fecha_recoleccion": "2026-11-24",
  "lugar": "Centro de Acopio Robledo",
  "responsable": "Samuel Mora Vélez"
}
```

---

### PUT /residuos/1 — Actualizar parcialmente

**Body JSON (solo campos a modificar):**
```json
{
  "peso_kg": 15.0,
  "lugar": "Bodega Sur - Sede Itagüí"
}
```

**Respuesta (200 OK):**
```json
{
  "id": 1,
  "tipo_material": "Plástico",
  "peso_kg": 15.0,
  "fecha_recoleccion": "2026-11-24",
  "lugar": "Bodega Sur - Sede Itagüí",
  "responsable": "Samuel Mora Vélez"
}
```

---

### DELETE /residuos/1 — Eliminar

**Respuesta (200 OK):**
```json
{
  "mensaje": "Residuo con ID 1 eliminado de la base de datos"
}
```

---

## Guía de Arquitectura y Flujo de Datos

### Interacción entre archivos

```
.env
 │  (DATABASE_URL como variable de entorno)
 ▼
database.py ──────────────────────────────────────────────────────────────┐
 │  load_dotenv() lee .env                                                 │
 │  Adapta el esquema de URL para psycopg3                                 │
 │  create_engine() → pool de conexiones a Neon/PostgreSQL                 │
 │  sessionmaker() → fábrica SessionLocal                                  │
 │  declarative_base() → clase Base (registro ORM)                         │
 │  get_db() → función generadora de sesiones                              │
 │                                                                         │
models.py                                                                  │
 │  Importa Base desde database.py                                         │
 │  Define ResiduoDB(Base) → mapa Python ↔ tabla "residuos"               │
 │                                                                         │
 ▼                                                                         │
main.py ◄─────────────────────────────────────────────────────────────────┘
 │  Importa engine y get_db() desde database.py
 │  Importa models para usar ResiduoDB y crear tablas
 │  Base.metadata.create_all(bind=engine) → crea tabla si no existe
 │  Define esquemas Pydantic (validación de entrada/salida)
 │  Define endpoints FastAPI con Depends(get_db) para inyección de sesión
```

### Ciclo de vida de una petición HTTP

A continuación se describe el recorrido completo de una petición **POST /residuos/** desde Swagger UI hasta la respuesta JSON:

1. **El cliente envía la petición** desde Swagger UI (`/docs`): el navegador hace `POST http://127.0.0.1:8000/residuos/` con un cuerpo JSON.

2. **Uvicorn recibe la petición** y la entrega al framework ASGI de FastAPI.

3. **FastAPI resuelve las dependencias**: detecta `db: Session = Depends(get_db)` en la firma del endpoint e invoca `get_db()`, que abre una sesión de SQLAlchemy desde el pool del engine.

4. **Pydantic valida el cuerpo JSON**: el body es parseado y validado contra el esquema `ResiduoCreate`. Si hay errores (tipo incorrecto, campo faltante, `peso_kg <= 0`), FastAPI devuelve automáticamente HTTP 422 sin llegar al handler.

5. **FastAPI invoca el handler** `registrar_residuo(residuo, db)` con los datos validados y la sesión inyectada.

6. **El handler consulta duplicados**: `db.query(ResiduoDB).filter(...).first()` genera `SELECT ... WHERE id = X LIMIT 1` y lo envía a Neon via psycopg3 sobre TLS.

7. **Si el ID ya existe**: se lanza `HTTPException(400)` → FastAPI devuelve `{"detail": "..."}` con código 400.

8. **Si el ID es nuevo**: se crea `ResiduoDB(**residuo.model_dump())`, se llama `db.add()` y `db.commit()`. SQLAlchemy genera y ejecuta `INSERT INTO residuos (...) VALUES (...)` en PostgreSQL (Neon).

9. **`db.refresh(nuevo_residuo)`** recarga el objeto desde la BD, confirmando los datos persistidos.

10. **FastAPI serializa la respuesta**: convierte el objeto ORM `ResiduoDB` al esquema `ResiduoResponse` (gracias a `from_attributes=True`) y lo serializa a JSON.

11. **Uvicorn envía la respuesta** HTTP 201 con el JSON al cliente.

12. **`get_db()` ejecuta el bloque `finally`**: `db.close()` libera la sesión y devuelve la conexión al pool, lista para la siguiente petición.

---

## Glosario Técnico Aplicado

| Término | Definición aplicada al proyecto |
|---|---|
| **ORM** (Object-Relational Mapping) | SQLAlchemy mapea la clase `ResiduoDB` a la tabla `residuos`. Las operaciones como `db.add()`, `db.query()` y `db.delete()` se traducen internamente a `INSERT`, `SELECT` y `DELETE` en PostgreSQL, sin escribir SQL manualmente. |
| **Inyección de Dependencias** | FastAPI resuelve automáticamente `db: Session = Depends(get_db)` antes de ejecutar cada endpoint. `get_db()` provee la sesión de base de datos y garantiza su cierre al terminar, desacoplando la lógica del endpoint de la gestión de conexiones. |
| **Validación de Esquemas (Pydantic)** | Los modelos `ResiduoCreate`, `ResiduoUpdate` y `ResiduoResponse` actúan como contrato de datos. Pydantic valida tipos, restricciones (`gt=0`) y campos obligatorios en cada petición. Los errores se convierten automáticamente en respuestas HTTP 422 con detalle del campo problemático. |
| **Pool de Conexiones** | `create_engine()` mantiene un conjunto de conexiones abiertas y reutilizables a Neon, evitando el costo de abrir y cerrar conexiones TCP+TLS en cada petición. `pool_pre_ping=True` descarta conexiones caídas antes de usarlas, crítico para bases serverless que se suspenden por inactividad. |
| **Variables de Entorno** | La `DATABASE_URL` (con usuario, contraseña y host de Neon) se almacena en `.env` y se lee con `python-dotenv`, nunca se hardcodea en el código fuente. Esto protege las credenciales y facilita despliegues en distintos entornos (desarrollo, producción) sin cambiar el código. |

---

*Proyecto académico desarrollado en el Centro de Servicios y Gestión Empresarial del SENA.*
