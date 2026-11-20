# CU02. Iniciar sesión

## 1. Identificación

| Campo | Descripción |
|---|---|
| **ID** | CU02 |
| **Nombre** | Iniciar sesión |
| **Actor principal** | Usuario registrado |
| **Actores secundarios** | Sistema de GlucoVida, servicio de autenticación |
| **Objetivo** | Permitir que un usuario con una cuenta activa acceda de forma segura a las funcionalidades privadas de GlucoVida. |
| **Prioridad** | Alta |
| **Tipo** | Caso de uso principal |

## 2. Descripción

El usuario ingresa su correo electrónico y contraseña en el formulario de inicio de sesión. El sistema valida las credenciales, verifica el estado de la cuenta y, si la autenticación es exitosa, genera una sesión autenticada mediante un token JWT almacenado en una cookie segura.

La sesión tendrá una duración máxima de 24 horas y expirará automáticamente después de 30 minutos sin interacción.

## 3. Precondiciones

- El usuario debe tener una cuenta registrada.
- El correo electrónico debe haber sido verificado.
- La cuenta debe encontrarse en estado **Activa**.
- El sistema debe encontrarse disponible.

## 4. Disparador

El usuario selecciona la opción **«Iniciar sesión»** desde la página principal o desde el formulario de acceso.

## 5. Flujo principal

| Paso | Actor | Acción |
|---|---|---|
| 1 | Usuario | Selecciona la opción «Iniciar sesión». |
| 2 | Sistema | Muestra el formulario de acceso. |
| 3 | Usuario | Ingresa su correo electrónico y contraseña. |
| 4 | Usuario | Envía el formulario. |
| 5 | Sistema | Verifica que los campos obligatorios estén completos y tengan un formato válido. |
| 6 | Sistema | Busca la cuenta asociada al correo electrónico ingresado. |
| 7 | Sistema | Verifica la contraseña utilizando el hash almacenado mediante `bcrypt`. |
| 8 | Sistema | Comprueba que la cuenta esté activa y que el correo electrónico haya sido verificado. |
| 9 | Sistema | Genera un token JWT de autenticación. |
| 10 | Sistema | Almacena el JWT en una cookie con las propiedades de seguridad definidas. |
| 11 | Sistema | Inicia el control de tiempo de sesión e inactividad. |
| 12 | Sistema | Redirige al usuario al panel principal de GlucoVida. |

## 6. Parámetros técnicos definidos

| Parámetro | Valor |
|---|---|
| **Tiempo máximo de inactividad** | 30 minutos sin interacción |
| **Duración máxima de sesión activa** | 24 horas |
| **Límite de intentos fallidos** | 5 intentos consecutivos |
| **Duración del bloqueo temporal** | 15 minutos |
| **Estrategia de autenticación** | JWT almacenado en cookie segura |
| **Cookie** | `HttpOnly`, `Secure` y `SameSite` |
| **Hash de contraseña** | `bcrypt` |
| **Factor de trabajo bcrypt** | 12 |
| **Almacenamiento del JWT** | Cookie, no `localStorage` |
| **Expiración** | Por inactividad o al alcanzar las 24 horas de sesión |

### Política de expiración

La sesión finalizará cuando ocurra **cualquiera** de estas condiciones:

1. El usuario permanezca 30 minutos sin interacción.
2. Se cumplan 24 horas desde el inicio de la sesión.
3. El usuario seleccione «Cerrar sesión».
4. El sistema invalide la sesión por una medida de seguridad o administración.

El límite de 24 horas representa la duración máxima absoluta de la sesión. La actividad del usuario no debe extenderla indefinidamente.

## 7. Flujos alternativos

### FA01. Correo electrónico o contraseña incorrectos

- En el paso 7, el sistema determina que las credenciales no son válidas.
- El sistema muestra un mensaje general indicando que el correo o la contraseña son incorrectos.
- El intento fallido queda registrado para el control de seguridad.
- El usuario puede volver a ingresar sus credenciales.
- El flujo continúa desde el paso 3.

El sistema no debe indicar si el correo existe o no en la base de datos.

### FA02. Cuenta pendiente de verificación

- En el paso 8, el sistema identifica que el correo todavía no ha sido verificado.
- El sistema informa que es necesario verificar el correo electrónico.
- El sistema ofrece la opción de reenviar el mensaje de verificación.
- No se crea una sesión.
- El usuario debe completar la verificación antes de volver a intentar iniciar sesión.

### FA03. Cuenta bloqueada

- En el paso 8, el sistema identifica que la cuenta se encuentra bloqueada.
- El sistema informa que el acceso está temporalmente restringido.
- No se crea una sesión.
- El usuario deberá esperar hasta que finalice el periodo de bloqueo o seguir el proceso correspondiente.

### FA04. Campos incompletos o formato inválido

- En el paso 5, el sistema identifica información faltante o incorrecta.
- El sistema señala los campos que deben corregirse.
- El usuario modifica la información.
- El flujo continúa desde el paso 3.

### FA05. Recuperación de contraseña

- El usuario selecciona «¿Olvidaste tu contraseña?».
- El sistema dirige al usuario al caso de uso correspondiente a recuperación de contraseña.
- No se crea una sesión durante este proceso.

