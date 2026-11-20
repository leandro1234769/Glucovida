# GlucoVida | Arquitectura de autenticación y revocación de tokens

**Documento técnico 1 de 4**

**Componente:** Arquitectura de tokens y revocación de sesiones  
**Versión:** 1.0  
**Estado:** Propuesta técnica base para revisión e implementación del backend  
**Alcance:** Aplicación web con autenticación, gestión de sesiones y protección de datos sensibles.

## 1. Objetivo

Diseñar una arquitectura de autenticación basada en dos tokens que permita:

- Autenticar las solicitudes mediante un *Access Token* JWT de corta duración.
- Mantener la sesión mediante un *Refresh Token* protegido en una cookie `HttpOnly`.
- Revocar inmediatamente una sesión individual cuando el usuario cierre sesión.
- Invalidar todas las sesiones activas de un usuario cuando cambie o recupere su contraseña.
- Detectar el uso repetido de *Refresh Tokens* que ya fueron utilizados o revocados.
- Mantener el control de acceso en el servidor, sin depender exclusivamente del navegador.

La solución debe impedir que una copia de un token continúe autorizando operaciones después de la revocación de su sesión.

## 2. Decisión arquitectónica: doble token

GlucoVida utilizará dos credenciales con funciones diferentes.

| Característica | Access Token | Refresh Token |
|---|---|---|
| Formato | JWT firmado | Cadena aleatoria opaca |
| Función | Autorizar solicitudes a la API | Obtener un nuevo par de tokens |
| Almacenamiento en el navegador | Memoria de la aplicación | Cookie `HttpOnly` |
| Acceso desde JavaScript | Sí, durante su uso en memoria | No |
| Control del servidor | Firma, expiración y estado de la sesión | Hash almacenado, rotación y estado de la sesión |
| Revocación | Mediante comprobación del estado de la sesión y versión de autenticación | Mediante revocación y rotación en el servidor |

**Decisión importante:** el Access Token será un JWT, pero el Refresh Token no necesita ser otro JWT. Para GlucoVida, un valor opaco generado criptográficamente simplifica la revocación, el seguimiento de reutilización y la rotación.

El Refresh Token se generará con un generador criptográfico seguro, con al menos 256 bits de aleatoriedad. La base de datos almacenará su hash, nunca el valor original.

## 3. Emisión y validación del Access Token

### 3.1. Contenido del JWT

El Access Token incluirá únicamente las afirmaciones necesarias para identificar al usuario, la sesión y el periodo de validez.

Ejemplo ilustrativo del payload:

```json
{
  "iss": "https://api.glucovida.example",
  "aud": "glucovida-api",
  "sub": "uuid-del-usuario",
  "sid": "uuid-de-la-sesion",
  "jti": "identificador-unico-del-token",
  "av": 4,
  "iat": 1793200000,
  "exp": 1793200900
}
```

Los valores son ilustrativos y no representan una sesión real.

| Campo | Propósito |
|---|---|
| `iss` | Identifica al emisor autorizado del token. |
| `aud` | Define el servicio al que está destinado. |
| `sub` | Identifica al usuario autenticado. |
| `sid` | Relaciona el token con una sesión registrada en el servidor. |
| `jti` | Identificador único del JWT. |
| `av` | Versión de autenticación del usuario al emitir el token. |
| `iat` | Momento de emisión. |
| `exp` | Momento de expiración. |

No deben incluirse contraseñas, hashes de contraseñas, datos clínicos, mediciones de glucosa ni información nutricional dentro del JWT. Aunque un JWT esté firmado, su payload normalmente no está cifrado.

### 3.2. Firma y validación criptográfica

La implementación debe:

- Utilizar un algoritmo de firma explícitamente permitido, por ejemplo `RS256`.
- Mantener la clave privada de firma en un gestor de secretos o almacenamiento seguro equivalente, nunca en el repositorio del proyecto.
- Verificar la firma antes de confiar en las afirmaciones del token.
- Validar `iss`, `aud`, `exp` y, cuando corresponda, `iat` y `nbf`.
- Rechazar algoritmos no autorizados, tokens malformados y tokens cuyo emisor o audiencia no correspondan.
- Gestionar la rotación de claves sin aceptar firmas creadas con claves retiradas que ya no deban considerarse confiables.

La clave privada no debe enviarse al frontend. Las decisiones de autenticación siempre corresponden al backend.

## 4. Validación de sesión en cada solicitud protegida

Esta es la pieza principal de la arquitectura.

Validar solamente la firma y la expiración del JWT no basta para garantizar una revocación inmediata. Por tanto, GlucoVida consultará el estado actual de la sesión en el servidor para cada solicitud protegida.

### Secuencia de validación

1. El cliente envía el Access Token mediante la cabecera `Authorization: Bearer`.
2. El backend valida la firma y las afirmaciones del JWT.
3. Extrae `sub`, `sid` y `av`.
4. Consulta el estado de la sesión identificada por `sid`.
5. Comprueba que la sesión pertenezca al usuario del token, que no esté revocada, que no haya expirado y que no haya superado el límite de inactividad.
6. Comprueba que `av` coincida con la versión de autenticación vigente del usuario.
7. Autoriza la solicitud solamente si todas las comprobaciones son satisfactorias.

Esquema lógico:

```text
Solicitud protegida
        |
        v
¿JWT válido y firmado correctamente?
        | No
        +----------------------> 401 Unauthorized
        |
       Sí
        |
        v
Consultar sesión y usuario en servidor
        |
        v
¿Sesión activa, vigente y perteneciente al usuario?
        | No
        +----------------------> 401 Unauthorized
        |
       Sí
        |
        v
¿Versión de autenticación vigente?
        | No
        +----------------------> 401 Unauthorized
        |
       Sí
        |
        v
Autorizar solicitud
```

### Decisión para el MVP

La base de datos será la fuente de verdad para el estado de las sesiones. La comprobación no debe depender de una copia en caché que pueda conservar un estado de sesión activo después de la revocación.

Si en el futuro se incorpora Redis para acelerar las consultas, se deberá diseñar una estrategia de invalidación consistente. Si el sistema no puede verificar de forma confiable el estado de la sesión, debe fallar de forma cerrada y no aceptar el token únicamente porque su firma sea válida.

Esta comprobación en cada solicitud permite que el servidor rechace un Access Token todavía vigente cuando su sesión ya haya sido revocada.

## 5. Modelo de datos propuesto

Se recomienda separar la cuenta del usuario, sus sesiones y los Refresh Tokens emitidos.

### 5.1. Tabla `users`

Campos relacionados con la autenticación:

| Campo | Tipo orientativo | Función |
|---|---|---|
| `id` | UUID | Identificador del usuario. |
| `password_hash` | Texto | Hash de la contraseña. |
| `auth_version` | Entero | Versión global de autenticación. |
| `account_status` | Enum o texto controlado | Estado de la cuenta. |
| `password_changed_at` | Fecha y hora | Último cambio de contraseña. |

`auth_version` comienza, por ejemplo, en `1`. Su valor debe incrementarse ante un cambio o recuperación exitosa de contraseña, entre otros eventos de seguridad que requieran invalidación global.

### 5.2. Tabla `auth_sessions`

Representa una sesión autenticada en un navegador o dispositivo.

| Campo | Tipo orientativo | Función |
|---|---|---|
| `id` | UUID | Identificador de la sesión, utilizado como `sid`. |
| `user_id` | UUID | Usuario propietario de la sesión. |
| `created_at` | Fecha y hora | Creación de la sesión. |
| `last_activity_at` | Fecha y hora | Última actividad válida registrada. |
| `absolute_expires_at` | Fecha y hora | Límite absoluto de la sesión. |
| `auth_version_at_creation` | Entero | Versión de autenticación al crear la sesión. |
| `revoked_at` | Fecha y hora, nullable | Momento de revocación. |
| `revoke_reason` | Enum o texto controlado, nullable | Motivo de revocación. |

