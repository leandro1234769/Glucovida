# GlucoVida | Contratos de API y especificación de endpoints de autenticación

**Documento técnico 3 de 4**

**Versión:** 1.0  
**Estado:** Especificación técnica propuesta para implementación.  
**Dependencias:** Componentes 1 y 2: arquitectura de tokens, revocación, expiración y Rate Limiting.  
**Ámbito:** API REST del backend de GlucoVida.

## 1. Objetivo

Definir los contratos de comunicación entre el frontend y el backend para ejecutar los procesos de autenticación, renovación de credenciales, cierre de sesión, cambio de contraseña y recuperación de acceso.

Cada endpoint debe especificar:

- Método HTTP y ruta.
- Requisitos de autenticación y autorización.
- Cabeceras HTTP.
- Estructura de solicitud.
- Estructura de respuesta.
- Cookies involucradas.
- Códigos HTTP y errores esperados.
- Controles de seguridad que deben ejecutarse en el servidor.

La finalidad es que el frontend y el backend implementen un mismo contrato, evitando comportamientos distintos entre módulos y reduciendo los riesgos derivados de validaciones incompletas.

## 2. Convenciones generales de la API

### 2.1. Base de rutas y versión

Se utilizará una versión explícita en las rutas:

```text
/api/v1/
```

Ejemplo:

```text
POST /api/v1/auth/login
```

La versión permite evolucionar los contratos sin introducir cambios incompatibles de forma silenciosa.

### 2.2. Transporte y formato

La API deberá cumplir estas condiciones:

| Elemento | Especificación |
|---|---|
| Protocolo | HTTPS obligatorio |
| Formato de intercambio | JSON |
| Codificación | UTF-8 |
| Métodos | GET, POST, PATCH, según el propósito |
| Identificadores | UUID cuando corresponda |
| Fechas | ISO 8601, preferiblemente UTC en las respuestas |
| Versión | `/api/v1` |
| Caché de respuestas sensibles | Deshabilitada |

Las solicitudes con cuerpo JSON deberán utilizar:

```http
Content-Type: application/json
Accept: application/json
```

El servidor rechazará los tipos de contenido no admitidos en los endpoints que reciben cuerpos de solicitud.

### 2.3. Cabeceras de seguridad

Las siguientes cabeceras se utilizarán conforme al tipo de operación:

| Cabecera | Uso |
|---|---|
| `Authorization: Bearer <access_token>` | Autenticación en endpoints protegidos. |
| `Content-Type: application/json` | Identifica el formato del cuerpo. |
| `Accept: application/json` | Indica el formato de respuesta esperado. |
| `X-CSRF-Token` | Protección CSRF en operaciones realizadas desde el navegador. |
| `Origin` | Verificación del origen de la solicitud. |
| `X-Request-ID` | Identificador de trazabilidad generado o validado por el servidor. |

El backend no confiará en el valor de `X-Request-ID` como prueba de identidad ni de autorización.

### 2.4. Política CSRF

El uso de cookies para transportar el Refresh Token exige protección frente a solicitudes falsificadas entre sitios.

Se implementará una estrategia de doble envío de token (*signed double-submit cookie*) complementada con verificación estricta de origen.

Se utilizará una cookie independiente:

```http
Set-Cookie: __Host-gv_csrf=<token_firmado>;
Path=/;
Secure;
SameSite=Strict;
Max-Age=86400
```

Esta cookie no llevará el atributo `HttpOnly`, porque el frontend necesita obtener el valor para enviarlo en la cabecera `X-CSRF-Token`. No constituye una credencial de autenticación.

El servidor comprobará:

1. Que la cookie CSRF esté presente.
2. Que la cabecera `X-CSRF-Token` coincida con el valor esperado.
3. Que la firma del token sea válida.
4. Que la cabecera `Origin` corresponda al origen autorizado de GlucoVida.
5. Que la solicitud cumpla la política de métodos y tipos de contenido admitidos.

El token CSRF debe generarse mediante valores criptográficamente seguros y una firma HMAC con una clave protegida en el servidor. Se renovará al establecer una nueva sesión y podrá rotarse durante la renovación de credenciales.

Se rechazará una solicitud protegida cuando no pueda comprobarse su origen o su token CSRF.

### 2.5. Configuración CORS

La configuración debe permitir exclusivamente los orígenes de frontend autorizados.

No se permitirá:

```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Credentials: true
```

Cuando frontend y backend se desplieguen en orígenes diferentes, se utilizará una lista explícita de orígenes permitidos, junto con los métodos y cabeceras necesarios.

