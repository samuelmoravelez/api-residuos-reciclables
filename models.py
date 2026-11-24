"""
==============================================================================
MÓDULO: models.py
==============================================================================
Responsabilidad dentro de la arquitectura:
    Este módulo define la capa de persistencia de datos de la aplicación
    mediante el patrón ORM (Object-Relational Mapping). Contiene la clase
    'ResiduoDB', que actúa como mapa bidireccional entre:
        - La tabla "residuos" en la base de datos PostgreSQL (Neon).
        - Objetos Python que FastAPI puede manipular, consultar y serializar.

    Al heredar de 'Base' (importado desde database.py), SQLAlchemy registra
    automáticamente esta clase en sus metadatos, lo que permite que la
    instrucción 'Base.metadata.create_all(bind=engine)' en main.py cree la
    tabla físicamente en la base de datos si aún no existe, sin necesidad de
    escribir DDL (Data Definition Language) manualmente.

Dependencias:
    - sqlalchemy    : Proporciona los tipos de columna (Column, Integer,
                      String, Float, Date) y la clase base del modelo.
    - database      : Importa la instancia de 'Base' (declarative_base)
                      que actúa como registro centralizado del esquema ORM.

Autor:          Samuel Mora Vélez
Programa:       Análisis y Desarrollo de Software (ADSO) - Ficha 3504434
==============================================================================
"""

# --- IMPORTACIONES ---

from sqlalchemy import Column, Integer, String, Float, Date
# Column   : Constructor de columna de tabla. Recibe el tipo de dato y los
#            metadatos de la columna (nullable, index, primary_key, etc.).
# Integer  : Tipo SQL INTEGER. Mapea a 'int' de Python. Usado para IDs y
#            valores numéricos enteros.
# String   : Tipo SQL VARCHAR(n). Mapea a 'str' de Python. Recibe longitud
#            máxima como argumento (p.ej. String(100)).
# Float    : Tipo SQL DOUBLE PRECISION / FLOAT. Mapea a 'float' de Python.
#            Usado para valores decimales como el peso en kilogramos.
# Date     : Tipo SQL DATE. Mapea a 'datetime.date' de Python. Almacena
#            fecha sin componente de hora (YYYY-MM-DD).

from database import Base
# Importa la clase Base generada por declarative_base() en database.py.
# Todos los modelos ORM deben heredar de esta Base para quedar registrados
# en el sistema de metadatos de SQLAlchemy y poder ser creados/consultados.


# ==============================================================================
# MODELO ORM: ResiduoDB
# ==============================================================================

