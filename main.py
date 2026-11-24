"""
==============================================================================
MÓDULO: main.py
==============================================================================
Responsabilidad dentro de la arquitectura:
    Este módulo es el punto de entrada y núcleo de la aplicación. Orquesta
    todos los demás módulos y define la interfaz pública de la API REST.
    Sus responsabilidades son:

    1. Inicializar la aplicación FastAPI con sus metadatos (título, versión,
       descripción visible en Swagger UI).
    2. Crear el esquema de base de datos al arrancar la aplicación, usando
       los metadatos del ORM definidos en models.py.
    3. Declarar los esquemas de validación (Pydantic) para las entradas y
       salidas de datos, garantizando que el contrato de la API sea explícito
       y seguro en ambas direcciones.
    4. Implementar los seis endpoints REST del CRUD de residuos reciclables:
       - POST   /residuos/           → Registrar un nuevo residuo.
       - GET    /residuos/           → Consultar todos (con filtro opcional).
       - GET    /residuos/{id}       → Consultar uno por ID.
       - PUT    /residuos/{id}       → Actualizar parcialmente un residuo.
       - DELETE /residuos/{id}       → Eliminar un residuo.
       - GET    /                    → Ruta raíz de bienvenida.

Dependencias:
    - fastapi       : Framework web ASGI para construcción de APIs REST.
    - pydantic      : Validación de datos y serialización de esquemas JSON.
    - sqlalchemy    : Sesión ORM para interacción con la base de datos.
    - typing        : Tipos genéricos de Python (Optional).
    - datetime      : Tipo de dato 'date' para fechas sin hora.
    - models        : Modelos ORM (clases de tabla) definidos en models.py.
    - database      : Engine y función get_db() de database.py.

Autor:          Samuel Mora Vélez
Programa:       Análisis y Desarrollo de Software (ADSO) - Ficha 3504434
==============================================================================
"""

# --- IMPORTACIONES ---

from fastapi import FastAPI, HTTPException, Query, Depends
# FastAPI      : Clase principal del framework. Instancia la aplicación ASGI.
# HTTPException: Excepción estándar de FastAPI para retornar respuestas de
#                error HTTP con código de estado y mensaje JSON estructurado.
# Query        : Descriptor de parámetro de consulta (query string) en la URL.
#                Permite declarar parámetros opcionales como ?tipo_material=X
#                con descripción, validaciones y valor por defecto.
# Depends      : Sistema de Inyección de Dependencias de FastAPI. Permite
#                declarar que un endpoint necesita un recurso (como una sesión
#                de base de datos) que FastAPI resolverá y suministrará
#                automáticamente antes de ejecutar el handler.

from pydantic import BaseModel, Field, ConfigDict
# BaseModel   : Clase base de Pydantic para definir esquemas de datos.
#               Las clases que heredan de BaseModel validan y parsean
#               automáticamente los datos entrantes (cuerpo JSON del request).
# Field       : Permite añadir metadatos a un campo de Pydantic: valor por
#               defecto, restricciones (gt=0 para "mayor que cero"), ejemplo
#               visible en Swagger, descripción, etc.
# ConfigDict  : Clase de configuración de Pydantic v2. Se usa para activar
#               'from_attributes=True', que permite a Pydantic leer los valores
#               directamente desde atributos de un objeto ORM de SQLAlchemy
#               (en lugar de un diccionario), habilitando la serialización
#               automática ORM → JSON.

from sqlalchemy.orm import Session
# Session     : Tipo de la sesión de SQLAlchemy. Se usa como anotación de tipo
#               en los parámetros de los endpoints para indicar que 'db' es una
#               sesión activa de base de datos. No instancia nada por sí mismo;
#               la instancia real la provee la función get_db() vía Depends.