Ejemplo conceptual:

```http
Access-Control-Allow-Origin: https://app.glucovida.example
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST, PATCH, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type, X-CSRF-Token
Vary: Origin
```

El origen mostrado es ilustrativo. En producción se sustituirá por el dominio real de GlucoVida. Si ambos componentes se alojan bajo el mismo origen, no será necesario habilitar CORS para esta comunicación.

## 3. Estructura de cookies

### 3.1. Cookie del Refresh Token

La cookie de autenticación se denominará:

```text
__Host-gv_refresh
```

Configuración:

| Atributo | Valor |
|---|---|
| Nombre | `__Host-gv_refresh` |
| HttpOnly | Sí |
| Secure | Sí |
| SameSite | Strict |
| Path | `/` |
| Domain | No se establece |
| Max-Age | Tiempo restante de sesión, en segundos |

Ejemplo:

```http
Set-Cookie: __Host-gv_refresh=<refresh_token>;
Path=/;
HttpOnly;
Secure;
SameSite=Strict;
Max-Age=18000
```

El valor `18000` corresponde a cinco horas restantes de sesión en este ejemplo. Nunca debe reiniciar las 24 horas máximas aprobadas.

### 3.2. Eliminación de la cookie

Al cerrar sesión, cambiar la contraseña o completar la recuperación, se deberá eliminar la cookie del navegador:

```http
Set-Cookie: __Host-gv_refresh=;
Path=/;
HttpOnly;
Secure;
SameSite=Strict;
Max-Age=0;
Expires=Thu, 01 Jan 1970 00:00:00 GMT
```

La eliminación debe conservar los mismos atributos relevantes con los que fue creada, especialmente nombre y ruta. La eliminación en el navegador complementa la revocación del servidor, pero no la reemplaza.

## 4. Catálogo de endpoints

Las siguientes rutas constituyen el contrato propuesto para los procesos de autenticación de GlucoVida.

| Método | Endpoint | Caso de uso asociado | Autenticación |
|---|---|---|---|
| GET | `/api/v1/auth/csrf` | Inicialización de protección CSRF | Pública |
| POST | `/api/v1/auth/register` | CU01 Registrarse | Pública |
| POST | `/api/v1/auth/email-verification/confirm` | CU01 Verificación de correo | Pública, con token de verificación |
| POST | `/api/v1/auth/login` | CU02 Iniciar sesión | Pública |
| POST | `/api/v1/auth/refresh` | Renovación de tokens | Cookie Refresh Token |
| POST | `/api/v1/auth/logout` | CU19 Cerrar sesión | Sesión vigente o Refresh Token |
| PATCH | `/api/v1/me/password` | CU03 Gestionar perfil, cambio de contraseña | Access Token |
| POST | `/api/v1/auth/password-recovery` | CU18 Solicitar recuperación | Pública |
| POST | `/api/v1/auth/password-recovery/confirm` | CU18 Confirmar recuperación | Pública, con token de recuperación |

El cambio de contraseña se ubica bajo `/me/password` porque forma parte de la gestión del perfil autenticado en CU03. No se debe confundir con la recuperación de contraseña de CU18, que es un flujo independiente.

## 5. Especificación de endpoints

### 5.1. GET /api/v1/auth/csrf

**Propósito:** inicializar el mecanismo de protección CSRF antes de ejecutar operaciones desde el navegador.

| Elemento | Definición |
|---|---|
| Método | GET |
| Autenticación | No requiere |
| Cuerpo | No requiere |
| Respuesta exitosa | 200 OK |
| Efecto | Emite cookie CSRF y entrega el token al frontend |

Respuesta ilustrativa:

```json
{
  "csrf_token": "<token_csrf_firmado>"
}
```

Cabeceras:

```http
Cache-Control: no-store
Set-Cookie: __Host-gv_csrf=<token_csrf_firmado>; Path=/; Secure; SameSite=Strict; Max-Age=86400
```

El frontend conservará el token para enviarlo en `X-CSRF-Token` en las operaciones protegidas.

El endpoint no crea una sesión autenticada ni emite Access Tokens.

### 5.2. POST /api/v1/auth/register

**Propósito:** registrar una cuenta nueva, de acuerdo con CU01.

| Elemento | Definición |
|---|---|
| Método | POST |
| Autenticación | No requiere |
| Protección adicional | Validación de origen, CSRF y Rate Limiting |
| Respuesta | 202 Accepted |

Solicitud:

```json
{
  "names": "Nombre",
  "surnames": "Apellidos",
  "email": "usuario@example.com",
  "password": "<contraseña>",
  "sensitive_data_authorization": true
}
```

El nombre exacto de la propiedad de autorización deberá corresponder al modelo de consentimiento aprobado para CU01.

Comportamiento:

1. Validar los campos y las reglas de contraseña vigentes.
2. Normalizar el correo electrónico.
3. Verificar las condiciones de registro.
4. Almacenar la contraseña mediante bcrypt con el costo 12 ya definido.
5. Crear la cuenta en estado pendiente de verificación.
6. Generar un token de verificación de uso único.
7. Enviar el correo de verificación.
8. No crear una sesión autenticada antes de completar la verificación.

Respuesta ilustrativa:

```json
{
  "message": "Si el registro puede procesarse, recibirás las instrucciones correspondientes por correo electrónico."
}
```

El mensaje debe evitar revelar si una dirección de correo ya está registrada.

Errores relevantes:

- `400 Bad Request`: estructura o datos inválidos.
- `413 Content Too Large`: cuerpo por encima del límite permitido.
- `415 Unsupported Media Type`: formato no admitido.
- `429 Too Many Requests`: límite de solicitudes superado.
- `500 Internal Server Error`: error no controlado.

### 5.3. POST /api/v1/auth/email-verification/confirm

**Propósito:** confirmar la dirección de correo electrónico y habilitar la cuenta registrada en CU01.

Solicitud:

```json
{
  "token": "<token_de_verificacion>"
}
```

| Elemento | Definición |
|---|---|
| Método | POST |
| Autenticación | No requiere sesión |
| Credencial | Token de verificación de un solo uso |
| Respuesta exitosa | 204 No Content |

El token debe ser aleatorio, tener vigencia limitada, almacenarse de forma segura y consumirse una sola vez.

El backend verificará su correspondencia, vigencia y estado antes de activar la cuenta.

Errores:

- `400 Bad Request`: estructura inválida.
- `401 Unauthorized`: token inválido, expirado o consumido.
- `429 Too Many Requests`: límite de solicitudes superado.

El token no debe incluirse como parámetro de consulta en una URL que pueda quedar almacenada en registros. El enlace de correo puede transportar el valor en el fragmento de URL (`#token=...`) y el frontend enviarlo posteriormente en el cuerpo de esta solicitud.

### 5.4. POST /api/v1/auth/login

**Propósito:** autenticar al usuario y crear una nueva sesión.

Solicitud:

```http
POST /api/v1/auth/login
Content-Type: application/json
Accept: application/json
X-CSRF-Token: <token_csrf>
Origin: https://app.glucovida.example
```

```json
{
  "email": "usuario@example.com",
  "password": "<contraseña>"
}
```

| Elemento | Definición |
|---|---|
| Método | POST |
| Autenticación previa | No requiere |
| Protección | CSRF, verificación de origen y Rate Limiting |
| Respuesta exitosa | 200 OK |

Respuesta:

```json
{
  "access_token": "<jwt>",
  "token_type": "Bearer",
  "expires_in": 900
}
```

En la misma respuesta se establecerán:

- Cookie `__Host-gv_refresh`, con los atributos aprobados.
- Cookie CSRF renovada, cuando corresponda.

El servidor deberá:

1. Normalizar el identificador de cuenta.
2. Consultar los límites por cuenta e IP.
3. Rechazar temporalmente cuentas bloqueadas.
4. Verificar las credenciales mediante comparación segura del hash.
5. Confirmar que la cuenta esté activa y verificada.
6. Crear el registro de sesión.
7. Generar `sid`, `jti` y `auth_version` correspondientes.
8. Emitir el Access Token con 15 minutos de vigencia.
9. Generar el Refresh Token opaco.
10. Almacenar únicamente su hash y metadatos.
11. Emitir la cookie del Refresh Token.

Errores:

| Código | Situación |
|---|---|
| 400 | Solicitud mal formada o datos inválidos. |
| 401 | Credenciales incorrectas o autenticación no válida. |
| 403 | Protección CSRF fallida o cuenta que requiere completar una condición de verificación. |
| 429 | Bloqueo temporal o límite por IP superado. |
| 500 | Error interno. |

Los mensajes de autenticación deben ser genéricos para no revelar si la cuenta existe, si la contraseña es incorrecta o si la cuenta está deshabilitada. La aplicación puede presentar una explicación general y un procedimiento para recuperar el acceso.

