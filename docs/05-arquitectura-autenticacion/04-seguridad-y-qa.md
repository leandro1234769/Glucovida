# GlucoVida | Plan de pruebas de seguridad y validación QA de autenticación

**Documento técnico 4 de 4**

**Versión:** 1.0  
**Estado:** Plan de pruebas propuesto para ejecución en ambiente de pruebas.  
**Dependencias:** Componentes 1, 2 y 3.  
**Ámbito:** Autenticación, administración de sesiones, expiración de credenciales, recuperación de contraseña y Rate Limiting.

## 1. Objetivo

Definir los escenarios de pruebas funcionales, de integración y de seguridad necesarios para verificar que la arquitectura de autenticación de GlucoVida cumpla los requisitos establecidos.

El plan busca comprobar que:

- Los tokens expiran en los tiempos definidos.
- Las sesiones revocadas dejan de autorizar solicitudes.
- El cierre de sesión afecta únicamente a la sesión correspondiente.
- El cambio o recuperación de contraseña invalida todas las sesiones del usuario.
- Los límites de solicitudes impiden los intentos automatizados excesivos.
- La rotación de Refresh Tokens no permite reutilizar credenciales consumidas.
- Las cookies, cabeceras y mecanismos CSRF se comportan correctamente.
- Los errores no revelan información sensible ni detalles internos.

Este documento establece qué debe probar QA, cómo debe ejecutarlo y cuáles son los resultados esperados. No representa una certificación de seguridad ni afirma que las pruebas ya hayan sido ejecutadas.

## 2. Alcance de las pruebas

Se contemplan cuatro grupos:

| Grupo | Área | Propósito |
|---|---|---|
| A | Expiración | Validar duración de tokens y sesiones. |
| B | Revocación | Comprobar logout y cierre global de sesiones. |
| C | Rate Limiting | Verificar límites frente a intentos automatizados. |
| D | Controles adicionales | Revisar CSRF, cookies, rotación y exposición de información. |

### 2.1. Ambiente de pruebas

Las pruebas deberán ejecutarse inicialmente en un ambiente de QA o staging, independiente de producción.

Este ambiente debe disponer de:

- Backend configurado con las mismas reglas de seguridad que producción.
- Base de datos de pruebas con usuarios ficticios.
- Redis o el mecanismo compartido definido para Rate Limiting.
- Servicio de correo de pruebas o bandeja controlada para recuperación y verificación.
- Certificado HTTPS válido en el entorno expuesto al navegador.
- Registro de eventos de autenticación y auditoría.
- Herramienta para controlar o simular el tiempo del servidor.
- Al menos dos instancias de backend cuando se validen contadores distribuidos.

No se utilizarán cuentas reales ni mediciones clínicas de usuarios. Las pruebas de carga y solicitudes automatizadas se realizarán exclusivamente en infraestructura autorizada.

## 3. Datos y condiciones de prueba

Antes de ejecutar los escenarios se prepararán los siguientes datos:

| Identificador | Descripción |
|---|---|
| QA_USER_01 | Usuario activo y con correo verificado. |
| QA_USER_02 | Usuario activo para probar sesiones simultáneas. |
| QA_USER_03 | Usuario con credenciales válidas para recuperación. |
| QA_USER_PENDING | Usuario registrado sin verificación de correo. |
| QA_SESSION_A | Primera sesión del mismo usuario. |
| QA_SESSION_B | Segunda sesión del mismo usuario desde otro navegador o dispositivo. |
| QA_IP_A | Dirección IP de pruebas autorizada. |
| QA_IP_B | Segunda dirección IP controlada. |

También se utilizarán contraseñas ficticias, tokens generados por el entorno de pruebas y correos no pertenecientes a usuarios reales.

### 3.1. Control del tiempo

No es recomendable esperar 15 minutos, 30 minutos o 24 horas durante cada ejecución de pruebas.