from typing import Optional
# Optional[X] : Tipo genérico equivalente a 'Union[X, None]'. Indica que un
#               campo o parámetro puede tener el tipo X o ser None. Usado en
#               ResiduoUpdate para campos opcionales en actualizaciones parciales
#               y en el parámetro de filtro del GET /residuos/.

from datetime import date
# date        : Clase de fecha (año, mes, día) del módulo estándar datetime.
#               Pydantic la soporta de forma nativa y la valida/parsea desde
#               cadenas ISO 8601 (formato "YYYY-MM-DD") en el cuerpo JSON.

import models
# Importa el módulo models.py completo. Se accede a sus clases como
# models.ResiduoDB. Esta forma de importar (en lugar de 'from models import...')
# hace explícito el origen del símbolo y evita colisiones de nombres.

from database import engine, get_db
# engine  : El motor de SQLAlchemy creado en database.py. Se usa aquí
#           únicamente para 'Base.metadata.create_all(bind=engine)', la
#           instrucción que crea las tablas al iniciar la app.
# get_db  : Función generadora usada como dependencia inyectable. FastAPI
#           la invoca automáticamente en cada request para suministrar una
#           sesión de base de datos al endpoint correspondiente.


# ==============================================================================
# INICIALIZACIÓN DE TABLAS EN LA BASE DE DATOS
# ==============================================================================

models.Base.metadata.create_all(bind=engine)
# Al arrancar la aplicación (cuando uvicorn carga main.py), esta instrucción
# compara el esquema definido en los modelos ORM (models.py) contra las tablas
# existentes en la base de datos PostgreSQL de Neon.
# - Si la tabla 'residuos' NO existe: la crea ejecutando el DDL (CREATE TABLE).
# - Si la tabla YA existe: no hace nada (comportamiento idempotente, seguro
#   para reinicios de servidor en producción).
# 'bind=engine' indica sobre qué base de datos ejecutar la operación.


# ==============================================================================
# INSTANCIA DE LA APLICACIÓN FASTAPI
# ==============================================================================

app = FastAPI(
    title="API de Gestión de Residuos Reciclables",
    # Nombre del proyecto. Aparece como encabezado en la interfaz Swagger UI
    # (disponible en /docs) y en el esquema OpenAPI generado automáticamente.

    description="API conectada a PostgreSQL (Neon) - Aprendiz: Samuel Mora Vélez",
    # Descripción corta del proyecto y del autor. Visible en /docs debajo del
    # título. Puede incluir Markdown para enriquecer la presentación.

    version="2.0.0"
    # Versión semántica (SemVer) de la API. Ayuda a los consumidores de la API
    # a entender el nivel de madurez y detectar cambios entre versiones.
)


# ==============================================================================
# ESQUEMAS PYDANTIC (CAPA DE VALIDACIÓN Y CONTRATO DE DATOS)
# ==============================================================================

class ResiduoBase(BaseModel):
    """
    Esquema Pydantic base con los campos comunes a varias operaciones.

    Define y valida los atributos descriptivos de un residuo reciclable.
    No incluye el campo 'id' porque este esquema sirve tanto para la creación
    (donde id se gestiona en ResiduoCreate) como base estructural reutilizable.

    Pydantic valida cada campo automáticamente al instanciar el modelo:
    tipos incorrectos, valores None en campos obligatorios o violaciones de
    restricciones (como gt=0) generan una respuesta HTTP 422 automática.

    Atributos:
        tipo_material (str):
            Categoría del residuo (p.ej. "Plástico", "Vidrio", "Metal").
            Obligatorio. El '...' (Ellipsis) como primer argumento de Field
            indica que no tiene valor por defecto y es requerido.

        peso_kg (float):
            Peso del residuo en kilogramos. Obligatorio.
            Restricción: gt=0 (greater than 0) → el valor debe ser
            estrictamente mayor que cero. Pydantic rechazará valores negativos
            o cero con un error de validación 422.

        fecha_recoleccion (date):
            Fecha de recolección. Pydantic parsea automáticamente la cadena
            ISO 8601 "YYYY-MM-DD" del JSON entrante al tipo 'datetime.date'.

        lugar (str):
            Nombre del lugar de recolección. Obligatorio.

        responsable (str):
            Nombre del responsable de la recolección. Obligatorio.
    """

    tipo_material: str = Field(
        ...,
        # Ellipsis (...) indica campo obligatorio sin valor por defecto.
        example="Plástico"
        # Valor de ejemplo mostrado en Swagger UI para facilitar las pruebas.
    )
    peso_kg: float = Field(
        ...,
        # Campo obligatorio.
        gt=0,
        # Restricción: mayor estrictamente que cero. Impide registrar
        # residuos con peso nulo o negativo.
        example=12.5
    )
    fecha_recoleccion: date = Field(
        ...,
        example="2026-11-24"
        # Pydantic acepta este string y lo convierte a datetime.date.
    )
    lugar: str = Field(
        ...,
        example="Centro de Acopio Robledo"
    )
    responsable: str = Field(
        ...,
        example="Samuel Mora Vélez"
    )


