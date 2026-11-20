# GlucoVida | Políticas de expiración y Rate Limiting

**Documento técnico 2 de 4**

**Componente:** Políticas de expiración de tokens y limitación de solicitudes.  
**Versión:** 1.0  
**Estado:** Propuesta técnica definida para implementación del backend.  
**Dependencia:** Componente 1. Arquitectura de tokens y revocación.  
**Alcance:** Autenticación, renovación de sesión, cambio de contraseña y recuperación de contraseña.

## 1. Objetivo

Establecer valores exactos para la duración de los tokens, la expiración de las sesiones y la limitación de solicitudes a los servicios de autenticación de GlucoVida.

Las políticas deben cumplir tres objetivos:

1. Reducir el tiempo durante el cual un token robado puede utilizarse.
2. Evitar que un Refresh Token prolongue una sesión más allá de los límites funcionales aprobados.
3. Dificultar ataques de fuerza bruta, intentos automatizados y abuso de los servicios de autenticación.

Estas políticas complementan los requisitos funcionales existentes. No modifican los tiempos de sesión ni las reglas de recuperación de contraseña que ya fueron aprobados.

# 2. Políticas de expiración de tokens

## 2.1. Access Token

**Valor establecido: 15 minutos (900 segundos).**

El Access Token tendrá una duración máxima de 15 minutos contados desde su emisión.

Configuración:

| Parámetro | Valor |
|---|---|
| Tipo | JWT |
| Duración | 15 minutos |
| Valor en segundos | 900 |
| Almacenamiento del cliente | Memoria de la aplicación |
| Envío | Cabecera Authorization: Bearer |
| Renovación | Mediante Refresh Token |
| Revocación anticipada | Mediante validación del estado de sesión en el servidor |

Ejemplo:

```json
{
  "sub": "uuid-del-usuario",
  "sid": "uuid-de-la-sesion",
  "jti": "identificador-unico",
  "av": 4,
  "iat": 1793200000,
  "exp": 1793200900
}
```

El valor de `exp` representa el momento exacto en que deja de aceptarse el token.

**Regla de validación:**

```text
Si hora_actual >= exp:
    Rechazar token
    Responder 401 Unauthorized
Si hora_actual < exp:
    Continuar con validación de sesión
```

La firma JWT válida no es suficiente para autorizar una operación. Se debe verificar también el estado vigente de la sesión y la versión de autenticación del usuario, según el componente 1.

No se concederá un periodo adicional de aceptación después de `exp`. Los servidores deberán mantener sus relojes sincronizados mediante un servicio de tiempo confiable.

## 2.2. Refresh Token

**Valor establecido: máximo 24 horas desde la creación de la sesión.**

El Refresh Token permitirá obtener nuevos Access Tokens sin solicitar nuevamente las credenciales, siempre que la sesión siga activa.

| Parámetro | Valor |
|---|---|
| Tipo | Token opaco aleatorio |
| Duración absoluta máxima | 24 horas |
| Rotación | Cada renovación exitosa |
| Almacenamiento | Cookie HttpOnly, Secure y SameSite=Strict |
| Persistencia del hash | Base de datos |
| Expiración anticipada | Por inactividad, revocación o cierre de sesión |

**Decisión de arquitectura:** no se utilizará una duración de siete días para el Refresh Token. Ese periodo sería incompatible con la duración absoluta máxima de 24 horas aprobada para las sesiones de GlucoVida.

Cada renovación debe emitir un Refresh Token nuevo, pero no podrá extender la fecha límite absoluta de la sesión.

Ejemplo:

```text
Inicio de sesión:
04/11/2026 - 08:00

Expiración absoluta de sesión:
05/11/2026 - 08:00

Renovación del token:
04/11/2026 - 14:00

Nueva expiración absoluta:
05/11/2026 - 08:00
```

La renovación cambia el token, pero no modifica la fecha límite de la sesión.

## 2.3. Expiración por inactividad

**Valor establecido: 30 minutos.**

La sesión se invalidará cuando transcurran 30 minutos sin actividad autenticada válida.

La validación se realizará en el backend mediante `last_activity_at`.