Se implementará un reloj controlable en el entorno de pruebas (*controllable clock* o *time provider*). Esto permitirá avanzar el tiempo de forma determinista y comprobar las fronteras exactas de expiración.

El mecanismo no debe modificar directamente los relojes de las máquinas de producción ni permitir que un usuario pueda alterar la hora de validación desde el frontend.

## 4. Pruebas de expiración de tokens y sesiones

### QA-AUTH-01. Expiración del Access Token

<badge color="danger">Crítica</badge>

**Objetivo:** verificar que un Access Token deje de ser aceptado después de 15 minutos.

**Precondiciones:**
- Usuario autenticado.
- Sesión activa.
- Access Token emitido con una duración de 900 segundos.

**Procedimiento:**

1. Autenticar al usuario.
2. Guardar el Access Token emitido en el entorno de QA.
3. Realizar una solicitud protegida antes de la expiración.
4. Avanzar el reloj de pruebas hasta un segundo antes de `exp`.
5. Repetir la solicitud.
6. Avanzar el reloj hasta el instante exacto de expiración.
7. Repetir nuevamente la solicitud.

**Resultados esperados:**

| Momento | Resultado |
|---|---|
| Antes de `exp` | Solicitud aceptada si la sesión continúa activa. |
| Un segundo antes de `exp` | Solicitud aceptada si la sesión continúa activa. |
| En `exp` | `401 Unauthorized`. |
| Después de `exp` | `401 Unauthorized`. |

**Criterio de aprobación:** el backend no acepta un token cuando `hora_actual >= exp`.

### QA-AUTH-02. Renovación correcta del Access Token

**Objetivo:** verificar que un Refresh Token vigente pueda obtener un nuevo Access Token.

**Procedimiento:**

1. Iniciar sesión.
2. Esperar o simular la expiración del Access Token.
3. Enviar una solicitud al endpoint `/api/v1/auth/refresh`.
4. Adjuntar la cookie Refresh Token y la protección CSRF correspondiente.
5. Revisar la respuesta y la nueva cookie.

**Resultado esperado:**

- Código `200 OK`.
- Nuevo Access Token con `expires_in = 900`.
- Emisión de un nuevo Refresh Token.
- Consumo del token anterior.
- La fecha absoluta de expiración de la sesión permanece intacta.

**Criterio de aprobación:** el nuevo Access Token permite realizar solicitudes protegidas sin extender el límite absoluto de la sesión.

### QA-AUTH-03. Expiración por inactividad

<badge color="danger">Crítica</badge>

**Objetivo:** verificar la invalidación de una sesión después de 30 minutos sin actividad autenticada válida.

**Procedimiento:**

1. Iniciar sesión.
2. Realizar una solicitud protegida que actualice `last_activity_at`.
3. Registrar el instante de última actividad válida.
4. Simular el paso del tiempo hasta 29 minutos y 59 segundos.
5. Realizar una solicitud protegida.
6. En una sesión de prueba nueva, dejar transcurrir exactamente 30 minutos sin actividad.
7. Intentar utilizar el Access Token y el Refresh Token.

**Resultados esperados:**

- Antes del límite, la sesión puede continuar si no ha alcanzado otra condición de expiración.
- Al alcanzar los 30 minutos de inactividad, la sesión deja de autorizar solicitudes.
- El Refresh Token es rechazado.
- Los siguientes intentos de renovación devuelven `401 Unauthorized`.

**Validación adicional:** realizar únicamente solicitudes automáticas de renovación y comprobar que estas no actualizan por sí solas `last_activity_at`.

**Criterio de aprobación:** una sesión inactiva durante 30 minutos no puede mantenerse abierta mediante renovaciones automáticas.

### QA-AUTH-04. Expiración absoluta de sesión

<badge color="danger">Crítica</badge>

**Objetivo:** comprobar que una sesión no pueda durar más de 24 horas desde su creación.

**Procedimiento:**

