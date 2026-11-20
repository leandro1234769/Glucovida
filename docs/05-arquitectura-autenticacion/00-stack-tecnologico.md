# GlucoVida | Arquitectura tecnológica del backend

**Documento:** Diseño de arquitectura tecnológica.  
**Fase:** Diseño técnico del backend.  
**Versión:** 1.0  
**Estado:** Propuesta arquitectónica para aprobación.  
**Stack principal:** Python + FastAPI + PostgreSQL + Redis.

## 1. Objetivo

Definir la arquitectura tecnológica sobre la que se construirá el backend de GlucoVida, estableciendo los componentes, herramientas, responsabilidades y mecanismos de comunicación necesarios para implementar la plataforma.

La arquitectura deberá permitir:

- Implementar una API REST segura y organizada.
- Gestionar autenticación y sesiones basadas en JWT y Refresh Tokens.
- Aplicar controles de autorización y protección de endpoints.
- Almacenar las mediciones de glucosa y los datos de los usuarios de forma confiable.
- Administrar un catálogo nutricional y un módulo educativo independientes de los registros clínicos.
- Controlar solicitudes automatizadas mediante Rate Limiting.
- Facilitar las pruebas automatizadas, el mantenimiento y la evolución del sistema.

La arquitectura se diseñará considerando que GlucoVida es inicialmente un MVP, por lo que se priorizará una solución modular, mantenible y suficientemente robusta, sin incorporar complejidad innecesaria.

## 2. Selección del stack tecnológico

### 2.1. Lenguaje: Python

**Versión de referencia: Python 3.14.10.**

Python será el lenguaje principal para desarrollar la lógica del backend.

Se selecciona por su integración con FastAPI, la disponibilidad de herramientas para desarrollo web, la facilidad para implementar servicios y su ecosistema de validación, persistencia y pruebas.

Se establece Python 3.14 como versión inicial para favorecer la compatibilidad con las dependencias seleccionadas. El proyecto utilizará una versión exacta del intérprete en el entorno de desarrollo y en los contenedores.

### 2.2. Framework: FastAPI

**Versión de referencia: FastAPI 0.147.x.**

FastAPI será el framework responsable de exponer los servicios de GlucoVida mediante una API REST.

Responsabilidades:

- Definir rutas y endpoints.
- Validar solicitudes y respuestas.
- Gestionar dependencias de autenticación y autorización.
- Integrar middleware y controles de seguridad.
- Documentar automáticamente la API mediante OpenAPI.
- Administrar operaciones asíncronas.
- Conectar los casos de uso con los servicios de aplicación.

FastAPI no concentrará toda la lógica del negocio dentro de los controladores. Los endpoints deberán delegar las operaciones a los servicios o casos de uso correspondientes.

### 2.3. Base de datos: PostgreSQL

**Versión de referencia: PostgreSQL 18.6.**

PostgreSQL será la fuente principal y persistente de información de GlucoVida.

Se utilizará para almacenar:

- Usuarios y perfiles.
- Hashes de contraseñas.
- Sesiones autenticadas.
- Registros de Refresh Tokens y su estado.
- Tokens de recuperación y verificación, almacenados de manera segura.
- Mediciones de glucosa.
- Catálogo de alimentos y valores nutricionales.
- Contenidos educativos y sus fuentes.
- Reportes de inconsistencias.
- Registros de auditoría.

Se selecciona por su soporte de transacciones, restricciones de integridad, índices, tipos de datos y mecanismos de control de concurrencia.

La base de datos será la fuente de verdad del estado de los usuarios y las sesiones. La validez de una sesión no dependerá exclusivamente de Redis ni del contenido de un JWT.

### 2.4. Almacenamiento temporal: Redis

**Versión de referencia: Redis 8.8.x.**

Redis se utilizará para operaciones que requieren contadores, información temporal y acceso rápido.

Responsabilidades:

- Contadores de Rate Limiting por cuenta, sesión e IP.
- Ventanas deslizantes de solicitudes.
- Bloqueos temporales asociados a límites de solicitudes.
- Coordinación de tareas que necesiten exclusión o sincronización temporal.
- Caché selectiva, únicamente cuando exista una necesidad justificada.

Redis no reemplazará PostgreSQL como fuente de verdad de las sesiones. Tampoco almacenará las contraseñas ni los Refresh Tokens originales.

Los datos temporales deberán tener expiraciones controladas mediante TTL y nombres de claves organizados por funcionalidad.

## 3. Arquitectura general: monolito modular

Se utilizará una arquitectura de **monolito modular con separación por capas**.

Esto significa que el backend se desplegará inicialmente como una aplicación principal, pero su código estará separado en módulos funcionales y responsabilidades claramente definidas.

No se implementarán microservicios en esta etapa.

### Justificación

Para el MVP, los módulos comparten usuarios, autenticación, autorización y una misma base de datos. Separarlos en servicios independientes aumentaría la complejidad de despliegue, comunicación entre servicios, administración de secretos y control de transacciones.

La arquitectura modular permitirá evolucionar posteriormente hacia servicios separados si el crecimiento del sistema demuestra que realmente se necesita.

### Módulos funcionales

| Módulo | Responsabilidad |
|---|---|
| `auth` | Inicio de sesión, tokens, renovación, logout y recuperación. |
| `users` | Registro, verificación de correo y gestión de perfil. |
| `glucose` | Registro, consulta, edición, eliminación y estadísticas de mediciones. |
| `nutrition_catalog` | Consulta y administración del catálogo nutricional. |
| `education` | Consulta y administración de contenidos educativos. |
| `reports` | Reportes de inconsistencias del catálogo. |
| `audit` | Registro de eventos y trazabilidad de operaciones. |

Los módulos deberán tener responsabilidades delimitadas y no depender directamente de los detalles internos de otros módulos.

### Separación obligatoria de nutrición y mediciones clínicas

El catálogo nutricional y los registros de glucosa serán componentes independientes.

No se implementarán relaciones, consultas ni servicios que permitan asociar alimentos consultados con mediciones personales de glucosa.

La consulta de un alimento no significará que el usuario lo consumió y no producirá ninguna modificación en sus registros clínicos.

Esta separación deberá reflejarse en el código, los modelos, las consultas y las pruebas de integración.

## 4. Arquitectura por capas

La aplicación estará organizada en cuatro capas principales.

### 4.1. Capa de presentación (API)

Es la puerta de entrada de las solicitudes HTTP.

Responsabilidades:

- Recibir solicitudes.
- Validar datos mediante esquemas.
- Aplicar dependencias de autenticación y autorización.
- Invocar los casos de uso.
- Transformar resultados en respuestas HTTP.
- Gestionar códigos de estado y errores controlados.

Tecnologías:

- FastAPI.
- Pydantic.
- Starlette, como infraestructura utilizada por FastAPI.
- Uvicorn, como servidor ASGI.

Esta capa no debe ejecutar consultas SQL directamente ni contener reglas complejas de negocio.

### 4.2. Capa de aplicación (Application)

Contiene los casos de uso y coordina las operaciones del sistema.

Ejemplos:

- `RegisterUser`
- `LoginUser`
- `RefreshSession`
- `LogoutSession`
- `ChangePassword`
- `RecoverPassword`
- `CreateGlucoseMeasurement`
- `ConsultFoodInformation`

Responsabilidades:

- Ejecutar los flujos definidos en los casos de uso.
- Coordinar repositorios y servicios.
- Gestionar transacciones cuando corresponda.
- Aplicar reglas de autorización relacionadas con cada operación.
- Controlar el resultado de los procesos.

Esta capa no debe depender directamente de FastAPI ni de los modelos ORM de SQLAlchemy.

### 4.3. Capa de dominio (Domain)

Contiene las reglas y conceptos propios de GlucoVida.

Responsabilidades:

- Representar las entidades relevantes.
- Definir reglas de negocio.
- Definir políticas y validaciones independientes de la infraestructura.
- Mantener consistencia con los requisitos funcionales.
- Establecer interfaces o contratos para los servicios externos cuando sea necesario.

Ejemplos:

- Política de duración de sesión.
- Regla de revocación de sesiones.
- Reglas de integridad de mediciones.
- Estados permitidos de los reportes.
- Validaciones del catálogo nutricional.

Las reglas del dominio no deberán depender de FastAPI, PostgreSQL, Redis ni del proveedor de correo.

### 4.4. Capa de infraestructura (Infrastructure)

Implementa los mecanismos técnicos utilizados por las demás capas.

Responsabilidades:

- Conexiones a PostgreSQL.
- Configuración de SQLAlchemy.
- Implementación de repositorios.
- Conexión a Redis.
- Gestión de tokens JWT.
- Generación y verificación de Refresh Tokens.
- Hash de contraseñas.
- Comunicación con proveedores de correo.
- Persistencia de auditoría.

Las tecnologías concretas se utilizarán aquí, detrás de interfaces definidas para la aplicación.

## 5. Flujo general de una solicitud

Una solicitud seguirá esta secuencia:

```text
            CLIENTE WEB
                 |
                 v
          Solicitud HTTP
                 |
                 v
        FASTAPI / API REST
                 |
                 v
      Middleware y dependencias
                 |
                 v
     Autenticación y autorización
                 |
                 v
          CASO DE USO
                 |
                 v
         CAPA DE DOMINIO
                 |
                 v
       Repositorio / Servicios
                 |
           +-----+-----+
           |           |
           v           v
      PostgreSQL     Redis
           |           |
           +-----+-----+
                 |
                 v
          Resultado
                 |
                 v
          Respuesta HTTP
```

Redis se utilizará solo en los flujos que requieran sus capacidades temporales. No todas las solicitudes deberán consultar simultáneamente PostgreSQL y Redis.

## 6. Tecnologías complementarias

### 6.1. Persistencia y acceso a datos

**SQLAlchemy 2.1.x**

Será el ORM principal para interactuar con PostgreSQL.

Responsabilidades:

- Definir modelos de persistencia.
- Ejecutar consultas.
- Gestionar transacciones.
- Implementar repositorios.
- Controlar sesiones de base de datos.

Se utilizará su API asíncrona mediante `AsyncSession`.

**Psycopg 3.x**

Será el controlador de PostgreSQL.

Se utilizará la integración con SQLAlchemy para realizar operaciones asíncronas.

**Alembic 1.x**

Se empleará para administrar las migraciones del esquema de la base de datos.

Las modificaciones de tablas y restricciones se realizarán mediante migraciones versionadas. No se utilizará la creación automática de tablas como mecanismo de actualización de producción.

### 6.2. Validación y configuración

**Pydantic 2.x**

Se utilizará para definir y validar los modelos de entrada y salida de la API.

**Pydantic Settings 2.x**

Se utilizará para cargar y validar la configuración de la aplicación desde variables de entorno.

Los valores sensibles no estarán escritos directamente en los archivos fuente.

### 6.3. Conexión con Redis

**redis-py 8.1.x o una versión estable compatible.**

Se utilizará su cliente asíncrono para comunicarse con Redis.

El Rate Limiting se implementará mediante operaciones atómicas, scripts Lua o mecanismos equivalentes que impidan inconsistencias cuando lleguen solicitudes concurrentes.

### 6.4. Servidor de aplicación

**Uvicorn**

Ejecutará FastAPI mediante ASGI.

En producción se ubicará detrás de un proxy inverso o balanceador que gestione el tráfico HTTPS, los encabezados de seguridad y los límites de conexión.

### 6.5. Pruebas automatizadas

Se utilizarán inicialmente:

| Herramienta | Propósito |
|---|---|
| Pytest | Pruebas unitarias e integración. |
| HTTPX | Solicitudes de prueba contra la API. |
| Pytest-asyncio | Pruebas de código asíncrono. |
| Ruff | Formato y análisis estático básico del código. |
| Mypy o Pyright | Verificación de tipos. |
| OWASP ZAP | Pruebas de seguridad de la API y aplicación web. |

Las dependencias deberán fijarse mediante un archivo de bloqueo para que los ambientes de desarrollo, pruebas y producción utilicen versiones reproducibles.

## 7. Organización de directorios del backend

Se propone la siguiente estructura inicial:

```text
glucovida-backend/
│
├── app/
│   │
│   ├── main.py
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── glucose.py
│   │       ├── nutrition.py
│   │       ├── education.py
│   │       └── reports.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   │
│   ├── domain/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── glucose/
│   │   ├── nutrition/
│   │   ├── education/
│   │   └── reports/
│   │
│   ├── application/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── glucose/
│   │   ├── nutrition/
│   │   ├── education/
│   │   └── reports/
│   │
│   ├── infrastructure/
│   │   ├── database/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   ├── models/
│   │   │   └── repositories/
│   │   │
│   │   ├── redis/
│   │   │   ├── client.py
│   │   │   └── rate_limiter.py
│   │   │
│   │   ├── security/
│   │   │   ├── jwt_service.py
│   │   │   ├── refresh_token.py
│   │   │   └── password_hasher.py
│   │   │
│   │   └── email/
│   │       └── email_service.py
│   │
│   └── schemas/
│       ├── auth.py
│       ├── users.py
│       ├── glucose.py
│       ├── nutrition.py
│       └── education.py
│
├── migrations/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   └── e2e/
│
├── scripts/
│
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
├── alembic.ini
├── Dockerfile
├── compose.yaml
└── README.md
```

La estructura es una propuesta inicial. Al desarrollar cada módulo se podrán crear subdirectorios de casos de uso, repositorios y esquemas cuando su complejidad lo justifique.

No es necesario crear archivos vacíos para todos los elementos desde el primer día. Se irán incorporando a medida que se implemente cada funcionalidad.

## 8. Diseño de comunicación entre PostgreSQL y Redis

Se mantendrán responsabilidades separadas.

### 8.1. PostgreSQL: información persistente

PostgreSQL será responsable de:

- Identidad y estado de los usuarios.
- Hashes de contraseñas.
- Estado de las sesiones.
- Historial de Refresh Tokens y revocaciones.
- Mediciones de glucosa.
- Datos del catálogo nutricional.
- Contenido educativo.
- Reportes y auditoría.

Las operaciones críticas, como el cambio de contraseña y la revocación global, deberán realizarse en transacciones consistentes.

La persistencia de una sesión revocada no podrá depender de que Redis esté disponible.

### 8.2. Redis: información temporal

Redis será responsable de:

- Contadores de solicitudes.
- Ventanas deslizantes.
- Límites por cuenta, sesión e IP.
- Bloqueos temporales derivados de los límites de solicitudes.
- Datos temporales con TTL.

No se almacenarán allí las contraseñas ni los Refresh Tokens originales.

### 8.3. Tratamiento de indisponibilidad

Si Redis deja de estar disponible, los endpoints críticos que dependan de sus contadores deberán aplicar la política de fallo cerrado definida para GlucoVida.

No se permitirá que un fallo de Redis convierta el login, la recuperación o la renovación en servicios sin límite de solicitudes.

Se devolverá un error temporal controlado, por ejemplo `503 Service Unavailable`, cuando no sea posible garantizar la política de seguridad.

Como refuerzo, el estado del bloqueo por cinco intentos fallidos de inicio de sesión podrá persistirse en PostgreSQL mediante campos específicos de seguridad, de forma que un reinicio de Redis no elimine un bloqueo todavía vigente.

## 9. Estrategia de acceso a PostgreSQL

Se utilizará una conexión asíncrona mediante SQLAlchemy y Psycopg 3.