```text
idle_expiration = last_activity_at + 30 minutos

Si hora_actual >= idle_expiration:
    Marcar sesión como expirada
    Revocar sus Refresh Tokens
    Rechazar nuevas solicitudes
    Exigir autenticación nuevamente
```

Para evitar que una renovación automática mantenga una sesión indefinidamente abierta, las llamadas a `/refresh` no deben actualizar por sí solas `last_activity_at`.

Se considerarán actividad válida las solicitudes autenticadas correspondientes a operaciones reales de la aplicación. Las llamadas automáticas de renovación, comprobaciones de salud y consultas periódicas de fondo que no representen interacción del usuario no reiniciarán el contador.

La hora se registrará y calculará en el servidor. No se aceptarán marcas de tiempo enviadas por el navegador como prueba de actividad.

## 2.4. Expiración absoluta de sesión

**Valor establecido: 24 horas.**

Independientemente de la actividad del usuario, una sesión no podrá permanecer activa por más de 24 horas desde su creación.

```text
absolute_expiration = session.created_at + 24 horas

Si hora_actual >= absolute_expiration:
    Invalidar sesión
    Revocar Refresh Token
    Rechazar Access Tokens asociados
    Exigir nuevo inicio de sesión
```

La fecha absoluta nunca se reinicia al renovar los tokens.

## 2.5. Relación entre los tiempos de expiración

Las reglas se aplican simultáneamente. La sesión terminará al cumplirse la primera condición de expiración o revocación.

| Elemento | Límite | ¿Puede extenderse? |
|---|---:|---|
| Access Token | 15 minutos | Se emite uno nuevo mediante renovación válida. |
| Refresh Token | Hasta 24 horas desde la creación de sesión | No puede superar la fecha absoluta. |
| Inactividad | 30 minutos | Se reinicia únicamente por actividad autenticada válida. |
| Sesión absoluta | 24 horas | No se extiende. |
| Enlace de recuperación de contraseña | 30 minutos | No se extiende; es de un solo uso. |

**Regla general:**

```text
La sesión permanece autorizada únicamente cuando:

Access Token no expirado
Y Refresh Token vigente cuando se utilice
Y sesión no revocada
Y tiempo de inactividad < 30 minutos
Y tiempo absoluto de sesión < 24 horas
Y versión de autenticación vigente
```

El Refresh Token se almacenará con `expires_at` igual a la fecha de expiración absoluta de la sesión. La expiración por inactividad se verificará adicionalmente mediante el registro de sesión.

## 2.6. Expiración de la cookie

La cookie del Refresh Token tendrá una fecha de expiración igual al tiempo restante de la sesión, nunca una duración independiente de 24 horas que se reinicie después de cada renovación.

Ejemplo:

```http
Set-Cookie: __Host-gv_refresh=<token>;
Path=/;
HttpOnly;
Secure;
SameSite=Strict;
Max-Age=18000
```

En el ejemplo quedan cinco horas para alcanzar el límite absoluto de la sesión.

En cada rotación se calculará nuevamente el tiempo restante. La cookie no podrá sobrevivir a la sesión en el servidor.

## 2.7. Expiración del enlace de recuperación

Se conserva la decisión funcional de CU18:

- Vigencia del enlace: 30 minutos.
- Uso único.
- Máximo de tres solicitudes de recuperación por hora y por cuenta.
- Al completar la recuperación, invalidación de todas las sesiones activas.
- Los límites adicionales por IP se especifican en la sección de Rate Limiting.

Esta política no modifica el CU18 previamente cerrado.

# 3. Arquitectura de Rate Limiting

## 3.1. Objetivo

Rate Limiting es el mecanismo que limita la cantidad de solicitudes que una cuenta, sesión o dirección IP puede realizar durante un periodo determinado.

Su implementación debe dificultar:

- Ataques de fuerza bruta contra contraseñas.
- Intentos automatizados de acceso a múltiples cuentas.
- Abuso del envío de enlaces de recuperación.
- Intentos excesivos de cambio de contraseña.
- Solicitudes repetidas para renovar tokens.
- Ataques que buscan agotar los recursos del servidor.

GlucoVida utilizará límites independientes por cuenta, dirección IP y sesión, de acuerdo con el endpoint.

## 3.2. Tecnología y estrategia de implementación

Para la implementación se recomienda utilizar Redis como almacenamiento compartido de contadores temporales.