1. Crear una sesión en el instante T0.
2. Renovar Access Tokens durante el periodo de pruebas.
3. Comprobar que el sistema conserva la fecha absoluta original.
4. Avanzar el reloj hasta un segundo antes de cumplir 24 horas.
5. Intentar renovar.
6. Avanzar el reloj hasta cumplir las 24 horas.
7. Intentar nuevamente renovar y utilizar los tokens anteriores.

**Resultados esperados:**

- Antes del límite absoluto, la renovación puede funcionar si las demás condiciones se cumplen.
- En el instante de las 24 horas, la sesión queda expirada.
- El Refresh Token deja de ser válido.
- Los Access Tokens asociados dejan de autorizar solicitudes.
- Se requiere un nuevo inicio de sesión.

**Criterio de aprobación:** ninguna renovación puede extender la sesión más allá de sus 24 horas desde T0.

## 5. Pruebas de revocación de sesiones

### QA-AUTH-05. Revocación individual al cerrar sesión

<badge color="danger">Crítica</badge>

**Objetivo:** verificar que seleccionar «Cerrar sesión» invalide la sesión actual sin afectar otras sesiones del mismo usuario.

**Precondiciones:**
- Un mismo usuario autenticado desde dos navegadores o dispositivos.
- Sesión A y sesión B activas.
- Cada sesión dispone de su propio Access Token y Refresh Token.

**Procedimiento:**

1. Iniciar sesión en el dispositivo A.
2. Iniciar sesión en el dispositivo B con la misma cuenta.
3. Realizar una solicitud protegida desde A y B.
4. Ejecutar `POST /api/v1/auth/logout` desde A.
5. Comprobar el estado de la sesión A en el backend.
6. Intentar utilizar el Access Token anterior de A.
7. Intentar renovar utilizando el Refresh Token anterior de A.
8. Repetir las solicitudes desde B.

**Resultados esperados:**

| Acción | Resultado |
|---|---|
| Logout de A | `204 No Content`. |
| Access Token de A | Rechazado con `401`. |
| Refresh Token de A | Rechazado con `401`. |
| Access Token de B | Continúa funcionando. |
| Refresh Token de B | Continúa funcionando si la sesión sigue vigente. |
| Cookie de A | Eliminada en el navegador A. |

**Criterio de aprobación:** la revocación afecta únicamente a la sesión A. La sesión B permanece activa.

### QA-AUTH-06. Invalidación global después del cambio de contraseña

<badge color="danger">Crítica</badge>

**Objetivo:** verificar que cambiar la contraseña invalide todas las sesiones del usuario.

**Precondiciones:**
- Usuario activo.
- Dos sesiones autenticadas en dispositivos diferentes.
- Contraseña actual conocida para el usuario de prueba.

**Procedimiento:**

1. Iniciar sesión en el dispositivo A.
2. Iniciar sesión en el dispositivo B.
3. Verificar que ambas sesiones funcionen.
4. Desde A, ejecutar `PATCH /api/v1/me/password`.
5. Enviar la contraseña actual y una nueva contraseña válida.
6. Esperar el resultado exitoso de la operación.
7. Intentar utilizar el Access Token de A.
8. Intentar utilizar el Access Token de B.
9. Intentar renovar las dos sesiones.
10. Intentar iniciar sesión con la contraseña anterior.
11. Intentar iniciar sesión con la nueva contraseña.

**Resultados esperados:**

- El cambio devuelve `204 No Content`.
- `auth_version` aumenta.
- Todas las sesiones anteriores quedan revocadas.
- Los Refresh Tokens anteriores quedan invalidados.
- Los Access Tokens anteriores devuelven `401`.
- La contraseña anterior deja de funcionar.
- La nueva contraseña permite iniciar sesión y crear una sesión nueva.

**Criterio de aprobación:** ninguna sesión previa puede continuar autorizando operaciones después de confirmarse el cambio de contraseña.

### QA-AUTH-07. Invalidación global después de la recuperación