### FA06. Sesión ya existente

- El sistema detecta una sesión válida asociada al usuario.
- No genera innecesariamente una nueva sesión.
- El usuario es dirigido al panel principal.

## 8. Flujos de excepción

### FE01. Servicio de autenticación no disponible

- El sistema no puede completar la validación de las credenciales.
- El sistema informa que el inicio de sesión no está disponible temporalmente.
- No se crea una sesión.
- El usuario puede intentarlo nuevamente.

### FE02. Error al crear la sesión

- Las credenciales son válidas, pero ocurre un error al generar o establecer la sesión.
- El sistema no concede acceso.
- No se almacena un JWT incompleto o inválido.
- El usuario recibe un mensaje indicando que no fue posible completar el inicio de sesión.

### FE03. Quinto intento fallido

- El sistema registra el quinto intento consecutivo fallido.
- El sistema aplica un bloqueo temporal de **15 minutos**.
- Durante ese periodo no permite nuevos intentos de autenticación.
- El sistema informa al usuario que el acceso ha sido restringido temporalmente.

### FE04. Sesión expirada por inactividad

- El usuario intenta utilizar GlucoVida después de superar los **30 minutos sin interacción**.
- El sistema determina que la sesión expiró.
- El sistema elimina o invalida la cookie correspondiente.
- El usuario es redirigido al inicio de sesión.

### FE05. Sesión expirada por duración máxima

- El usuario intenta utilizar GlucoVida después de alcanzar las **24 horas** desde el inicio de sesión.
- El sistema invalida la sesión.
- El usuario debe autenticarse nuevamente.

## 9. Postcondiciones

### Si el inicio de sesión es exitoso:

- El usuario queda autenticado.
- Se genera un JWT válido.
- El JWT se almacena en una cookie protegida.
- El usuario puede acceder a las funcionalidades autorizadas para su rol.
- Comienza el control de duración e inactividad de la sesión.

### Si el inicio de sesión falla:

- No se crea una sesión válida.
- No se concede acceso a funcionalidades privadas.
- El intento puede quedar registrado como evento de seguridad.
- Si se alcanzan cinco intentos consecutivos fallidos, se aplica el bloqueo temporal.

## 10. Reglas de negocio relacionadas

| Código | Regla |
|---|---|
| **RN08** | Solo las cuentas en estado Activa pueden iniciar sesión. |
| **RN09** | La verificación del correo electrónico es obligatoria para habilitar el acceso. |
| **RN10** | El usuario debe autenticarse mediante correo electrónico y contraseña. |
| **RN11** | Los mensajes de autenticación fallida no deben revelar si un correo está registrado. |
| **RN12** | Las contraseñas deben verificarse utilizando `bcrypt` y nunca almacenarse en texto plano. |
| **RN13** | Después de cinco intentos consecutivos de autenticación fallidos se aplica un bloqueo temporal de 15 minutos. |
| **RN14** | La sesión expira después de 30 minutos sin interacción. |
| **RN15** | La duración máxima absoluta de una sesión es de 24 horas. |
| **RN16** | El JWT de autenticación debe almacenarse mediante una cookie con las propiedades `HttpOnly`, `Secure` y `SameSite`. |
| **RN17** | El usuario solo puede acceder a las funcionalidades autorizadas para su rol y estado de cuenta. |

## 11. Requisitos funcionales relacionados

- **RF06:** El sistema debe permitir iniciar sesión mediante correo electrónico y contraseña.
- **RF07:** El sistema debe validar las credenciales antes de conceder acceso.
- **RF08:** El sistema debe impedir el acceso a cuentas cuyo correo electrónico no haya sido verificado.
- **RF09:** El sistema debe impedir el acceso a cuentas bloqueadas o inactivas.
- **RF10:** El sistema debe generar y administrar sesiones autenticadas mediante JWT.
- **RF11:** El sistema debe almacenar el token de autenticación mediante una cookie segura.
- **RF12:** El sistema debe finalizar la sesión después de 30 minutos sin interacción.
- **RF13:** El sistema debe finalizar la sesión al alcanzar 24 horas desde su creación.
- **RF14:** El sistema debe aplicar un bloqueo temporal después de cinco intentos consecutivos fallidos.
- **RF15:** El sistema debe permitir al usuario acceder al proceso de recuperación de contraseña.

## 12. Consideraciones de seguridad

- El sistema debe utilizar HTTPS para proteger las comunicaciones.
- El JWT no debe almacenarse en `localStorage` ni `sessionStorage`.
- La cookie debe utilizar `HttpOnly` para impedir su lectura mediante JavaScript.
- La cookie debe utilizar `Secure` para permitir su transmisión únicamente mediante HTTPS.
- La propiedad `SameSite` debe configurarse de acuerdo con la arquitectura de GlucoVida para reducir el riesgo de CSRF.
- Las contraseñas deben almacenarse mediante `bcrypt` con factor de trabajo 12.
- El sistema no debe almacenar contraseñas en texto plano.
- Los intentos de autenticación deben controlarse para reducir ataques de fuerza bruta.
- Los mensajes de error no deben revelar información que facilite la enumeración de usuarios.
- Al cerrar sesión, la cookie de autenticación debe invalidarse o eliminarse.