Configuración conceptual:

```python
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)

DATABASE_URL = (
    "postgresql+psycopg://usuario@localhost:5432/glucovida"
)

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)
```

Los valores de conexión son ilustrativos. La URL real se construirá mediante configuración segura y variables de entorno.

Reglas:

- Cada solicitud utilizará su propia `AsyncSession`.
- Una sesión ORM no será compartida entre solicitudes concurrentes.
- Las transacciones se administrarán explícitamente.
- Los repositorios concentrarán las operaciones de persistencia.
- Las conexiones se cerrarán correctamente al finalizar el ciclo de vida de la aplicación.
- Los tamaños del pool se ajustarán de acuerdo con la concurrencia y los recursos reales.
- Las contraseñas de la base de datos no se incluirán en el repositorio.

Las operaciones de hash bcrypt son computacionalmente costosas y síncronas. Se ejecutarán fuera del hilo principal del event loop, mediante un mecanismo de ejecución en thread pool, para evitar bloquear las demás solicitudes asíncronas.

## 10. Arquitectura de seguridad transversal

La seguridad no será responsabilidad de un único endpoint. Se implementará mediante controles distribuidos en las capas del sistema.

| Área | Mecanismo |
|---|---|
| Autenticación | JWT de corta duración y Refresh Token opaco. |
| Contraseñas | bcrypt con costo 12, conforme a la decisión aprobada. |
| Revocación | Estado de sesión persistente en PostgreSQL. |
| Renovación | Rotación atómica de Refresh Tokens. |
| Autorización | Dependencias y políticas aplicadas en backend. |
| Rate Limiting | Redis con operaciones atómicas. |
| CSRF | Validación de origen y token CSRF. |
| Transporte | HTTPS obligatorio en despliegue. |
| Configuración | Secretos mediante variables de entorno o gestor de secretos. |
| Auditoría | Registro de eventos sin credenciales ni tokens. |
| Migraciones | Alembic con control de versiones. |
| Protección de base de datos | Roles de mínimo privilegio y acceso restringido. |

Las operaciones administrativas de migración utilizarán credenciales diferentes de las utilizadas por la aplicación en tiempo de ejecución. El usuario de base de datos del backend no tendrá permisos generales para modificar el esquema.

## 11. Configuración y gestión de secretos

La configuración se separará del código fuente.

Variables conceptuales:

```env
APP_ENV=development
APP_DEBUG=true
APP_SECRET_KEY=<secreto-de-aplicacion>

DATABASE_URL=<conexion-postgresql>
REDIS_URL=<conexion-redis>

JWT_PRIVATE_KEY=<clave-privada>
JWT_PUBLIC_KEY=<clave-publica>

JWT_ISSUER=<emisor>
JWT_AUDIENCE=<audiencia>

CSRF_HMAC_SECRET=<secreto-csrf>
EMAIL_PROVIDER_API_KEY=<clave-del-proveedor>
```

Estas variables representan nombres de configuración. Los secretos no deben escribirse dentro de archivos versionados ni entregarse al frontend.

Reglas:

- `.env` permanecerá fuera del control de versiones.
- `.env.example` incluirá únicamente nombres de variables y valores de ejemplo no sensibles.
- Producción utilizará un gestor de secretos o mecanismo equivalente.
- Las claves criptográficas tendrán procesos definidos de rotación.
- Se evitará registrar valores completos de configuración en los logs.

## 12. Entorno de desarrollo y despliegue

### 12.1. Desarrollo local

Se utilizará Docker Compose para ejecutar los servicios de infraestructura necesarios:

```text
Desarrollo local
│
├── FastAPI
│   └── Python 3.14
│
├── PostgreSQL 18
│
└── Redis 8
```

El código del backend podrá ejecutarse en el entorno virtual local o dentro de un contenedor, según la configuración del equipo.

### 12.2. Producción

La arquitectura prevista será:

```text
          CLIENTE WEB
               |
               v
        HTTPS / TLS
               |
               v
      Proxy inverso / Gateway
               |
               v
        FASTAPI + UVICORN
               |
       +-------+-------+
       |               |
       v               v
   POSTGRESQL        REDIS
   Persistencia    Contadores
   de datos        temporales
```

Los servicios internos no deberán exponerse directamente a Internet.

PostgreSQL y Redis estarán en una red privada, con acceso restringido al backend y a las herramientas administrativas autorizadas.

La configuración de producción deberá incorporar copias de seguridad, restauración probada, actualizaciones de seguridad, supervisión de disponibilidad y protección del tráfico interno.

## 13. Organización del ciclo de desarrollo

Se propone el siguiente flujo:

1. Crear y configurar el repositorio.
2. Preparar el entorno Python y el gestor de dependencias.
3. Configurar Docker Compose para PostgreSQL y Redis.
4. Inicializar FastAPI.
5. Configurar SQLAlchemy y Alembic.
6. Implementar la conexión asíncrona a PostgreSQL.
7. Implementar el cliente asíncrono de Redis.
8. Configurar pruebas unitarias e integración.
9. Incorporar los módulos de manera progresiva.
10. Automatizar verificaciones mediante integración continua.

No se recomienda comenzar implementando todos los endpoints de manera simultánea. Se debe construir primero la infraestructura base y después desarrollar los casos de uso.

## 14. Decisiones arquitectónicas establecidas

| ID | Decisión | Estado |
|---|---|---|
| ARC-01 | Python como lenguaje del backend | Definida |
| ARC-02 | FastAPI como framework API | Definida |
| ARC-03 | PostgreSQL como base persistente | Definida |
| ARC-04 | Redis como almacenamiento temporal y Rate Limiting | Definida |
| ARC-05 | Monolito modular para el MVP | Propuesta recomendada |
| ARC-06 | Arquitectura por capas | Propuesta recomendada |
| ARC-07 | SQLAlchemy y Psycopg 3 | Propuesta recomendada |
| ARC-08 | Alembic para migraciones | Propuesta recomendada |
| ARC-09 | Operaciones asíncronas para I/O | Propuesta recomendada |
| ARC-10 | Docker Compose para desarrollo | Propuesta recomendada |
| ARC-11 | PostgreSQL como fuente de verdad de sesiones | Definida por arquitectura de autenticación |
| ARC-12 | Separación estricta entre catálogo nutricional y mediciones clínicas | Requisito funcional obligatorio |

## 15. Criterio de aceptación de esta etapa

La arquitectura tecnológica se considerará aprobada cuando:

- Se haya confirmado el stack y las versiones de referencia.
- Estén definidas las responsabilidades de FastAPI, PostgreSQL y Redis.
- Se haya aprobado la organización modular y por capas.
- Se encuentren identificadas las dependencias principales.
- Esté definido el entorno de desarrollo.
- Se hayan establecido las reglas básicas de seguridad, configuración y persistencia.

La aprobación de este diseño no significa que la aplicación esté implementada. Significa que existe una guía técnica sobre la cual construir el backend sin tomar decisiones contradictorias durante el desarrollo.

## 16. Referencias técnicas oficiales

- Python Software Foundation. Documentación y ciclo de versiones de Python. https://devguide.python.org/versions/
- FastAPI. Documentación oficial y notas de versiones. https://fastapi.tiangolo.com/
- PostgreSQL Global Development Group. Versionado y soporte de PostgreSQL. https://www.postgresql.org/support/versioning/
- Psycopg. Documentación oficial del adaptador PostgreSQL para Python. https://www.psycopg.org/
- SQLAlchemy. Documentación oficial del ORM y soporte asíncrono. https://docs.sqlalchemy.org/
- Alembic. Documentación oficial de migraciones. https://alembic.sqlalchemy.org/
- Redis. Documentación oficial. https://redis.io/docs/latest/
- Pytest. Documentación oficial. https://docs.pytest.org/