**Objetivo:** comprobar que recuperar la contraseña mediante CU18 tenga el mismo efecto de invalidación global.

**Procedimiento:**

1. Crear dos sesiones activas del mismo usuario.
2. Solicitar recuperación de contraseña.
3. Obtener el enlace desde el correo de pruebas.
4. Completar la recuperación con una nueva contraseña.
5. Intentar utilizar los Access Tokens de ambas sesiones.
6. Intentar renovar ambos Refresh Tokens.
7. Comprobar que los enlaces de recuperación anteriores ya no puedan utilizarse.

**Resultados esperados:**

- La recuperación termina correctamente.
- Se incrementa la versión de autenticación.
- Todas las sesiones anteriores quedan revocadas.
- Todos los tokens de recuperación pendientes quedan invalidados.
- El enlace utilizado no puede volver a utilizarse.
- El usuario debe iniciar una sesión nueva con la nueva contraseña.

**Criterio de aprobación:** recuperación y cambio de contraseña aplican una invalidación global consistente.

### QA-AUTH-08. Reutilización de un Refresh Token consumido

**Objetivo:** verificar que un Refresh Token anterior no pueda utilizarse nuevamente después de una renovación exitosa.

**Procedimiento:**

1. Iniciar sesión y obtener el Refresh Token R1.
2. Ejecutar una renovación válida.
3. Guardar el nuevo Refresh Token R2.
4. Intentar renovar utilizando nuevamente R1.
5. Comprobar los registros de seguridad y el estado de la sesión.

**Resultado esperado:**

- R1 es rechazado.
- El backend registra la reutilización.
- Se revoca la sesión o familia de tokens correspondiente.
- Se requiere una autenticación nueva.

**Criterio de aprobación:** no es posible utilizar dos veces un Refresh Token consumido para generar credenciales válidas.

## 6. Pruebas de Rate Limiting

Las pruebas deben comprobar tanto la limitación por cuenta como la limitación por IP. Son controles diferentes y no deben sustituirse entre sí.

### QA-RL-01. Fuerza bruta contra inicio de sesión

<badge color="danger">Crítica</badge>

**Objetivo:** comprobar el bloqueo después de cinco intentos fallidos consecutivos por cuenta.

**Procedimiento:**

1. Preparar una cuenta de pruebas.
2. Enviar cuatro solicitudes de login con contraseña incorrecta.
3. Comprobar que todavía no se haya aplicado el bloqueo.
4. Enviar el quinto intento fallido.
5. Intentar iniciar sesión con la contraseña correcta durante el periodo de bloqueo.
6. Avanzar el reloj 14 minutos y 59 segundos.
7. Intentar nuevamente.
8. Avanzar el reloj hasta completar 15 minutos.
9. Intentar el inicio de sesión con la contraseña correcta.

**Resultados esperados:**

| Intento o momento | Resultado |
|---|---|
| Fallos 1 a 4 | Autenticación rechazada. |
| Fallo 5 | Se activa el bloqueo de 15 minutos. |
| Durante el bloqueo | Se rechaza el intento, incluso con la contraseña correcta. |
| Al cumplir los 15 minutos | Se permite un nuevo intento de autenticación. |
| Credenciales correctas después del bloqueo | Login exitoso, si la cuenta cumple las demás condiciones. |

El comportamiento del error no debe permitir identificar si una cuenta existe. La misma política de respuesta genérica se aplicará a identificadores no registrados.

**Criterio de aprobación:** se activa el bloqueo al quinto fallo y se mantiene durante 15 minutos, conforme a CU02.

### QA-RL-02. Límite de solicitudes de login por IP

**Objetivo:** comprobar el límite de 30 solicitudes por IP en una ventana móvil de cinco minutos.

**Procedimiento:**