Los contadores deberán ser atómicos y compartidos entre todas las instancias del backend. No se deben guardar únicamente en memoria local de cada servidor, porque un atacante podría distribuir sus solicitudes entre diferentes instancias y evadir los límites.

Se recomienda un algoritmo de ventana deslizante (*Sliding Window*), que calcula las solicitudes realizadas dentro del periodo configurado y evita los picos artificiales que pueden presentarse en los extremos de una ventana fija.

Ejemplo conceptual:

```text
Solicitud entrante
       |
       v
Identificar endpoint
       |
       v
Identificar cuenta, IP y/o sesión
       |
       v
Consultar contadores compartidos
       |
       v
¿Superó algún límite?
       |
  +----+----+
  |         |
 Sí         No
  |         |
  v         v
429       Procesar
Retry-After solicitud
```

En las claves de límite asociadas al correo electrónico se utilizará un HMAC del identificador normalizado, en lugar de almacenar el correo directamente en Redis.

Ejemplos conceptuales de claves:

```text
rl:login:account:<hmac_email>
rl:login:ip:<client_ip>
rl:change-password:user:<user_id>
rl:change-password:session:<session_id>
rl:recovery:account:<hmac_email>
rl:recovery:ip:<client_ip>
rl:refresh:session:<session_id>
```

La IP de origen deberá obtenerse de forma segura. El backend solamente confiará en cabeceras de proxy como `X-Forwarded-For` cuando la solicitud provenga de un proxy inverso expresamente autorizado.

Si el servicio de contadores no está disponible y no existe un mecanismo alternativo confiable, los endpoints críticos de autenticación no deberán omitir silenciosamente la protección. Se devolverá un error temporal de servicio y se registrará el evento.

# 4. Límites específicos por endpoint

## 4.1. Inicio de sesión

**Endpoint funcional:** inicio de sesión.

Se conservará el límite aprobado en CU02.

| Control | Límite | Acción |
|---|---|---|
| Intentos fallidos consecutivos por cuenta | 5 | Activar bloqueo temporal. |
| Duración del bloqueo por cuenta | 15 minutos | Impedir nuevos intentos de autenticación durante el bloqueo. |
| Solicitudes desde una IP | 30 en 5 minutos | Aplicar limitación por IP durante 5 minutos. |

### Comportamiento

1. El backend recibe las credenciales.
2. Normaliza el identificador de cuenta.
3. Consulta el contador de intentos fallidos.
4. Verifica si la cuenta está temporalmente bloqueada.
5. Realiza la verificación segura de la contraseña.
6. Si la contraseña es incorrecta, incrementa el contador.
7. Al quinto fallo consecutivo, bloquea temporalmente la autenticación durante 15 minutos.
8. Si se supera el límite de solicitudes por IP, responde con `429 Too Many Requests`.

El contador de intentos fallidos se asocia a la cuenta y no solamente a la IP. Esto evita que un atacante eluda el bloqueo cambiando de dirección IP.

El contador se reinicia después de una autenticación exitosa o cuando termina el periodo de bloqueo de 15 minutos.

La protección por IP funciona de manera independiente. No debe utilizarse para bloquear permanentemente una cuenta.

También se aplicará un comportamiento equivalente para identificadores que no correspondan a cuentas registradas, mediante contadores temporales, con el propósito de evitar que las diferencias de respuesta revelen qué correos están registrados.

## 4.2. Cambio de contraseña

El cambio de contraseña requiere una sesión autenticada y la verificación de la contraseña actual, conforme al requisito ya definido en CU03.

Se establecen los siguientes límites técnicos:

| Control | Límite | Acción |
|---|---|---|
| Verificaciones fallidas de contraseña actual por cuenta | 5 en 15 minutos | Bloquear el endpoint durante 15 minutos. |
| Solicitudes al endpoint por sesión | 10 en 5 minutos | Responder 429 durante el tiempo restante de la ventana. |
| Solicitudes al endpoint por IP | 30 en 5 minutos | Aplicar límite temporal por IP durante 5 minutos. |

### Comportamiento