### 5.5. POST /api/v1/auth/refresh

**Propósito:** renovar el Access Token utilizando el Refresh Token enviado automáticamente en la cookie.

Solicitud:

```http
POST /api/v1/auth/refresh
Content-Type: application/json
X-CSRF-Token: <token_csrf>
Origin: https://app.glucovida.example
Cookie: __Host-gv_refresh=<refresh_token>
```

El cuerpo estará vacío.

| Elemento | Definición |
|---|---|
| Método | POST |
| Autenticación | Refresh Token en cookie |
| Protección | CSRF, origen y Rate Limiting |
| Respuesta exitosa | 200 OK |

Respuesta:

```json
{
  "access_token": "<nuevo_jwt>",
  "token_type": "Bearer",
  "expires_in": 900
}
```

Además, el backend establecerá un nuevo Refresh Token y actualizará la cookie CSRF cuando corresponda.

El backend deberá ejecutar de forma atómica:

1. Identificar el Refresh Token mediante el hash.
2. Verificar que no esté expirado, consumido o revocado.
3. Verificar que su sesión continúe activa.
4. Comprobar inactividad y expiración absoluta.
5. Comprobar la versión de autenticación del usuario.
6. Consumir el token anterior.
7. Crear su sucesor.
8. Actualizar la relación entre ambos.
9. Emitir el nuevo Access Token y la nueva cookie.

La fecha absoluta de expiración de la sesión no se modifica.

Errores:

- `401 Unauthorized`: token inválido, expirado, revocado, consumido o sesión no vigente.
- `403 Forbidden`: error de CSRF u origen.
- `429 Too Many Requests`: exceso de solicitudes.
- `500 Internal Server Error`: error interno.

Si se detecta reutilización de un Refresh Token consumido, el backend registrará el evento y revocará la sesión o familia de tokens según el mecanismo definido en el componente 1.

El frontend deberá coordinar las renovaciones para que varias solicitudes simultáneas no intenten rotar el mismo token. La implementación recomendada es un mecanismo de renovación única compartida (*single-flight refresh*).

### 5.6. POST /api/v1/auth/logout

**Propósito:** cerrar la sesión actual conforme a CU19.

Solicitud:

```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
X-CSRF-Token: <token_csrf>
Origin: https://app.glucovida.example
Cookie: __Host-gv_refresh=<refresh_token>
```

| Elemento | Definición |
|---|---|
| Método | POST |
| Identificación de sesión | `sid` del Access Token válido o registro identificado por el Refresh Token |
| Protección | CSRF, verificación de origen |
| Respuesta exitosa | 204 No Content |

El backend deberá:

1. Identificar la sesión actual mediante la información de autenticación disponible.
2. Marcar esa sesión como revocada.
3. Revocar sus Refresh Tokens.
4. Registrar el evento de cierre de sesión.
5. Confirmar la operación.
6. Eliminar la cookie del Refresh Token.
7. Eliminar o rotar el estado CSRF del navegador.

La operación no debe revocar las sesiones de otros dispositivos. El cierre ordinario corresponde únicamente a la sesión actual.

La operación debe ser idempotente en cuanto a la limpieza del navegador: repetirla no debe restablecer una sesión ni generar un error que impida eliminar las cookies. Sin embargo, solo podrá revocarse una sesión en el servidor cuando exista una credencial que permita identificarla.

Respuesta:

```http
HTTP/1.1 204 No Content
Set-Cookie: __Host-gv_refresh=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0
```

Después del cierre de sesión, el frontend eliminará el Access Token de memoria.

La eliminación de las cookies no será considerada evidencia suficiente de revocación: el backend debe confirmar el cambio de estado de la sesión.

### 5.7. PATCH /api/v1/me/password

**Propósito:** cambiar la contraseña del usuario autenticado, conforme a CU03.

Solicitud:

```http
PATCH /api/v1/me/password
Authorization: Bearer <access_token>
Content-Type: application/json
X-CSRF-Token: <token_csrf>
Origin: https://app.glucovida.example
```

```json
{
  "current_password": "<contraseña_actual>",
  "new_password": "<nueva_contraseña>"
}
```

| Elemento | Definición |
|---|---|
| Método | PATCH |
| Autenticación | Access Token |
| Protección | Verificación de sesión, origen, controles CSRF y Rate Limiting |
| Respuesta exitosa | 204 No Content |

El backend deberá:

1. Validar el Access Token y su sesión.
2. Aplicar los límites por cuenta, sesión e IP.
3. Verificar la contraseña actual.
4. Validar la nueva contraseña según la política vigente.
5. Generar su hash con bcrypt y costo 12.
6. Actualizar el hash de contraseña.
7. Incrementar `auth_version`.
8. Revocar todas las sesiones activas del usuario.
9. Revocar los Refresh Tokens asociados.
10. Registrar el evento de seguridad.
11. Confirmar la transacción.
12. Eliminar las cookies del navegador que realizó la operación.

Los demás dispositivos deberán recibir `401 Unauthorized` en su siguiente solicitud protegida y deberán autenticarse de nuevo.

Respuesta exitosa:

```http
HTTP/1.1 204 No Content
Set-Cookie: __Host-gv_refresh=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0
```

Errores:

- `400 Bad Request`: formato o datos inválidos.
- `401 Unauthorized`: sesión no válida o contraseña actual incorrecta.
- `403 Forbidden`: protección CSRF fallida.
- `429 Too Many Requests`: límite superado o bloqueo temporal.
- `500 Internal Server Error`: operación fallida.

La respuesta frente a una contraseña actual incorrecta no debe revelar información interna. El control de cinco verificaciones fallidas en 15 minutos y el bloqueo de 15 minutos del endpoint se aplicará conforme al componente 2.

### 5.8. POST /api/v1/auth/password-recovery

**Propósito:** solicitar la recuperación de contraseña conforme a CU18.

Solicitud:

```json
{
  "email": "usuario@example.com"
}
```

| Elemento | Definición |
|---|---|
| Método | POST |
| Autenticación | No requiere |
| Protección | Verificación de origen y Rate Limiting |
| Respuesta | 202 Accepted |

Comportamiento:

1. Validar el formato del correo.
2. Normalizar el identificador.
3. Aplicar límite de tres solicitudes por cuenta en 60 minutos.
4. Aplicar límites por IP.
5. Si procede, generar un token de recuperación de un solo uso.
6. Guardar de forma segura el hash del token.
7. Enviar el enlace de recuperación al correo registrado.

Respuesta genérica:

```json
{
  "message": "Si la cuenta cumple las condiciones para recuperar el acceso, recibirás las instrucciones en el correo correspondiente."
}
```

La misma respuesta general se utilizará para cuentas inexistentes, evitando enumeración de usuarios.

Cuando se alcance el límite por cuenta, el backend no emitirá otro enlace ni revelará el estado de la cuenta. El límite por IP podrá generar `429 Too Many Requests` con `Retry-After`.

Errores:

- `400 Bad Request`: solicitud mal formada.
- `429 Too Many Requests`: límite de IP superado.
- `500 Internal Server Error`: fallo interno controlado.

### 5.9. POST /api/v1/auth/password-recovery/confirm

**Propósito:** establecer una nueva contraseña utilizando el enlace de recuperación de CU18.

Solicitud:

```json
{
  "token": "<token_de_recuperacion>",
  "new_password": "<nueva_contraseña>"
}
```

| Elemento | Definición |
|---|---|
| Método | POST |
| Autenticación | No requiere sesión previa |
| Credencial | Token de recuperación |
| Protección | CSRF, origen y Rate Limiting |
| Respuesta exitosa | 204 No Content |

El backend deberá:

1. Localizar el registro correspondiente al hash del token.
2. Comprobar que no esté consumido, revocado ni expirado.
3. Verificar que no hayan transcurrido 30 minutos desde su emisión.
4. Validar la nueva contraseña.
5. Actualizar el hash de contraseña con bcrypt costo 12.
6. Incrementar `auth_version`.
7. Invalidar todos los tokens de recuperación pendientes.
8. Revocar todas las sesiones activas del usuario.
9. Revocar todos sus Refresh Tokens.
10. Registrar el evento de recuperación.
11. Confirmar la operación y eliminar las cookies del navegador.

La operación debe ser transaccional en lo relacionado con actualización de contraseña, invalidación global y consumo del token.

Errores:

- `400 Bad Request`: cuerpo mal formado o nueva contraseña inválida.
- `401 Unauthorized`: token inválido, expirado, revocado o consumido.
- `403 Forbidden`: protección CSRF fallida.
- `429 Too Many Requests`: límite por IP superado.
- `500 Internal Server Error`: fallo interno.

Un enlace de recuperación no debe activar una cuenta que todavía no haya completado la verificación del correo.

## 6. Contrato estándar de errores

La API utilizará un formato uniforme para los errores.