1. Utilizar una IP de pruebas autorizada.
2. Enviar 30 solicitudes controladas al endpoint de login durante una ventana de cinco minutos.
3. Utilizar cuentas ficticias diferentes para aislar esta prueba del bloqueo por cuenta.
4. Enviar la solicitud número 31 dentro de la misma ventana.
5. Revisar el código HTTP y `Retry-After`.
6. Repetir la prueba desde otra IP controlada.

**Resultados esperados:**

- Las primeras 30 solicitudes no superan el límite de IP.
- La solicitud 31 recibe `429 Too Many Requests`.
- `Retry-After` indica el tiempo restante.
- El límite de la IP A no bloquea automáticamente a la IP B.
- La protección por cuenta continúa funcionando independientemente del cambio de IP.

**Criterio de aprobación:** el límite de solicitudes por IP se aplica sin depender de una sola instancia del backend.

### QA-RL-03. Cambio de contraseña con verificaciones incorrectas

**Objetivo:** comprobar el límite de cinco verificaciones fallidas de la contraseña actual en 15 minutos.

**Procedimiento:**

1. Iniciar sesión con una cuenta válida.
2. Enviar cuatro solicitudes de cambio con contraseña actual incorrecta.
3. Enviar el quinto intento fallido.
4. Intentar una nueva solicitud durante el bloqueo.
5. Avanzar el reloj de pruebas hasta completar 15 minutos.
6. Repetir la operación con las credenciales correctas.

**Resultados esperados:**

- Los primeros cuatro fallos incrementan el contador.
- El quinto activa el bloqueo del endpoint durante 15 minutos.
- Durante el bloqueo, el endpoint rechaza nuevas solicitudes.
- El bloqueo no cierra todas las sesiones ni impide el inicio de sesión.
- Una vez finalizado, la operación puede continuar si las credenciales y reglas son válidas.

**Criterio de aprobación:** se limita el endpoint sin generar un bloqueo general de la cuenta.

### QA-RL-04. Límite de cambio de contraseña por sesión e IP

**Objetivo:** validar los límites adicionales de solicitudes.

Valores que deben probarse:

- 10 solicitudes en 5 minutos por sesión.
- 30 solicitudes en 5 minutos por IP.

**Procedimiento:**

1. Realizar solicitudes controladas dentro de una misma sesión.
2. Superar el décimo intento dentro de la ventana.
3. Repetir utilizando sesiones distintas desde la misma IP.
4. Superar el límite por IP.
5. Verificar `429` y `Retry-After`.

**Resultado esperado:** cada contador se aplica de manera independiente y no puede eludirse utilizando varias sesiones dentro de una IP que ya alcanzó su límite.

### QA-RL-05. Solicitudes de recuperación por cuenta

**Objetivo:** verificar el máximo de tres solicitudes por cuenta dentro de 60 minutos.

**Procedimiento:**

1. Preparar una cuenta ficticia.
2. Enviar tres solicitudes de recuperación dentro de una hora.
3. Comprobar los correos emitidos.
4. Enviar una cuarta solicitud dentro de la misma ventana.
5. Revisar la respuesta y los correos generados.

**Resultados esperados:**

- Se procesan como máximo tres solicitudes por cuenta en la ventana.
- La cuarta no genera un nuevo enlace.
- La respuesta mantiene un mensaje genérico.
- No se revela si la cuenta está registrada.
- El contador se aplica también a identificadores no registrados.

**Criterio de aprobación:** no pueden generarse más de tres enlaces de recuperación por cuenta en la ventana aprobada.

### QA-RL-06. Solicitudes de recuperación por IP

**Objetivo:** comprobar los dos límites por IP del proceso de recuperación.

| Ventana | Máximo |
|---|---:|
| 10 minutos | 5 solicitudes |
| 60 minutos | 20 solicitudes |

**Procedimiento:**

1. Enviar cinco solicitudes desde la misma IP dentro de diez minutos.
2. Enviar una sexta solicitud antes de cerrar la ventana.
3. Comprobar el bloqueo temporal.
4. Repetir en una ventana controlada de 60 minutos para superar el límite de 20 solicitudes.
5. Revisar `429`, `Retry-After` y los registros del servidor.