class ResiduoCreate(ResiduoBase):
    """
    Esquema de creación de un residuo. Extiende ResiduoBase añadiendo el campo 'id'.

    Se usa como tipo del cuerpo (Body) en el endpoint POST /residuos/.
    El cliente debe proveer el ID manualmente dado que el modelo ORM tiene
    'autoincrement=False'. Esto permite a la organización controlar la
    numeración de registros según su propio sistema de códigos.

    Atributos heredados de ResiduoBase:
        tipo_material, peso_kg, fecha_recoleccion, lugar, responsable.

    Atributos propios:
        id (int):
            Identificador único del residuo. Obligatorio. gt=0: debe ser un
            entero positivo mayor que cero para ser un ID válido.
    """

    id: int = Field(
        ...,
        # Campo obligatorio.
        gt=0,
        # El ID debe ser un entero positivo. Rechaza IDs cero o negativos.
        example=1
    )


class ResiduoUpdate(BaseModel):
    """
    Esquema de actualización parcial (PATCH semántico vía PUT).

    Todos los campos son opcionales (Optional[tipo] = None). Esto permite al
    cliente enviar en el cuerpo del PUT únicamente los campos que desea
    modificar, sin necesidad de repetir los que no cambian.

    La lógica de actualización en el endpoint usa 'model_dump(exclude_unset=True)'
    para obtener solo los campos que el cliente envió explícitamente, evitando
    sobrescribir campos existentes con None cuando no fueron incluidos en el body.

    Atributos (todos opcionales):
        tipo_material (Optional[str]):  Nuevo tipo de material. None = sin cambio.
        peso_kg (Optional[float]):      Nuevo peso. gt=0 si se proporciona.
        fecha_recoleccion (Optional[date]): Nueva fecha. None = sin cambio.
        lugar (Optional[str]):          Nuevo lugar. None = sin cambio.
        responsable (Optional[str]):    Nuevo responsable. None = sin cambio.
    """

    tipo_material: Optional[str] = None
    # Si el cliente no envía 'tipo_material' en el JSON, este campo es None
    # y no se incluirá en los cambios a aplicar.

    peso_kg: Optional[float] = Field(
        None,
        # Valor por defecto None indica que es opcional.
        gt=0
        # Si se proporciona, debe ser mayor que cero. Si es None, la
        # restricción gt=0 no aplica (Pydantic omite la validación para None).
    )

    fecha_recoleccion: Optional[date] = None
    lugar: Optional[str] = None
    responsable: Optional[str] = None