class ResiduoDB(Base):
    """
    Modelo ORM que representa la tabla 'residuos' en la base de datos PostgreSQL.

    Este modelo sigue el patrón Active Record a través del ORM declarativo de
    SQLAlchemy: cada instancia de ResiduoDB corresponde exactamente a una fila
    de la tabla 'residuos'. Las operaciones CRUD se realizan manipulando objetos
    Python de esta clase a través de una sesión de SQLAlchemy (db: Session).

    Tabla SQL generada:
        CREATE TABLE residuos (
            id               INTEGER PRIMARY KEY,
            tipo_material    VARCHAR(100) NOT NULL,
            peso_kg          DOUBLE PRECISION NOT NULL,
            fecha_recoleccion DATE NOT NULL,
            lugar            VARCHAR(150) NOT NULL,
            responsable      VARCHAR(150) NOT NULL
        );

    Atributos:
        id (int):
            Identificador único del registro. Actúa como clave primaria (PRIMARY KEY).
            'autoincrement=False' indica que el valor de la clave primaria es
            proporcionado explícitamente por el cliente de la API al crear un
            registro, en lugar de ser generado automáticamente por la base de datos.
            Se crea un índice B-tree implícito sobre esta columna.

        tipo_material (str):
            Categoría o tipo del residuo reciclable (p.ej. "Plástico", "Vidrio",
            "Metal", "Papel"). Longitud máxima de 100 caracteres. No acepta valores
            nulos. Se indexa ('index=True') para acelerar las consultas de filtrado
            por tipo_material en el endpoint GET /residuos/?tipo_material=...

        peso_kg (float):
            Peso del residuo recolectado expresado en kilogramos. Tipo DOUBLE
            PRECISION en PostgreSQL. No acepta valores nulos. La validación de que
            el valor sea mayor a cero se realiza en la capa de esquemas Pydantic
            (main.py), no en el modelo de base de datos.

        fecha_recoleccion (date):
            Fecha en que se realizó la recolección del residuo. Almacenada como
            tipo DATE en PostgreSQL (formato YYYY-MM-DD). No acepta valores nulos.

        lugar (str):
            Nombre o descripción del lugar físico donde se recolectó el residuo
            (p.ej. "Centro de Acopio Robledo"). Longitud máxima de 150 caracteres.
            No acepta valores nulos.

        responsable (str):
            Nombre completo de la persona responsable de la recolección. Longitud
            máxima de 150 caracteres. No acepta valores nulos.
    """

    __tablename__ = "residuos"
    # Nombre exacto de la tabla que SQLAlchemy buscará o creará en PostgreSQL.
    # Si la tabla aún no existe cuando se ejecuta 'Base.metadata.create_all()',
    # SQLAlchemy emitirá la sentencia CREATE TABLE con este nombre y todas las
    # columnas definidas abajo.

    id = Column(
        Integer,
        # Tipo de dato SQL: INTEGER (entero de 32 bits con signo en PostgreSQL).

        primary_key=True,
        # Declara esta columna como clave primaria de la tabla. PostgreSQL
        # creará automáticamente una restricción UNIQUE y un índice sobre ella,
        # garantizando que no existan dos filas con el mismo ID.

        index=True,
        # Instrucción explícita a SQLAlchemy para crear un índice adicional.
        # Aunque primary_key=True ya implica un índice en PostgreSQL, declararlo
        # explícitamente hace que la intención sea clara en el código.

        autoincrement=False
        # Desactiva el comportamiento predeterminado de autoincremento de
        # SQLAlchemy. El campo 'id' debe ser provisto manualmente en cada
        # petición POST, lo que da control al cliente sobre la numeración.
    )

    tipo_material = Column(
        String(100),
        # Tipo SQL: VARCHAR(100). Almacena cadenas de texto de hasta 100
        # caracteres. PostgreSQL aplica esta restricción de longitud a nivel
        # de base de datos como segunda línea de defensa (la primera es Pydantic).

        nullable=False,
        # Mapea a la restricción NOT NULL en SQL. La base de datos rechazará
        # cualquier INSERT o UPDATE que intente dejar este campo vacío.

        index=True
        # Crea un índice B-tree sobre esta columna en PostgreSQL. Esto optimiza
        # las consultas con filtros WHERE tipo_material = '...' o ILIKE '...',
        # como las del endpoint GET /residuos/?tipo_material=Plástico.
    )

    peso_kg = Column(
        Float,
        # Tipo SQL: DOUBLE PRECISION (punto flotante de 64 bits). Suficiente
        # precisión para representar pesos en kilogramos con decimales.

        nullable=False
        # Campo obligatorio. No se permite insertar un residuo sin especificar
        # su peso.
    )

    fecha_recoleccion = Column(
        Date,
        # Tipo SQL: DATE. Almacena únicamente la fecha (año, mes, día) sin
        # información de hora ni zona horaria. SQLAlchemy convierte automáticamente
        # entre el tipo 'datetime.date' de Python y el tipo DATE de PostgreSQL.

        nullable=False
        # Campo obligatorio. Todo registro de residuo debe tener una fecha de
        # recolección asociada.
    )

    lugar = Column(
        String(150),
        # Tipo SQL: VARCHAR(150). Permite nombres de lugares de hasta 150
        # caracteres, suficiente para descripciones como
        # "Planta de Tratamiento Norte de Medellín - Sede Principal".

        nullable=False
        # Campo obligatorio. Se requiere saber el lugar de recolección para
        # cualquier análisis geográfico o logístico posterior.
    )

    responsable = Column(
        String(150),
        # Tipo SQL: VARCHAR(150). Almacena el nombre completo del responsable,
        # con margen para nombres compuestos de hasta 150 caracteres.

        nullable=False
        # Campo obligatorio. La trazabilidad de responsables es fundamental
        # en sistemas de gestión ambiental y auditoría.
    )