**Resultado esperado:** una solicitud que supere cualquiera de los límites por IP es rechazada temporalmente.

### QA-RL-07. Renovación masiva de tokens

**Objetivo:** comprobar los límites por sesión e IP del endpoint de renovación.

Límites establecidos:

- Cinco renovaciones por minuto y por sesión.
- Treinta solicitudes por minuto y por IP.

**Procedimiento:**

1. Crear una sesión de pruebas.
2. Ejecutar renovaciones secuenciales controladas, utilizando cada vez el Refresh Token sucesor.
3. Enviar la sexta solicitud dentro de la misma ventana.
4. Repetir en un entorno con múltiples sesiones desde la misma IP para validar el límite por IP.
5. Comprobar los códigos de respuesta y los contadores.

**Resultado esperado:** el servidor limita las solicitudes que exceden la política, sin permitir que múltiples sesiones de una misma IP eludan el límite global por IP.

**Importante:** esta prueba debe utilizar una cadena de tokens rotados correctamente. No debe reutilizar repetidamente el mismo Refresh Token, porque eso activaría la detección de reutilización y confundiría dos controles diferentes.

## 7. Pruebas adicionales de seguridad de API

### QA-SEC-01. Protección CSRF

**Objetivo:** verificar que un tercero no pueda provocar operaciones autenticadas mediante solicitudes falsificadas.

**Procedimiento:**

1. Enviar una solicitud de renovación sin `X-CSRF-Token`.
2. Repetir con un token incorrecto.
3. Repetir con un token correcto, pero con `Origin` no autorizado.
4. Repetir con cookie y cabecera válidas desde el origen autorizado.

**Resultado esperado:**

- Las tres primeras solicitudes son rechazadas.
- La solicitud legítima puede procesarse si cumple las demás validaciones.

### QA-SEC-02. Seguridad de cookies

**Objetivo:** verificar los atributos de las cookies de autenticación.

**Comprobaciones:**

- La cookie Refresh Token se llama `__Host-gv_refresh`.
- Incluye `HttpOnly`.
- Incluye `Secure`.
- Incluye `SameSite=Strict`.
- Incluye `Path=/`.
- No establece el atributo `Domain`.
- La cookie CSRF no lleva `HttpOnly`, pero sí utiliza `Secure` y `SameSite=Strict`.
- La duración de la cookie Refresh Token no supera el tiempo restante de sesión.
- Después del logout y del cambio o recuperación de contraseña se eliminan las cookies correspondientes.

**Criterio de aprobación:** todos los atributos se encuentran presentes y tienen los valores definidos en el componente 3.

### QA-SEC-03. Validación de CORS

**Objetivo:** impedir que orígenes no autorizados realicen solicitudes con acceso a las respuestas de la API.

**Procedimiento:**

1. Solicitar recursos desde el origen oficial.
2. Repetir desde un origen no autorizado.
3. Enviar una solicitud con `Origin` falsificado en un cliente de pruebas.
4. Revisar las respuestas de preflight y las cabeceras CORS.

**Resultado esperado:** únicamente se permiten los orígenes configurados. No se acepta una configuración abierta que combine comodín de origen con credenciales.

### QA-SEC-04. Protección contra exposición de datos

**Objetivo:** comprobar que las credenciales y los datos sensibles no se filtren.

**Revisiones:**

- Access Tokens no aparecen en URL.
- Contraseñas no aparecen en logs.
- Refresh Tokens no aparecen en logs.
- Los tokens de recuperación no se almacenan en texto plano.
- Los hashes de contraseñas no se envían al frontend.
- Las respuestas de autenticación incluyen `Cache-Control: no-store`.
- Los mensajes de error no incluyen trazas internas ni consultas SQL.
- Las respuestas no incluyen datos clínicos o información de perfil que no sea necesaria para autenticar.