class ResiduoResponse(ResiduoCreate):
    """
    Esquema de respuesta JSON para operaciones que devuelven un residuo completo.

    Hereda todos los campos de ResiduoCreate (id + los cinco campos descriptivos).
    La configuración 'from_attributes=True' (Pydantic v2) es la clave que
    permite serializar un objeto ORM de SQLAlchemy (ResiduoDB) directamente
    a este esquema JSON, leyendo los valores desde los atributos del objeto
    Python en lugar de un diccionario.

    Sin esta configuración, FastAPI no podría convertir un objeto ResiduoDB
    (retornado por SQLAlchemy) en la respuesta JSON esperada.

    Configuración:
        model_config (ConfigDict):
            from_attributes=True → Habilita la compatibilidad ORM-to-Pydantic.
    """

    model_config = ConfigDict(
        from_attributes=True
        # Pydantic v2 reemplaza la clase interna 'Config' por 'model_config'.
        # Este parámetro equivale al antiguo 'orm_mode = True' de Pydantic v1.
        # Permite que Pydantic acceda a 'residuo.id', 'residuo.tipo_material',
        # etc. como atributos de un objeto ORM, no como claves de diccionario.
    )


# ==============================================================================
# ENDPOINT RAÍZ - VERIFICACIÓN DE ESTADO (HEALTH CHECK)
# ==============================================================================

@app.get("/")
def inicio():
    """
    Endpoint de bienvenida y verificación de estado de la API.

    Permite comprobar con una petición GET a la raíz que la aplicación está
    activa y respondiendo. También guía al usuario hacia la documentación
    interactiva.

    Método HTTP:    GET
    Ruta:           /

    Returns:
        dict: Mensaje JSON informativo indicando el estado y la URL de la
              documentación interactiva.
              Ejemplo: {"mensaje": "API de Residuos conectada a Neon. Abre /docs para probar."}
    """
    return {"mensaje": "API de Residuos conectada a Neon. Abre /docs para probar."}


# ==============================================================================
# ACTIVIDAD 1: REGISTRAR RESIDUOS
# ==============================================================================

