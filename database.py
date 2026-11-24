"""
==============================================================================
MÓDULO: database.py
==============================================================================
Responsabilidad dentro de la arquitectura:
    Este módulo es el núcleo de conectividad de la aplicación. Se encarga de:
    1. Leer la cadena de conexión a la base de datos desde las variables de
       entorno (archivo .env), manteniendo las credenciales fuera del código
       fuente (principio de seguridad: "12-Factor App").
    2. Adaptar el esquema de la URL al driver moderno psycopg (v3), ya que
       Neon y otras plataformas cloud entregan URLs con prefijo "postgres://"
       o "postgresql://", incompatibles con SQLAlchemy + psycopg3 sin la
       corrección explícita del dialecto.
    3. Crear el motor (Engine) de SQLAlchemy, que representa el punto central
       de comunicación con PostgreSQL.
    4. Configurar la fábrica de sesiones (SessionLocal), que genera sesiones
       de base de datos bajo demanda.
    5. Declarar la clase Base de SQLAlchemy, de la que heredarán todos los
       modelos ORM definidos en models.py.
    6. Proveer la función generadora get_db(), utilizada como dependencia
       inyectable en los endpoints de FastAPI para gestionar el ciclo de vida
       de cada sesión de base de datos.

Dependencias:
    - os            : Acceso a variables del sistema operativo y del entorno.
    - dotenv        : Carga de variables desde el archivo .env al entorno del proceso.
    - sqlalchemy    : ORM y abstracción de base de datos relacional.

Autor:          Samuel Mora Vélez
Programa:       Análisis y Desarrollo de Software (ADSO) - Ficha 3504434
==============================================================================
"""

# --- IMPORTACIONES ---

import os
# Librería estándar de Python. Se usa os.getenv() para leer variables de
# entorno que fueron cargadas previamente por load_dotenv().

from dotenv import load_dotenv
# 'python-dotenv' lee el archivo .env ubicado en la raíz del proyecto y
# carga cada par CLAVE=VALOR como variable de entorno del proceso actual.
# Esto evita hardcodear credenciales directamente en el código.

from sqlalchemy import create_engine
# Función de SQLAlchemy que construye el objeto 'Engine', el cual administra
# el pool de conexiones y el dialecto SQL hacia la base de datos destino.

from sqlalchemy.orm import declarative_base, sessionmaker
# declarative_base(): Fábrica que genera la clase Base, el registro central
#                     de metadatos del ORM. Todos los modelos ORM (tablas)
#                     deben heredar de esta clase.
# sessionmaker():     Fábrica de clases Session configurada con parámetros
#                     predefinidos (autocommit, autoflush, engine asociado).


# ==============================================================================
# CARGA DE VARIABLES DE ENTORNO
# ==============================================================================

load_dotenv()
# Ejecuta la lectura del archivo '.env' en el directorio de trabajo actual.
# A partir de este punto, DATABASE_URL y cualquier otra variable definida en
# .env están disponibles en el entorno del proceso (os.environ).


# ==============================================================================
# LECTURA Y VALIDACIÓN DE LA URL DE CONEXIÓN
# ==============================================================================

DATABASE_URL = os.getenv("DATABASE_URL")
# Lee el valor de la variable de entorno 'DATABASE_URL'. Si la variable no
# existe en el entorno (p.ej., el archivo .env no fue creado o la variable
# fue omitida), getenv() devuelve None.

if not DATABASE_URL:
    # Guardia de seguridad temprana (fail-fast): si la URL es None o cadena
    # vacía, la aplicación no tiene sentido continuar. Se eleva ValueError
    # para detener la ejecución con un mensaje de error claro antes de que
    # SQLAlchemy intente conectarse con una URL inválida.
    raise ValueError("No se encontró DATABASE_URL en el archivo .env")


# ==============================================================================
# ADAPTACIÓN DEL ESQUEMA DE URL AL DRIVER PSYCOPG (v3)
# ==============================================================================

# Neon y otras plataformas PostgreSQL en la nube suelen entregar la URL de
# conexión con el esquema genérico "postgres://" o "postgresql://". Sin
# embargo, SQLAlchemy con psycopg3 (el driver moderno) requiere el dialecto
# explícito "postgresql+psycopg://". Las siguientes dos condiciones corrigen
# el esquema en memoria (sin modificar el archivo .env) para que el Engine
# pueda instanciar el driver correcto.

if DATABASE_URL.startswith("postgres://"):
    # Caso 1: URL con esquema antiguo estilo Heroku "postgres://".
    # Se reemplaza únicamente la primera ocurrencia (argumento count=1) para
    # no corromper accidentalmente algún parámetro posterior de la cadena.
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)