**Criterio de aprobación:** no se encuentran credenciales ni secretos en los registros, respuestas o mecanismos de caché inspeccionados.

### QA-SEC-05. Consistencia del almacenamiento de sesiones

**Objetivo:** verificar que los cambios de estado no dejen sesiones parcialmente revocadas.

**Procedimiento:**

1. Ejecutar una renovación de tokens y simular un fallo controlado durante la operación transaccional.
2. Ejecutar un cambio de contraseña y provocar un error controlado antes de confirmar la transacción.
3. Revisar el estado de `users`, `auth_sessions` y `auth_refresh_tokens`.
4. Comprobar que no se emitan credenciales nuevas cuando la operación no se confirmó.

**Resultado esperado:** no quedan combinaciones inconsistentes de contraseña, versión de autenticación, sesiones y Refresh Tokens. La aplicación no informa éxito cuando la operación transaccional falla.

### QA-SEC-06. Rate Limiting entre instancias

**Objetivo:** comprobar que los contadores no se reinicien al cambiar de instancia de backend.

**Procedimiento:**

1. Configurar al menos dos instancias de backend en staging.
2. Enviar parte de las solicitudes a la primera instancia.
3. Enviar el resto a la segunda instancia utilizando la misma IP y cuenta de pruebas.
4. Superar el límite establecido.
5. Consultar los resultados.

**Resultado esperado:** el límite se aplica globalmente mediante el almacén compartido. No es posible duplicar la cantidad permitida utilizando diferentes instancias.

### QA-SEC-07. Indisponibilidad de Redis

**Objetivo:** verificar que una falla del servicio de contadores no desactive silenciosamente las protecciones.

**Procedimiento:**

1. Simular la indisponibilidad de Redis en el ambiente de pruebas.
2. Intentar ejecutar login, recuperación y renovación.
3. Revisar las respuestas.
4. Verificar los registros y alertas técnicas.

**Resultado esperado:** los endpoints críticos aplican una política de fallo cerrado o un mecanismo alternativo de seguridad previamente definido. No permiten solicitudes ilimitadas por no poder consultar los contadores.

La respuesta esperada puede ser `503 Service Unavailable` cuando no se pueda prestar el servicio de autenticación de forma segura.

## 8. Estrategia de automatización QA

Las pruebas deben implementarse en diferentes niveles.

| Nivel | Tipo de pruebas | Qué valida |
|---|---|---|
| Unitarias | Servicios de tokens, expiración y contadores | Reglas individuales y fronteras de tiempo. |
| Integración | API + base de datos + Redis | Persistencia, revocación y operaciones transaccionales. |
| End-to-end | Frontend y backend | Login, renovación, logout y recuperación. |
| Seguridad automatizada | Análisis de API y navegador | Cabeceras, CORS, CSRF y errores. |
| Carga controlada | Solicitudes concurrentes y distribuidas | Rate Limiting y estabilidad. |

Herramientas que pueden utilizarse:

- **Postman o Newman:** validación de contratos y respuestas HTTP.
- **Jest, Vitest, pytest u otra herramienta compatible con el backend:** pruebas unitarias y de integración.
- **OWASP ZAP:** análisis automatizado de seguridad web y API.
- **k6 o JMeter:** pruebas controladas de concurrencia y carga.
- **Redis CLI y consultas de base de datos:** inspección de contadores, registros y estados de sesión.

Las herramientas definitivas dependerán del lenguaje y framework que se adopten para el backend. No es necesario utilizar todas simultáneamente.

## 9. Criterios generales de aprobación

Se considerará aprobado el plan cuando todos los casos críticos hayan obtenido el resultado esperado y las vulnerabilidades encontradas hayan sido corregidas o formalmente gestionadas.

### Condiciones obligatorias de aprobación