La expiración por inactividad se calculará con la última actividad registrada y la política aprobada para la sesión. El servidor debe aplicar tanto ese límite como la expiración absoluta.

### 5.3. Tabla `auth_refresh_tokens`

Mantiene el estado de cada Refresh Token emitido y permite detectar reutilizaciones.

| Campo | Tipo orientativo | Función |
|---|---|---|
| `id` | UUID | Identificador del registro. |
| `session_id` | UUID | Sesión a la que pertenece. |
| `token_hash` | Texto único | Hash del token emitido. |
| `issued_at` | Fecha y hora | Fecha de emisión. |
| `expires_at` | Fecha y hora | Expiración del token. |
| `consumed_at` | Fecha y hora, nullable | Momento en que fue utilizado para renovar. |
| `replaced_by` | UUID, nullable | Token sucesor, si existe. |
| `revoked_at` | Fecha y hora, nullable | Momento de revocación. |

Los registros consumidos no deben eliminarse de inmediato, porque se necesitan para detectar la reutilización de un token antiguo. Su conservación y depuración deben definirse con una política de retención.

### 5.4. Registro de eventos de seguridad

Se recomienda una tabla o mecanismo equivalente de auditoría para registrar eventos como:

- Inicio y cierre de sesión.
- Cambio y recuperación de contraseña.
- Revocación global de sesiones.
- Detección de reutilización de Refresh Tokens.
- Bloqueos o eventos relevantes de autenticación.

La auditoría no debe guardar contraseñas, tokens completos, cookies ni otros secretos. Para este MVP, conviene registrar los identificadores necesarios para investigar eventos sin acumular datos personales innecesarios.

## 6. Estrategia de revocación

Se emplearán dos mecanismos complementarios:

1. **Revocación por sesión:** modifica el estado del registro de `auth_sessions`.
2. **Invalidación global por usuario:** incrementa `auth_version` y revoca todas sus sesiones activas.

La combinación permite revocar una sola sesión o todas las sesiones de la cuenta sin depender de una lista negra independiente para cada JWT emitido.

### 6.1. Cierre de sesión individual

Cuando el usuario selecciona «Cerrar sesión»:

1. El backend identifica la sesión mediante el contexto autenticado y, cuando sea necesario, el Refresh Token recibido en la cookie.
2. Revoca el registro correspondiente a esa sesión.
3. Revoca sus Refresh Tokens todavía utilizables.
4. Confirma la operación de persistencia.
5. Envía una instrucción para eliminar la cookie del navegador.
6. El frontend elimina el Access Token de la memoria de la aplicación.

A partir de la confirmación de la revocación, las nuevas solicitudes que presenten Access Tokens de esa sesión deben ser rechazadas, aunque todavía no hayan alcanzado su fecha `exp`.

**Alcance:** el cierre de sesión ordinario revoca únicamente la sesión actual. Las sesiones de otros dispositivos permanecen activas. Si GlucoVida necesita una función «Cerrar sesión en todos los dispositivos», deberá definirse como una operación diferenciada.

### 6.2. Cambio de contraseña

Después de verificar correctamente la contraseña actual, cuando el flujo de cambio de contraseña lo requiera, y validar la nueva contraseña, el backend ejecutará una operación transaccional:

1. Actualizar `password_hash`.
2. Incrementar `users.auth_version`.
3. Revocar todas las sesiones activas del usuario.
4. Revocar todos sus Refresh Tokens todavía utilizables.
5. Registrar el evento de seguridad.
6. Confirmar la transacción.

Si cualquier paso indispensable falla, no se debe informar que el cambio fue completado mientras la actualización y la revocación no se hayan confirmado de forma consistente.

Los JWT anteriores tendrán una versión `av` que ya no coincide con la del usuario, y sus sesiones también estarán revocadas. Por tanto, dejarán de autorizar nuevas solicitudes.