elif DATABASE_URL.startswith("postgresql://"):
    # Caso 2: URL con esquema estándar PostgreSQL "postgresql://".
    # Se añade el sufijo "+psycopg" para especificar explícitamente el
    # driver psycopg3, requerido por la versión de SQLAlchemy utilizada.
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)


# ==============================================================================
# CREACIÓN DEL ENGINE (MOTOR DE BASE DE DATOS)
# ==============================================================================

engine = create_engine(
    DATABASE_URL,
    # La URL ya adaptada al dialecto "postgresql+psycopg://" que incluye:
    # usuario, contraseña, host, puerto, nombre de BD y parámetros SSL.

    pool_pre_ping=True
    # pool_pre_ping=True activa una verificación de "salud" de la conexión
    # antes de entregarla desde el pool. Emite un SELECT 1 liviano; si la
    # conexión está caída (timeout de Neon, red intermitente), la descarta y
    # abre una nueva. Es fundamental para bases de datos serverless como Neon,
    # cuyas instancias se suspenden tras un período de inactividad.
)


# ==============================================================================
# CONFIGURACIÓN DE LA FÁBRICA DE SESIONES
# ==============================================================================

SessionLocal = sessionmaker(
    autocommit=False,
    # autocommit=False: SQLAlchemy no confirmará cambios automáticamente.
    # Cada operación de escritura requiere un db.commit() explícito, lo que
    # nos da control total sobre las transacciones y permite hacer rollback
    # ante errores.

    autoflush=False,
    # autoflush=False: Desactiva el envío automático de sentencias SQL al
    # buffer antes de cada consulta. Esto evita comportamientos inesperados
    # cuando el estado del objeto ORM aún no está listo para ser persistido.

    bind=engine
    # Asocia esta fábrica de sesiones al engine creado arriba, de modo que
    # cada sesión generada use la misma conexión configurada.
)


# ==============================================================================
# CLASE BASE DEL ORM
# ==============================================================================

Base = declarative_base()
# Genera la clase Base del sistema ORM declarativo de SQLAlchemy.
# Esta clase actúa como registro de metadatos: cada modelo que herede de
# 'Base' (como ResiduoDB en models.py) quedará registrado y SQLAlchemy
# sabrá cómo mapear esa clase Python a una tabla de PostgreSQL.


# ==============================================================================
# GENERADOR DE SESIÓN (DEPENDENCIA INYECTABLE)
# ==============================================================================

def get_db():
    """
    Generador de sesión de base de datos para inyección de dependencias en FastAPI.

    Este patrón 'yield + try/finally' garantiza que cada sesión de base de
    datos sea cerrada correctamente al terminar una petición HTTP, sin importar
    si esta finalizó con éxito o lanzó una excepción. Es la implementación
    recomendada por la documentación oficial de FastAPI para manejo de sesiones
    SQLAlchemy.

    Flujo de ejecución:
        1. FastAPI invoca get_db() al detectar 'db: Session = Depends(get_db)'
           en la firma de un endpoint.
        2. Se instancia una nueva sesión (db = SessionLocal()).
        3. La sesión 'db' es inyectada en el endpoint mediante 'yield'.
        4. El endpoint ejecuta su lógica usando 'db'.
        5. Al concluir el endpoint (éxito o excepción), el bloque 'finally'
           ejecuta db.close(), liberando la conexión de vuelta al pool.

    Yields:
        db (Session): Sesión activa de SQLAlchemy lista para ejecutar
                      consultas y transacciones contra la base de datos.
    """
    db = SessionLocal()
    # Crea una nueva instancia de sesión usando la fábrica configurada.
    # En este punto la sesión está abierta pero aún no ha ejecutado ninguna
    # consulta ni abierto una transacción real en PostgreSQL.

    try:
        yield db
        # 'yield' suspende la ejecución de este generador y entrega la sesión
        # al endpoint de FastAPI. El endpoint realizará todas sus operaciones
        # (consultas, inserciones, actualizaciones, eliminaciones) usando este
        # objeto 'db'. Cuando el endpoint retorna su respuesta, la ejecución
        # regresa aquí, después del yield.

    finally:
        db.close()
        # Se ejecuta siempre, sin importar si el endpoint tuvo éxito o lanzó
        # una excepción. Cierra la sesión y devuelve la conexión subyacente al
        # pool de conexiones del engine, manteniéndolo disponible para la
        # siguiente petición entrante.