1. Ningún Access Token debe autorizar una solicitud después de su expiración.
2. Ninguna sesión revocada debe seguir autorizando solicitudes nuevas.
3. El logout individual no debe revocar sesiones de otros dispositivos.
4. El cambio y la recuperación de contraseña deben invalidar todas las sesiones anteriores.
5. Ningún Refresh Token consumido puede utilizarse nuevamente para renovar la sesión.
6. Los límites por cuenta, sesión e IP deben funcionar de forma independiente y compartida entre instancias.
7. Las solicitudes que superen los límites deben rechazarse de forma controlada.
8. Los controles CSRF y CORS deben impedir las solicitudes de orígenes no autorizados.
9. No deben encontrarse contraseñas ni tokens completos en los registros.
10. Los errores no deben revelar la existencia de cuentas ni detalles internos del backend.

**Regla de liberación:** una prueba crítica fallida impide considerar cerrado el componente de seguridad de autenticación. No se debe compensar una falla de revocación con una expiración corta del token ni una falla de Rate Limiting con una limitación únicamente en el frontend.

## 10. Evidencias que QA debe conservar

Cada ejecución deberá generar evidencias verificables:

- ID de prueba y versión del backend.
- Fecha y hora de ejecución.
- Ambiente utilizado.
- Datos ficticios empleados.
- Solicitud y respuesta HTTP, con secretos ocultos.
- Resultado esperado y resultado obtenido.
- Logs de seguridad relacionados.
- Estado de los registros de sesión cuando corresponda.
- Capturas de pantalla cuando ayuden a demostrar un comportamiento del frontend.
- Clasificación del defecto, si existe.

No se deben adjuntar Access Tokens, Refresh Tokens, contraseñas ni enlaces activos de recuperación en los informes de QA.

## 11. Formato de registro de defectos

Cuando una prueba falle, se documentará con una estructura uniforme:

| Campo | Descripción |
|---|---|
| ID del defecto | Identificador único. |
| Prueba asociada | Código QA-AUTH, QA-RL o QA-SEC. |
| Severidad | Crítica, alta, media o baja. |
| Descripción | Comportamiento observado. |
| Resultado esperado | Comportamiento requerido. |
| Resultado obtenido | Comportamiento real. |
| Pasos de reproducción | Secuencia exacta. |
| Evidencias | Logs, respuestas y capturas sanitizadas. |
| Estado | Abierto, en corrección, pendiente de retest o cerrado. |

Ejemplo:

```text
ID: SEC-001
Prueba: QA-AUTH-05
Severidad: Crítica

Descripción:
El Access Token de una sesión continúa autorizando
solicitudes después de ejecutar logout.

Resultado esperado:
El backend debe rechazar las solicitudes de la
sesión revocada con 401 Unauthorized.

Estado:
Abierto
```

## 12. Resultado esperado

Con este plan, GlucoVida tendrá criterios verificables para evaluar la arquitectura de autenticación antes de su despliegue.

La estrategia combina pruebas de expiración, revocación, fuerza bruta, protección de cookies, solicitudes concurrentes y consistencia del almacenamiento.

**Criterio de cierre:** los cuatro componentes técnicos estarán documentados cuando los contratos de API estén definidos y el plan de pruebas tenga escenarios, resultados esperados y evidencias requeridas. La implementación y la aprobación efectiva de seguridad solo podrán declararse después de ejecutar las pruebas en el entorno correspondiente y corregir los defectos encontrados.

## 13. Referencias técnicas

- OWASP Foundation. *Authentication Cheat Sheet*. https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- OWASP Foundation. *REST Security Cheat Sheet*. https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html
- OWASP Foundation. *Session Management Cheat Sheet*. https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- OWASP Foundation. *Cross-Site Request Forgery Prevention Cheat Sheet*. https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
- OWASP Foundation. *Web Security Testing Guide*. https://owasp.org/www-project-web-security-testing-guide/
- National Institute of Standards and Technology. (2025). *SP 800-63B-4: Digital Identity Guidelines, Authentication and Authenticator Management*. https://pages.nist.gov/800-63-4/sp800-63b.html