- Una verificación fallida de la contraseña actual incrementará el contador de intentos fallidos.
- Al quinto fallo dentro de 15 minutos, el endpoint de cambio de contraseña quedará temporalmente limitado durante 15 minutos.
- Este bloqueo afectará exclusivamente al endpoint de cambio de contraseña.
- No bloqueará el acceso general a la cuenta ni impedirá iniciar el proceso de recuperación de contraseña.
- El límite general de solicitudes por sesión e IP se aplicará independientemente del resultado de la verificación.
- Cuando el cambio de contraseña se complete correctamente, se ejecutará la invalidación global de sesiones ya definida en el componente 1.

Esta regla es una protección técnica adicional. No cambia la obligación de verificar la contraseña actual ni modifica el flujo funcional de CU03.

## 4.3. Solicitud de recuperación de contraseña

Se conservará el límite funcional de CU18 y se concretará el límite complementario por IP.

| Control | Límite | Acción |
|---|---|---|
| Solicitudes por cuenta | 3 en 60 minutos | No generar nuevos enlaces durante el periodo de limitación. |
| Solicitudes por IP | 20 en 60 minutos | Responder 429 cuando se supere el límite. |
| Solicitudes por IP en ventana corta | 5 en 10 minutos | Aplicar limitación temporal para evitar ráfagas. |
| Vigencia del enlace | 30 minutos | Rechazar el enlace después de su expiración. |

### Comportamiento

- La cuenta no podrá generar más de tres solicitudes de recuperación dentro de una ventana móvil de 60 minutos.
- La dirección IP no podrá realizar más de 20 solicitudes en una ventana móvil de 60 minutos.
- También se limitarán las ráfagas a cinco solicitudes por cada ventana móvil de 10 minutos.
- Los límites por cuenta se aplicarán tanto a cuentas existentes como a identificadores no registrados.
- Cuando se alcance el límite por cuenta, se conservará una respuesta genérica para no revelar la existencia de la cuenta.
- El límite por IP podrá devolver `429 Too Many Requests` sin indicar si el correo está registrado.
- El enlace válido seguirá siendo de un solo uso y tendrá una vigencia máxima de 30 minutos.

La protección debe evitar que un atacante genere cantidades excesivas de correos y afecte la disponibilidad del servicio de recuperación.

## 4.4. Envío de nueva contraseña con enlace de recuperación

La recepción y validación del enlace también debe protegerse frente a intentos automatizados.

| Control | Límite | Acción |
|---|---|---|
| Envíos de formularios de recuperación por IP | 10 en 15 minutos | Responder 429 durante el tiempo restante de la ventana. |
| Vigencia del token | 30 minutos | Rechazar si está expirado. |
| Reutilización del token | No permitida | Rechazar token ya consumido. |

La contraseña solamente se actualizará cuando el token sea válido, no esté expirado y no haya sido utilizado previamente.

La actualización de contraseña y la invalidación global de sesiones se realizarán con las reglas ya establecidas en CU18 y en el componente 1.

## 4.5. Renovación del Access Token

El endpoint de renovación también debe tener protección contra solicitudes automatizadas.

| Control | Límite | Acción |
|---|---|---|
| Solicitudes por sesión | 5 por minuto | Responder 429 cuando se supere el límite. |
| Solicitudes por IP | 30 por minuto | Aplicar límite temporal por IP. |

La renovación legítima no debería alcanzar estos valores en condiciones normales, porque el Access Token tiene una duración de 15 minutos.

Además:

- Cada renovación debe validar el Refresh Token y el estado de la sesión.
- La rotación será atómica.
- Un token consumido o revocado no podrá reutilizarse.
- La detección de reutilización debe activar la revocación de la familia de tokens según el componente 1.
- El Rate Limiting no reemplaza la detección de reutilización.

# 5. Respuestas cuando se supera un límite

Cuando una solicitud exceda un límite de Rate Limiting, el backend devolverá:

**Código HTTP:** `429 Too Many Requests`.

Ejemplo:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 300
Cache-Control: no-store
Content-Type: application/json
```

Cuerpo ilustrativo:

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Se ha superado el límite de solicitudes. Inténtalo nuevamente más tarde."
  }
}
```

El encabezado `Retry-After` indicará los segundos restantes antes de que se permita intentar nuevamente.

Ejemplos:

| Situación | Retry-After |
|---|---:|
| Bloqueo temporal de inicio de sesión | 900 segundos |
| Límite de IP de inicio de sesión | 300 segundos |
| Bloqueo de cambio de contraseña | 900 segundos |
| Límite por IP de recuperación | Tiempo restante de la ventana o bloqueo |

Las respuestas no deben entregar detalles que faciliten la enumeración de cuentas, la identificación de usuarios registrados o la deducción de sus estados internos.

# 6. Reglas técnicas obligatorias

**RL-AUTH-01.** El Access Token tendrá una duración máxima de 15 minutos.

**RL-AUTH-02.** El Refresh Token no podrá superar la fecha de expiración absoluta de 24 horas de la sesión.

**RL-AUTH-03.** Una sesión finalizará después de 30 minutos de inactividad autenticada válida.

**RL-AUTH-04.** Una sesión finalizará al cumplir 24 horas desde su creación, independientemente de su actividad.

**RL-AUTH-05.** La renovación de tokens no reiniciará la duración absoluta de la sesión.

**RL-AUTH-06.** La renovación automática no actualizará por sí sola el contador de inactividad.

**RL-AUTH-07.** Se conservará el límite de cinco intentos fallidos y bloqueo de 15 minutos en el inicio de sesión.

**RL-AUTH-08.** El cambio de contraseña tendrá una limitación adicional de cinco verificaciones fallidas de la contraseña actual en 15 minutos, con bloqueo de 15 minutos del endpoint correspondiente.

**RL-AUTH-09.** Se conservará el máximo de tres solicitudes de recuperación por hora y por cuenta.

**RL-AUTH-10.** Los límites por IP se aplicarán de forma independiente y no sustituirán el control por cuenta.

**RL-AUTH-11.** Los contadores deberán ser compartidos entre las instancias del backend y actualizarse de forma atómica.

**RL-AUTH-12.** El servidor será la autoridad para determinar la expiración de tokens y sesiones.

**RL-AUTH-13.** No se permitirá renovar una sesión revocada, inactiva o que haya alcanzado su fecha de expiración absoluta.

**RL-AUTH-14.** Los contadores de seguridad no almacenarán contraseñas, tokens completos ni secretos de autenticación.

# 7. Criterios de aceptación técnica

El componente se considerará correctamente implementado cuando se compruebe lo siguiente:

1. Un Access Token deja de ser aceptado al alcanzar los 15 minutos de vigencia.
2. Un Refresh Token no puede extender una sesión más allá de las 24 horas desde su creación.
3. Una sesión se invalida cuando supera los 30 minutos de inactividad.
4. Una sesión se invalida al cumplir 24 horas aunque el usuario haya permanecido activo.
5. El quinto intento fallido de inicio de sesión activa el bloqueo de 15 minutos establecido en CU02.
6. Los límites por IP se aplican de forma compartida y no dependen de una única instancia del backend.
7. El endpoint de cambio de contraseña limita los intentos fallidos de verificación de la contraseña actual.
8. La recuperación de contraseña conserva el máximo de tres solicitudes por cuenta en una hora.
9. Un Refresh Token consumido, revocado o expirado no puede reutilizarse.
10. Los límites superados generan respuestas controladas, sin exposición innecesaria de información de las cuentas.

# 8. Resultado esperado

GlucoVida tendrá políticas exactas y coherentes para controlar la vida útil de sus credenciales y limitar los intentos automatizados contra los servicios críticos.

La política mantiene intactos los límites funcionales previamente aprobados y define controles técnicos adicionales para proteger los endpoints de autenticación.

## Referencias técnicas

- OWASP Foundation. *Session Management Cheat Sheet*. https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- OWASP Foundation. *Authentication Cheat Sheet*. https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- OWASP Foundation. *Forgot Password Cheat Sheet*. https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html
- National Institute of Standards and Technology (NIST). (2025). *Digital Identity Guidelines: Authentication and Authenticator Management (SP 800-63B-4)*. https://pages.nist.gov/800-63-4/sp800-63b.html
- Lodderstedt, T., Bradley, J., Labunets, A., & Fett, D. (2025). *RFC 9700: Best Current Practice for OAuth 2.0 Security*. https://www.rfc-editor.org/rfc/rfc9700.html