### 6.3. Recuperación de contraseña

Tras completar satisfactoriamente la recuperación, se aplicará la misma invalidación global:

- Se actualiza el hash de contraseña.
- Se incrementa `auth_version`.
- Se revocan todas las sesiones activas.
- Se invalidan todos los Refresh Tokens vigentes.
- Se registra el evento de seguridad.

La recuperación no debe activar cuentas que todavía no hayan completado la verificación requerida del correo electrónico.

## 7. Rotación y reutilización de Refresh Tokens

Cada vez que se utilice un Refresh Token para renovar la autenticación, el servidor debe emitir un token nuevo e invalidar el anterior.

### Flujo de renovación

```text
Cliente envía cookie de Refresh Token
                  |
                  v
Validar origen y protección CSRF
                  |
                  v
Buscar el hash del token
                  |
                  v
Comprobar token y sesión
                  |
          +-------+--------+
          |                |
       Inválido          Válido
          |                |
          v                v
    Rechazar      Transacción atómica:
                   consumir token anterior
                   crear token sucesor
                   conservar relación
                   emitir Access Token
                   renovar cookie
```

El consumo del token anterior y la creación del sucesor deben realizarse de forma atómica. Dos solicitudes simultáneas no pueden utilizar el mismo token para crear renovaciones independientes.

### Detección de reutilización

Si se presenta un Refresh Token que ya fue consumido o revocado:

1. El backend registra el evento.
2. Revoca la familia de tokens correspondiente y la sesión afectada.
3. Rechaza la renovación.
4. Exige una nueva autenticación.

Esta política sigue el enfoque de rotación con detección de reutilización descrito en el RFC 9700. Para evitar falsos positivos por solicitudes legítimas simultáneas, el frontend deberá coordinar las renovaciones y evitar lanzar varias al mismo tiempo.

## 8. Almacenamiento en el navegador

### Access Token

El Access Token se mantendrá en memoria mientras la aplicación lo necesite. No se almacenará en `localStorage` ni en `sessionStorage`.

El frontend lo enviará en la cabecera:

```http
Authorization: Bearer <access_token>
```

El almacenamiento en memoria reduce la persistencia del token, aunque no elimina el riesgo de que un ataque XSS activo actúe dentro de la aplicación. Por ello, también se requieren defensas contra XSS, una política CSP apropiada y una correcta codificación de la salida.

### Refresh Token

El servidor establecerá una cookie con atributos equivalentes a los siguientes:

```http
Set-Cookie: __Host-gv_refresh=<token_opaco>;
  Path=/;
  HttpOnly;
  Secure;
  SameSite=Strict;
  Max-Age=<segundos_restantes_de_sesion>
```

La cabecera se muestra dividida en líneas únicamente para facilitar la lectura; en una respuesta HTTP real debe emitirse como una sola cabecera `Set-Cookie`.

Reglas:

- `HttpOnly` impide que JavaScript lea el valor de la cookie.
- `Secure` exige que se transmita por HTTPS.
- `SameSite=Strict` limita su envío en contextos de navegación entre sitios.
- El prefijo `__Host-` requiere HTTPS, `Path=/` y ausencia de `Domain`.
- La duración de la cookie no debe superar el tiempo restante permitido para la sesión.
- No se debe confiar en la cookie como único control de autorización. El backend también consulta el estado del token y de la sesión.

Aunque `SameSite=Strict` añade protección frente a solicitudes entre sitios, los endpoints que reciben cookies de autenticación deben validar el origen esperado y aplicar controles adicionales contra CSRF. La configuración de CORS debe autorizar únicamente los orígenes legítimos de GlucoVida.

## 9. Diagrama general de la arquitectura