@app.post(
    "/residuos/",
    response_model=ResiduoResponse,
    # FastAPI usará este esquema para validar y serializar la respuesta.
    # Solo los campos definidos en ResiduoResponse serán incluidos en el JSON
    # de respuesta, ocultando internals del ORM (como '_sa_instance_state').

    status_code=201,
    # HTTP 201 Created: código semánticamente correcto para indicar que un
    # recurso fue creado exitosamente, distinguiéndolo del 200 OK usado en
    # consultas o actualizaciones.

    tags=["Residuos"]
    # Agrupa este endpoint bajo la etiqueta "Residuos" en Swagger UI,
    # mejorando la organización de la documentación interactiva.
)
def registrar_residuo(residuo: ResiduoCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo residuo reciclable en la base de datos.

    Valida que el ID proporcionado no exista previamente para mantener la
    integridad del identificador único. Si el ID ya está en uso, la operación
    es rechazada con un error claro antes de intentar la inserción.

    Método HTTP:    POST
    Ruta:           /residuos/

    Args:
        residuo (ResiduoCreate):
            Cuerpo JSON de la petición, automáticamente parseado y validado
            por Pydantic. Contiene: id, tipo_material, peso_kg,
            fecha_recoleccion, lugar, responsable. FastAPI rechaza
            automáticamente datos inválidos con HTTP 422.
        db (Session):
            Sesión de base de datos inyectada automáticamente por FastAPI
            mediante Depends(get_db). No es un parámetro que el cliente
            deba enviar; es un recurso interno resuelto por el framework.

    Returns:
        ResiduoResponse: El objeto del residuo recién creado, serializado
        a JSON con todos sus campos. Código HTTP 201.

    Raises:
        HTTPException (400 Bad Request):
            Si ya existe un residuo con el mismo ID en la base de datos.
            Mensaje: "Ya existe un residuo con el ID {residuo.id}"
    """

    # --- PASO 1: Validación de ID duplicado ---
    # Antes de intentar insertar, se verifica si ya existe una fila con el
    # mismo ID. Se usa .first() en lugar de .all() porque solo necesitamos
    # saber si existe al menos uno; .first() es más eficiente (añade LIMIT 1
    # a la consulta SQL).
    existe = db.query(models.ResiduoDB).filter(models.ResiduoDB.id == residuo.id).first()

    if existe:
        # Si el ID ya está registrado, se lanza una HTTPException con código
        # 400 (Bad Request). FastAPI convierte esta excepción automáticamente
        # en una respuesta JSON con la estructura {"detail": "mensaje de error"}.
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un residuo con el ID {residuo.id}"
        )

    # --- PASO 2: Creación del objeto ORM ---
    # Se construye una instancia de ResiduoDB a partir de los datos validados
    # por Pydantic. 'residuo.model_dump()' convierte el modelo Pydantic a un
    # diccionario Python (p.ej. {"id": 1, "tipo_material": "Plástico", ...}).
    # El operador ** (unpacking) lo expande como argumentos con nombre para
    # el constructor de ResiduoDB.
    nuevo_residuo = models.ResiduoDB(**residuo.model_dump())

    # --- PASO 3: Agregar al contexto de la sesión ---
    # db.add() registra el objeto 'nuevo_residuo' en la sesión de SQLAlchemy
    # como pendiente de inserción (estado "pending"). Aún NO se ha ejecutado
    # ningún SQL; el objeto existe solo en memoria.
    db.add(nuevo_residuo)

    # --- PASO 4: Confirmar la transacción (persistir en PostgreSQL) ---
    # db.commit() envía la sentencia INSERT INTO residuos (...) VALUES (...)
    # a PostgreSQL y confirma la transacción. Si ocurre un error en este paso
    # (p.ej. violación de restricción NOT NULL), PostgreSQL hace rollback
    # automáticamente y SQLAlchemy propaga la excepción.
    db.commit()

    # --- PASO 5: Refrescar el objeto desde la base de datos ---
    # db.refresh() recarga los atributos del objeto 'nuevo_residuo' desde la
    # base de datos, sincronizando cualquier valor generado por PostgreSQL
    # (como valores DEFAULT o secuencias). Garantiza que el objeto devuelto
    # refleje exactamente el estado persistido en la BD.
    db.refresh(nuevo_residuo)

    # --- PASO 6: Retornar el residuo creado ---
    # FastAPI serializa 'nuevo_residuo' (un objeto ResiduoDB de SQLAlchemy)
    # al esquema JSON definido por ResiduoResponse, gracias al parámetro
    # 'response_model=ResiduoResponse' y a 'from_attributes=True'.
    return nuevo_residuo


# ==============================================================================
# ACTIVIDADES 2 Y 5: CONSULTAR TODOS + FILTRO POR TIPO DE MATERIAL
# ==============================================================================

@app.get("/residuos/", tags=["Residuos"])
def consultar_residuos(
    tipo_material: Optional[str] = Query(
        None,
        # None como valor por defecto hace el parámetro completamente opcional.
        # Si el cliente no lo envía, la URL sería simplemente GET /residuos/.
        description="Filtrar por tipo de material"
        # Descripción visible en Swagger UI junto al campo del parámetro.
    ),
    db: Session = Depends(get_db)
    # Sesión de base de datos inyectada por FastAPI. No visible para el cliente.
):
    """
    Consulta todos los residuos registrados, con filtrado opcional por tipo.

    Combina dos funcionalidades en un mismo endpoint:
    - Sin parámetros: devuelve la lista completa de residuos.
    - Con ?tipo_material=X: filtra con ILIKE (insensible a mayúsculas/minúsculas).

    El uso de ILIKE (en lugar de = o LIKE) permite que el cliente busque
    "plástico", "PLÁSTICO" o "Plástico" y obtenga los mismos resultados,
    mejorando la experiencia de búsqueda.

    Método HTTP:    GET
    Ruta:           /residuos/
    Query Params:   ?tipo_material=<string>  (opcional)

    Args:
        tipo_material (Optional[str]):
            Parámetro de consulta opcional. Si se proporciona, filtra los
            residuos cuyo tipo_material coincida de forma insensible a
            mayúsculas. Acepta el valor exacto del tipo (p.ej. "vidrio").
        db (Session):
            Sesión de base de datos inyectada por Depends(get_db).

    Returns:
        dict: Objeto JSON con dos estructuras posibles:
            - Sin filtro:    {"total": int, "residuos": [ResiduoDB, ...]}
            - Con filtro:    {"total": int, "filtro_aplicado": str,
                              "residuos": [ResiduoDB, ...]}
            El campo "total" indica la cantidad de registros en el resultado.
    """

    # --- PASO 1: Construir la consulta base ---
    # Se inicia una query sobre el modelo ResiduoDB sin ningún filtro aún.
    # En SQL esto equivale a: SELECT * FROM residuos
    # La query no se ejecuta hasta que se llame a .all() o .first().
    consulta = db.query(models.ResiduoDB)

    if tipo_material:
        # --- PASO 2A: Aplicar filtro ILIKE si se recibió el parámetro ---
        # .ilike() genera una cláusula SQL ILIKE (case-insensitive LIKE) en
        # PostgreSQL, que es una extensión SQL no estándar soportada nativamente.
        # 'tipo_material.strip()' elimina espacios en blanco al inicio y al final
        # del string enviado por el cliente, evitando que " Plástico " (con
        # espacios) no encuentre resultados por diferencias de formato.
        # SQL generado: WHERE tipo_material ILIKE 'plástico'
        consulta = consulta.filter(models.ResiduoDB.tipo_material.ilike(tipo_material.strip()))

        # Ejecutar la consulta con filtro y obtener todos los resultados.
        resultados = consulta.all()

        # Retornar respuesta con metadato del filtro aplicado para que el
        # cliente pueda confirmar qué criterio se usó en la búsqueda.
        return {
            "total": len(resultados),
            "filtro_aplicado": tipo_material,
            "residuos": resultados
        }

    # --- PASO 2B: Sin filtro, consultar todos los registros ---
    # Si no se proporcionó tipo_material, se ejecuta la consulta sin cláusula
    # WHERE, devolviendo todos los registros de la tabla.
    # SQL generado: SELECT * FROM residuos
    resultados = consulta.all()

    return {
        "total": len(resultados),
        "residuos": resultados
    }


# ==============================================================================
# ACTIVIDAD 3: CONSULTAR UN RESIDUO POR ID
# ==============================================================================

@app.get(
    "/residuos/{residuo_id}",
    response_model=ResiduoResponse,
    # La respuesta será serializada al esquema ResiduoResponse (con ORM mode).
    tags=["Residuos"]
)
def consultar_residuo_por_id(residuo_id: int, db: Session = Depends(get_db)):
    """
    Consulta y devuelve un único residuo identificado por su ID.

    Realiza una búsqueda exacta por clave primaria. Si no existe un residuo
    con el ID especificado, retorna HTTP 404 con un mensaje descriptivo.

    Método HTTP:    GET
    Ruta:           /residuos/{residuo_id}

    Args:
        residuo_id (int):
            Parámetro de ruta (Path Parameter). FastAPI extrae el valor
            directamente del segmento de la URL (p.ej. /residuos/5 → residuo_id=5)
            y lo convierte automáticamente al tipo declarado (int).
        db (Session):
            Sesión de base de datos inyectada por Depends(get_db).

    Returns:
        ResiduoResponse: Objeto JSON con todos los campos del residuo
        encontrado. Código HTTP 200.

    Raises:
        HTTPException (404 Not Found):
            Si no existe ningún residuo con el ID proporcionado.
            Mensaje: "Residuo con ID {residuo_id} no encontrado"
    """

    # --- Búsqueda por ID en la base de datos ---
    # Se construye una query con filtro exacto sobre la clave primaria.
    # .first() retorna el primer objeto que coincida, o None si no hay coincidencia.
    # SQL generado: SELECT * FROM residuos WHERE id = :residuo_id LIMIT 1
    residuo = db.query(models.ResiduoDB).filter(models.ResiduoDB.id == residuo_id).first()

    if not residuo:
        # Si SQLAlchemy retornó None, el ID no existe en la base de datos.
        # Se lanza HTTPException con código 404 (Not Found), el estándar REST
        # para indicar que el recurso solicitado no fue localizado.
        raise HTTPException(
            status_code=404,
            detail=f"Residuo con ID {residuo_id} no encontrado"
        )

    # Si el residuo existe, se retorna directamente. FastAPI lo serializa
    # a JSON usando el esquema ResiduoResponse gracias a response_model.
    return residuo


# ==============================================================================
# ACTIVIDAD 4: ACTUALIZAR LA INFORMACIÓN DE UN RESIDUO (PUT)
# ==============================================================================

@app.put(
    "/residuos/{residuo_id}",
    response_model=ResiduoResponse,
    # La respuesta será el residuo actualizado serializado a ResiduoResponse.
    tags=["Residuos"]
)
def actualizar_residuo(residuo_id: int, datos: ResiduoUpdate, db: Session = Depends(get_db)):
    """
    Actualiza parcialmente los atributos de un residuo existente.

    Implementa actualización selectiva: solo los campos incluidos en el cuerpo
    JSON de la petición son modificados. Los campos omitidos conservan sus
    valores actuales en la base de datos, evitando sobrescrituras involuntarias.

    Este comportamiento es posible gracias a 'model_dump(exclude_unset=True)'
    de Pydantic, que distingue entre "campo enviado como None" y "campo no
    enviado en absoluto".

    Método HTTP:    PUT
    Ruta:           /residuos/{residuo_id}

    Args:
        residuo_id (int):
            Parámetro de ruta. ID del residuo a actualizar.
        datos (ResiduoUpdate):
            Cuerpo JSON con los campos a modificar. Todos son opcionales.
            Ejemplo de body parcial: {"peso_kg": 15.0, "lugar": "Bodega Sur"}
        db (Session):
            Sesión de base de datos inyectada por Depends(get_db).

    Returns:
        ResiduoResponse: El residuo con sus datos actualizados, serializado
        a JSON. Código HTTP 200.

    Raises:
        HTTPException (404 Not Found):
            Si no existe ningún residuo con el ID proporcionado.
            Mensaje: "Residuo con ID {residuo_id} no encontrado"
    """

    # --- PASO 1: Verificar existencia del recurso a actualizar ---
    # Se busca el residuo por su ID antes de intentar modificarlo.
    # Si no existe, se debe informar al cliente con 404 en lugar de crear
    # un registro nuevo (comportamiento de POST, no de PUT).
    residuo = db.query(models.ResiduoDB).filter(models.ResiduoDB.id == residuo_id).first()

    if not residuo:
        # El recurso a actualizar no fue encontrado. Se retorna 404.
        raise HTTPException(
            status_code=404,
            detail=f"Residuo con ID {residuo_id} no encontrado"
        )

    # --- PASO 2: Extraer solo los campos enviados por el cliente ---
    # 'model_dump(exclude_unset=True)' es la clave de la actualización parcial:
    # retorna únicamente los campos que el cliente incluyó explícitamente en
    # el JSON del request, ignorando los que tienen valor por defecto (None).
    # Ejemplo: si el cliente envió {"peso_kg": 15.0}, cambios = {"peso_kg": 15.0}
    # Los campos tipo_material, lugar, etc., no estarían en el diccionario.
    cambios = datos.model_dump(exclude_unset=True)

    # --- PASO 3: Aplicar los cambios al objeto ORM ---
    # Se itera sobre el diccionario de cambios y se actualiza cada atributo
    # del objeto 'residuo' usando setattr(objeto, nombre_atributo, valor).
    # Este mecanismo dinámico evita escribir una asignación por cada campo
    # posible (residuo.tipo_material = ..., residuo.peso_kg = ..., etc.).
    # SQLAlchemy detecta los cambios en los atributos del objeto y los marca
    # internamente como "dirty" (pendientes de escritura).
    for clave, valor in cambios.items():
        setattr(residuo, clave, valor)

    # --- PASO 4: Confirmar los cambios en PostgreSQL ---
    # db.commit() genera y ejecuta la sentencia SQL UPDATE:
    # UPDATE residuos SET <campo>=<valor>, ... WHERE id = :residuo_id
    # Solo se incluyen en el SET los campos marcados como "dirty".
    db.commit()

    # --- PASO 5: Refrescar el objeto ---
    # Recarga el objeto desde la base de datos para reflejar el estado
    # exacto post-UPDATE, incluyendo cualquier transformación aplicada
    # por PostgreSQL (como triggers o valores DEFAULT calculados).
    db.refresh(residuo)

    # Retornar el objeto actualizado. FastAPI lo serializa a JSON.
    return residuo


# ==============================================================================
# ACTIVIDAD 6: ELIMINAR RESIDUOS (DELETE)
# ==============================================================================

@app.delete("/residuos/{residuo_id}", tags=["Residuos"])
def eliminar_residuo(residuo_id: int, db: Session = Depends(get_db)):
    """
    Elimina de forma permanente un residuo de la base de datos.

    Verifica la existencia del recurso antes de eliminarlo. Si el ID no
    corresponde a ningún registro, informa al cliente con HTTP 404 en lugar
    de reportar un éxito falso.

    Método HTTP:    DELETE
    Ruta:           /residuos/{residuo_id}

    Args:
        residuo_id (int):
            Parámetro de ruta. ID del residuo a eliminar permanentemente.
        db (Session):
            Sesión de base de datos inyectada por Depends(get_db).

    Returns:
        dict: Mensaje JSON de confirmación indicando el ID eliminado.
              Código HTTP 200.
              Ejemplo: {"mensaje": "Residuo con ID 5 eliminado de la base de datos"}

    Raises:
        HTTPException (404 Not Found):
            Si no existe ningún residuo con el ID proporcionado.
            Mensaje: "Residuo con ID {residuo_id} no encontrado"
    """

    # --- PASO 1: Verificar que el recurso existe ---
    # Es una buena práctica verificar la existencia antes de llamar a
    # db.delete(), para retornar un 404 descriptivo en lugar de que
    # SQLAlchemy ignore silenciosamente la operación sobre un objeto inexistente.
    residuo = db.query(models.ResiduoDB).filter(models.ResiduoDB.id == residuo_id).first()

    if not residuo:
        # El residuo a eliminar no existe. Se informa al cliente con 404.
        raise HTTPException(
            status_code=404,
            detail=f"Residuo con ID {residuo_id} no encontrado"
        )

    # --- PASO 2: Marcar el objeto para eliminación ---
    # db.delete() marca el objeto ORM como pendiente de borrado (estado
    # "deleted") dentro de la sesión. Aún no se ha ejecutado ningún SQL.
    db.delete(residuo)

    # --- PASO 3: Confirmar la eliminación en PostgreSQL ---
    # db.commit() ejecuta la sentencia SQL:
    # DELETE FROM residuos WHERE id = :residuo_id
    # y confirma la transacción. La fila es eliminada de forma permanente
    # e irreversible en la base de datos.
    db.commit()

    # --- PASO 4: Retornar confirmación ---
    # Se retorna un mensaje JSON informativo. No se usa HTTP 204 (No Content)
    # para mantener la consistencia con el resto de la API y proveer feedback
    # explícito al cliente sobre qué recurso fue eliminado.
    return {"mensaje": f"Residuo con ID {residuo_id} eliminado de la base de datos"}