Ejemplo:

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "No fue posible completar la autenticación.",
    "request_id": "uuid-de-la-solicitud"
  }
}
```

El campo `code` permitirá al frontend identificar el tipo de error sin depender del texto mostrado al usuario.

### 6.1. Códigos HTTP generales

| Código | Uso en GlucoVida |
|---|---|
| 200 OK | Operación exitosa con respuesta JSON. |
| 202 Accepted | Solicitud aceptada para procesamiento, por ejemplo registro o recuperación. |
| 204 No Content | Operación completada sin cuerpo, por ejemplo logout o cambio de contraseña. |
| 400 Bad Request | Datos o estructura incorrectos. |
| 401 Unauthorized | Token inválido, expirado, revocado o autenticación fallida. |
| 403 Forbidden | Solicitud CSRF inválida o acción no permitida. |
| 404 Not Found | Recurso no disponible, cuando corresponda. |
| 409 Conflict | Conflicto de estado que no pueda resolverse con el contrato ordinario. |
| 413 Content Too Large | Cuerpo de solicitud superior al límite. |
| 415 Unsupported Media Type | Tipo de contenido no admitido. |
| 422 Unprocessable Content | Datos sintácticamente válidos, pero semánticamente no procesables, cuando se utilice esta distinción. |
| 429 Too Many Requests | Límite de solicitudes superado. |
| 500 Internal Server Error | Error interno no controlado. |
| 503 Service Unavailable | Dependencia crítica no disponible o servicio temporalmente indisponible. |

El código concreto debe utilizarse de manera consistente. No se devolverán mensajes de excepción, nombres de tablas, rutas internas, consultas SQL ni detalles de infraestructura.

### 6.2. Respuesta 429

Ejemplo:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 900
Cache-Control: no-store
Content-Type: application/json
```

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Se ha superado el límite de solicitudes. Inténtalo nuevamente más tarde.",
    "request_id": "uuid-de-la-solicitud"
  }
}
```

`Retry-After` indicará el tiempo restante de la limitación, en segundos.

## 7. Consideraciones para el frontend

El frontend debe cumplir las siguientes reglas:

1. Mantener el Access Token únicamente en memoria.
2. No guardar tokens de autenticación en `localStorage`, `sessionStorage` ni en IndexedDB.
3. Permitir que el navegador envíe la cookie Refresh Token únicamente a los endpoints correspondientes.
4. Coordinar las renovaciones para evitar solicitudes simultáneas con el mismo Refresh Token.
5. Al recibir un `401`, intentar una renovación controlada solo cuando la sesión todavía pueda ser válida.
6. Si la renovación falla, limpiar el estado autenticado y solicitar un nuevo inicio de sesión.
7. Después del logout, cambio de contraseña o recuperación exitosa, eliminar el Access Token de memoria y redirigir al flujo de autenticación.
8. No repetir automáticamente solicitudes que cambian datos sin una política de idempotencia apropiada.
9. Mostrar mensajes genéricos ante errores de autenticación y recuperación.
10. No guardar contraseñas, tokens ni datos sensibles en registros de consola o herramientas de analítica.

La renovación automática no debe generar actividad artificial que prolongue la sesión por encima de los 30 minutos de inactividad.

## 8. Criterios de aceptación del componente 3

El componente se considerará definido para implementación cuando:

- Los endpoints estén documentados con métodos, rutas y contratos de entrada y salida.
- Los endpoints protegidos validen JWT, sesión y versión de autenticación.
- Los endpoints basados en cookies tengan protección CSRF y verificación de origen.
- Las cookies utilicen los atributos aprobados.
- Los errores se entreguen con un formato uniforme.
- La renovación sea atómica y rote el Refresh Token.
- Logout revoque únicamente la sesión actual.
- El cambio y la recuperación de contraseña invaliden todas las sesiones.
- Los límites definidos en el componente 2 estén aplicados en el backend.
- No se expongan credenciales ni secretos en URL, logs o respuestas.

## 9. Referencias técnicas

- OWASP Foundation. *REST Security Cheat Sheet*. https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html
- OWASP Foundation. *Cross-Site Request Forgery Prevention Cheat Sheet*. https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
- OWASP Foundation. *Authentication Cheat Sheet*. https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- OWASP Foundation. *Session Management Cheat Sheet*. https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- IETF. *RFC 9110: HTTP Semantics*. https://www.rfc-editor.org/rfc/rfc9110.html
- IETF. *RFC 9111: HTTP Caching*. https://www.rfc-editor.org/rfc/rfc9111.html