```text
                         ┌───────────────────┐
                         │ Navegador GlucoVida│
                         └─────────┬─────────┘
                                   │
                   ┌───────────────┴───────────────┐
                   │                               │
            Access Token                    Refresh Token
            en memoria                      cookie protegida
                   │                               │
                   v                               v
        ┌────────────────────┐          ┌────────────────────┐
        │ API protegida       │          │ Servicio de       │
        │ JWT + estado sesión │          │ renovación        │
        └──────────┬─────────┘          └──────────┬─────────┘
                   │                               │
                   └───────────────┬───────────────┘
                                   v
                      ┌────────────────────────┐
                      │ Base de datos          │
                      │ users                  │
                      │ auth_sessions          │
                      │ auth_refresh_tokens    │
                      │ eventos de seguridad   │
                      └────────────────────────┘
```

La API protegida y el servicio de renovación deben consultar el estado vigente en el servidor. La cookie o la firma de un JWT, por sí solas, no sustituyen esa validación.

## 10. Reglas de seguridad que deben considerarse obligatorias

**ARQ-AUTH-01.** Toda solicitud protegida debe comprobar el JWT y el estado de su sesión.

**ARQ-AUTH-02.** Revocar una sesión debe impedir que sus tokens autoricen nuevas solicitudes después de confirmar la revocación.

**ARQ-AUTH-03.** Cambiar o recuperar la contraseña debe invalidar todas las sesiones activas del usuario.

**ARQ-AUTH-04.** La renovación debe rotar el Refresh Token y rechazar los tokens consumidos, revocados o expirados.

**ARQ-AUTH-05.** Los valores originales de los Refresh Tokens no se almacenarán en la base de datos ni en los registros de auditoría.

**ARQ-AUTH-06.** La validación de autorización debe fallar de forma cerrada cuando no sea posible confirmar el estado de la sesión.

**ARQ-AUTH-07.** El servidor aplicará los límites de inactividad y de duración absoluta, independientemente del comportamiento del navegador.

**ARQ-AUTH-08.** Las operaciones de revocación deberán persistirse de forma consistente antes de confirmarse al cliente.

## 11. Límites y consideraciones de implementación

La revocación inmediata se refiere a **las nuevas solicitudes que el backend recibe después de confirmar el cambio de estado**. No es posible retirar retroactivamente una respuesta ya enviada ni cancelar automáticamente una operación que se encontraba ejecutándose antes de la revocación. Las operaciones sensibles deben comprobar de nuevo las condiciones de autorización cuando su naturaleza lo requiera.

Esta arquitectura requiere acceso al estado de sesión en el servidor para cada solicitud protegida. Es una decisión deliberada para el MVP, porque prioriza la revocación confiable frente a una validación completamente sin estado. El rendimiento deberá medirse y optimizarse sin debilitar la garantía de revocación.

También debe respetarse la política de sesiones previamente aprobada en CU02: 30 minutos de inactividad y un máximo de 24 horas de duración absoluta. Un Refresh Token no debe permitir sobrepasar esos límites. Los tiempos definitivos de cada token y de su cookie se establecerán en el componente 2, sin cambiar silenciosamente los requisitos funcionales cerrados.

## 12. Resultado esperado

Al implementar este componente, GlucoVida tendrá una base de autenticación que permite diferenciar tres situaciones:

- **Token válido y sesión activa:** la solicitud puede continuar si también cumple las reglas de autorización.
- **Token todavía vigente, pero sesión revocada:** la solicitud se rechaza.
- **Cambio o recuperación de contraseña completados:** todas las sesiones anteriores quedan invalidadas y el usuario debe autenticarse nuevamente.

**Criterio de cierre del componente:** la arquitectura se considerará definida cuando el modelo de sesiones, el mecanismo de invalidación global, la rotación de Refresh Tokens y la comprobación del estado de sesión estén documentados y aprobados para su implementación.

### Referencias técnicas

- OWASP Foundation. *Session Management Cheat Sheet*. https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- Lodderstedt, T., Bradley, J., Labunets, A., & Fett, D. (2025). *RFC 9700: Best Current Practice for OAuth 2.0 Security*. RFC Editor. https://www.rfc-editor.org/rfc/rfc9700.html
